---
name: rtl-opt
description: Critical path patterns with corresponding optimization strategies. Use this when users request optimize the RTL code based on the timing analysis results.
license: Complete terms in LICENSE.txt
---



This file merges and normalizes the uploaded skill libraries into one comprehensive reference. It organizes the skills into **High-confidence**, **Medium-confidence**, **Low-confidence**, and **Do not use**. Each skill is written in the format:

`<pattern, strategy, example>`

For every example, both **before** and **after** Verilog snippets are included.

---

## High-confidence

### 1. `<repeated comparisons / repeated control checks, pre-compute shared condition wires and reuse them, example>`
- **Pattern**: repeated `(state == X)`, `(cmd == Y)`, `(count == Z)` or repeated shared condition fragments across branches.
- **Strategy**: extract named wires once, then reuse them in `always` / `assign` logic. Very safe and consistently effective for FSM decode, counters, and control fanout.
- **Example**:
  ```verilog
  // BEFORE
  always @(*) begin
    if (state == IDLE && cmd == START)
      next_state = START;
    else if (state == IDLE && cmd == STOP)
      next_state = STOP;
    else
      next_state = state;
  end

  // AFTER
  wire state_is_idle = (state == IDLE);
  wire cmd_is_start  = (cmd == START);
  wire cmd_is_stop   = (cmd == STOP);
  wire go_start      = state_is_idle & cmd_is_start;
  wire go_stop       = state_is_idle & cmd_is_stop;

  always @(*) begin
    if (go_start)
      next_state = START;
    else if (go_stop)
      next_state = STOP;
    else
      next_state = state;
  end
  ```

### 2. `<shared sub-conditions reused in multiple branches, build hierarchical shared condition wires before final checks, example>`
- **Pattern**: multiple branches share a common prefix such as `state == DATA && sck == HIGH`.
- **Strategy**: factor the shared prefix into one wire, then attach the remaining branch-local tests.
- **Example**:
  ```verilog
  // BEFORE
  assign fire_done  = (state == DATA) && (sck == HIGH) && (count == MAX);
  assign fire_shift = (state == DATA) && (sck == HIGH) && (count > THRESH);

  // AFTER
  wire state_is_data = (state == DATA);
  wire sck_is_high   = (sck == HIGH);
  wire data_and_sck  = state_is_data & sck_is_high;
  wire count_is_max  = (count == MAX);
  wire count_is_gt   = (count > THRESH);

  assign fire_done  = data_and_sck & count_is_max;
  assign fire_shift = data_and_sck & count_is_gt;
  ```

### 3. `<FSM / opcode / instruction decode used in many places, one-hot pre-decode encoded values before downstream logic, example>`
- **Pattern**: FSM-heavy control, instruction decoders, opcode/state checks fanning out widely.
- **Strategy**: generate one-hot-style boolean decode signals such as `state_is_*` / `op_is_*`, then use them directly.
- **Example**:
  ```verilog
  // BEFORE
  assign do_add = (opcode == 4'b0001) && valid;
  assign do_sub = (opcode == 4'b0010) && valid;
  assign do_and = (opcode == 4'b0011) && valid;

  // AFTER
  wire op_is_add = (opcode == 4'b0001);
  wire op_is_sub = (opcode == 4'b0010);
  wire op_is_and = (opcode == 4'b0011);

  assign do_add = op_is_add & valid;
  assign do_sub = op_is_sub & valid;
  assign do_and = op_is_and & valid;
  ```

### 4. `<one-hot or bit-encoded state with direct bit meaning, replace full equality with direct bit indexing, example>`
- **Pattern**: one-hot state or representation where a specific bit directly denotes the condition.
- **Strategy**: replace a full equality comparator with direct bit access when encoding guarantees equivalence.
- **Example**:
  ```verilog
  // BEFORE
  wire is_state_5 = (State == 6'b100000);

  // AFTER
  wire is_state_5 = State[5];
  ```

### 5. `<repeated arithmetic / repeated partial products / repeated shared expressions, common subexpression elimination to a named wire, example>`
- **Pattern**: same add/mul/compare subtree appears in multiple outputs or branches.
- **Strategy**: compute once and reuse everywhere.
- **Example**:
  ```verilog
  // BEFORE
  assign out_a = (x + y) + z;
  assign out_b = (x + y) + w;

  // AFTER
  wire [W-1:0] xy_sum = x + y;
  assign out_a = xy_sum + z;
  assign out_b = xy_sum + w;
  ```

### 6. `<shared arithmetic across module instances, hoist common subexpression upward and fan out result, example>`
- **Pattern**: identical intermediate arithmetic is recomputed in sibling instances or branches.
- **Strategy**: move the common computation to the parent or earlier stage and distribute the shared result.
- **Example**:
  ```verilog
  // BEFORE
  child0 u0(.prod_in(a * b), .c(c0));
  child1 u1(.prod_in(a * b), .c(c1));

  // AFTER
  wire [W-1:0] shared_mul = a * b;
  child0 u0(.prod_in(shared_mul), .c(c0));
  child1 u1(.prod_in(shared_mul), .c(c1));
  ```

### 7. `<high-fanout control or registered signals, duplicate register/signal copies and split fanout cones, example>`
- **Pattern**: reset/enable/state-derived signals with many loads.
- **Strategy**: create duplicated copies, ideally aligned with consumer cones.
- **Example**:
  ```verilog
  // BEFORE
  reg en;
  always @(posedge clk) en <= en_next;
  // en drives many distant loads

  // AFTER
  reg en_a, en_b;
  always @(posedge clk) begin
    en_a <= en_next;
    en_b <= en_next;
  end
  // split loads between en_a and en_b
  ```

### 8. `<high-fanout combinational condition wire, replicate equivalent local wires for separate consumers, example>`
- **Pattern**: a decoded combinational signal drives many separate cones.
- **Strategy**: replicate equivalent combinational wires so synthesis can localize logic and reduce loading.
- **Example**:
  ```verilog
  // BEFORE
  wire state_is_data = (state == DATA);
  assign cnt_en   = state_is_data & cnt_req;
  assign out_en   = state_is_data & out_req;
  assign flag_set = state_is_data & flag_req;

  // AFTER
  wire state_is_data_cnt  = (state == DATA);
  wire state_is_data_out  = (state == DATA);
  wire state_is_data_flag = (state == DATA);

  assign cnt_en   = state_is_data_cnt  & cnt_req;
  assign out_en   = state_is_data_out  & out_req;
  assign flag_set = state_is_data_flag & flag_req;
  ```

### 9. `<wide adder / deep carry chain, carry-select style split into blocks, example>`
- **Pattern**: ripple-carry dominated arithmetic path, especially wide adders.
- **Strategy**: split into blocks, precompute upper block for carry-in 0/1, then select.
- **Example**:
  ```verilog
  // BEFORE
  wire [31:0] sum = a + b;

  // AFTER
  wire [15:0] sum_lo = a[15:0] + b[15:0];
  wire        carry_lo = ({1'b0, a[15:0]} + {1'b0, b[15:0]})[16];
  wire [15:0] sum_hi_c0 = a[31:16] + b[31:16];
  wire [15:0] sum_hi_c1 = a[31:16] + b[31:16] + 1'b1;
  wire [15:0] sum_hi = carry_lo ? sum_hi_c1 : sum_hi_c0;
  wire [31:0] sum = {sum_hi, sum_lo};
  ```

### 10. `<counter decrement / borrow chain with predictable structure, pre-compute borrow or lookahead-style signals, example>`
- **Pattern**: decrement or borrow propagation dominates delay.
- **Strategy**: use carry-lookahead / borrow-lookahead style restructuring rather than serial borrow propagation.
- **Example**:
  ```verilog
  // BEFORE
  wire [3:0] dec = a - 4'd1;

  // AFTER
  wire b0 = ~a[0];
  wire b1 = b0 & ~a[1];
  wire b2 = b1 & ~a[2];
  wire [3:0] dec;
  assign dec[0] = ~a[0];
  assign dec[1] = a[1] ^ b0;
  assign dec[2] = a[2] ^ b1;
  assign dec[3] = a[3] ^ b2;
  ```

### 11. `<simple compare against power-of-two threshold / one-hot boundary, simplify wide comparison into bit-select or MSB check, example>`
- **Pattern**: checks like `count >= 32`, direct one-hot state recognition, fixed-point truncation by shift.
- **Strategy**: replace full comparator or arithmetic shift with direct bit inspection / slicing when semantics are guaranteed.
- **Example**:
  ```verilog
  // BEFORE
  wire limit_reached = (data_count >= 6'd32);
  wire [15:0] trunc = full_result >>> 8;

  // AFTER
  wire limit_reached = data_count[5];
  wire [15:0] trunc = full_result[23:8];
  ```

### 12. `<FSM outputs driving long downstream logic, register or pipeline the boundary signal when extra latency is architecturally acceptable, example>`
- **Pattern**: state decode or module input launches a long path into datapath/control logic.
- **Strategy**: register the boundary signal to break the path, but only when the extra cycle is explicitly acceptable and validated.
- **Example**:
  ```verilog
  // BEFORE
  wire state_is_data = (next_state == DATA);
  assign data_en = state_is_data & ready;

  // AFTER
  reg state_is_data_r;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      state_is_data_r <= 1'b0;
    else
      state_is_data_r <= (next_state == DATA);
  end
  assign data_en = state_is_data_r & ready;
  ```

---

## Medium-confidence

### 13. `<nested ternary / nested mux / branch-dependent data path, compute candidate branch values in parallel and select late, example>`
- **Pattern**: `sel1 ? (sel2 ? a : b) : (sel2 ? c : d)` and similar nested selection structures.
- **Strategy**: precompute branch values unconditionally, then use one late select.
- **Example**:
  ```verilog
  // BEFORE
  assign out = sel1 ? (sel2 ? a : b) : (sel2 ? c : d);

  // AFTER
  wire [W-1:0] r_a = a;
  wire [W-1:0] r_b = b;
  wire [W-1:0] r_c = c;
  wire [W-1:0] r_d = d;
  assign out = sel1 ? (sel2 ? r_a : r_b) : (sel2 ? r_c : r_d);
  ```

### 14. `<arithmetic gated by control, compute both arithmetic branches and mux result at the end, example>`
- **Pattern**: `full ? ptr : ptr + 1`, `en ? a+b : c+d`, branch-local arithmetic mixed with control.
- **Strategy**: move control after arithmetic so arithmetic can proceed in parallel.
- **Example**:
  ```verilog
  // BEFORE
  assign ptr_n = full ? ptr : (ptr + 1'b1);

  // AFTER
  wire [W-1:0] ptr_hold = ptr;
  wire [W-1:0] ptr_inc  = ptr + 1'b1;
  assign ptr_n = full ? ptr_hold : ptr_inc;
  ```

### 15. `<sel ? (A+B) : (C+D) style arithmetic mux, move muxes before adder when equivalence is clear, example>`
- **Pattern**: a final mux chooses between two arithmetic sums/products that share structure.
- **Strategy**: restructure to `(sel?A:C) + (sel?B:D)` to reduce adder count/depth.
- **Example**:
  ```verilog
  // BEFORE
  assign out = sel ? (A + B) : (C + D);

  // AFTER
  wire [W-1:0] x = sel ? A : C;
  wire [W-1:0] y = sel ? B : D;
  assign out = x + y;
  ```

### 16. `<deep if-else / default-then-override control chain, flatten into explicit parallel conditions with single-level selection, example>`
- **Pattern**: long control ladders where priority is known and preserved explicitly.
- **Strategy**: build mutually exclusive select wires and use a flat selection structure.
- **Example**:
  ```verilog
  // BEFORE
  always @(*) begin
    out = v0;
    if (cond1)
      out = v1;
    else if (cond2)
      out = v2;
    else if (cond3)
      out = v3;
  end

  // AFTER
  wire sel1 = cond1;
  wire sel2 = !cond1 & cond2;
  wire sel3 = !cond1 & !cond2 & cond3;
  assign out = sel1 ? v1 : sel2 ? v2 : sel3 ? v3 : v0;
  ```

### 17. `<large case statement with structured outputs, replace with direct AND-OR equations or flattened decode logic, example>`
- **Pattern**: case branches map encoded states/opcodes to simple output patterns.
- **Strategy**: convert case decode into predecoded booleans feeding direct equations.
- **Example**:
  ```verilog
  // BEFORE
  always @(*) begin
    case (state)
      IDLE:  next = START;
      START: next = DATA;
      DATA:  next = STOP;
      STOP:  next = IDLE;
    endcase
  end

  // AFTER
  wire state_is_idle  = (state == IDLE);
  wire state_is_start = (state == START);
  wire state_is_data  = (state == DATA);
  wire state_is_stop  = (state == STOP);

  assign next[0] = state_is_idle | state_is_data;
  assign next[1] = state_is_start | state_is_data;
  ```

### 18. `<wide OR/AND/XOR reduction, restructure linear logic into balanced tree, example>`
- **Pattern**: long reduction chains or unbalanced boolean logic depth.
- **Strategy**: group terms into a binary or hierarchical tree to reduce depth.
- **Example**:
  ```verilog
  // BEFORE
  wire any_set = a | b | c | d | e | f | g | h;

  // AFTER
  wire or01 = a | b;
  wire or23 = c | d;
  wire or45 = e | f;
  wire or67 = g | h;
  wire or0123 = or01 | or23;
  wire or4567 = or45 | or67;
  wire any_set = or0123 | or4567;
  ```

### 19. `<wide mux tree or wide selection network, rebalance into multi-level 2:1 tree, example>`
- **Pattern**: flat or poorly structured 8:1 / 16:1 mux logic.
- **Strategy**: implement an explicit balanced selection tree.
- **Example**:
  ```verilog
  // BEFORE
  assign out = sel[2] ? (sel[1] ? (sel[0] ? d7 : d6) : (sel[0] ? d5 : d4)) :
                       (sel[1] ? (sel[0] ? d3 : d2) : (sel[0] ? d1 : d0));

  // AFTER
  wire l10 = sel[0] ? d1 : d0;
  wire l11 = sel[0] ? d3 : d2;
  wire l12 = sel[0] ? d5 : d4;
  wire l13 = sel[0] ? d7 : d6;
  wire l20 = sel[1] ? l11 : l10;
  wire l21 = sel[1] ? l13 : l12;
  assign out = sel[2] ? l21 : l20;
  ```

### 20. `<multi-operand addition, rebalance serial add chain into tree, example>`
- **Pattern**: `a+b+c+d` in a long arithmetic chain.
- **Strategy**: split into pairwise adds then final combine.
- **Example**:
  ```verilog
  // BEFORE
  wire [31:0] sum = a + b + c + d;

  // AFTER
  wire [31:0] sum_ab = a + b;
  wire [31:0] sum_cd = c + d;
  wire [31:0] sum = sum_ab + sum_cd;
  ```

### 21. `<large lookup / ROM / decoder, split into hierarchical sub-decoders or subtables, example>`
- **Pattern**: monolithic case or LUT such as 8b/10b encode/decode, instruction decode, large table lookup.
- **Strategy**: factor into structured hierarchy such as major-opcode then sub-decode.
- **Example**:
  ```verilog
  // BEFORE
  assign data_out = lut_256[data_in];

  // AFTER
  wire [3:0] hi = data_in[7:4];
  wire [3:0] lo = data_in[3:0];
  wire [W-1:0] hi_dec = lut_hi[hi];
  wire [W-1:0] lo_dec = lut_lo[lo];
  assign data_out = combine(hi_dec, lo_dec);
  ```

### 22. `<GF / XOR-heavy datapath / crypto logic, rebalance XOR/AND computation into explicit stages, example>`
- **Pattern**: serial XOR chains in AES/GF/error-correction style logic.
- **Strategy**: precompute lower-level XORs in parallel, then combine with a balanced tree.
- **Example**:
  ```verilog
  // BEFORE
  wire y = x0 ^ x1 ^ x2 ^ x3 ^ x4 ^ x5;

  // AFTER
  wire x01 = x0 ^ x1;
  wire x23 = x2 ^ x3;
  wire x45 = x4 ^ x5;
  wire y = (x01 ^ x23) ^ x45;
  ```

### 23. `<fixed constant multiplication, replace multiply with shift-add decomposition, example>`
- **Pattern**: multiply by compile-time constant.
- **Strategy**: rewrite as shifts and adds when it reduces critical depth or resource pressure.
- **Example**:
  ```verilog
  // BEFORE
  wire [W-1:0] prod = x * 9'd257;

  // AFTER
  wire [W-1:0] prod = (x << 8) + x;
  ```

### 24. `<comparison after mux selection, convert mux-then-compare into compare-then-mux, example>`
- **Pattern**: select a source and then compare it to a threshold.
- **Strategy**: do the comparisons in parallel first, then mux the boolean result.
- **Example**:
  ```verilog
  // BEFORE
  wire [W-1:0] selected = sel ? a : b;
  wire result = (selected > threshold);

  // AFTER
  wire a_gt = (a > threshold);
  wire b_gt = (b > threshold);
  wire result = sel ? a_gt : b_gt;
  ```

### 25. `<FSM with multiple related outputs, group states by shared output behavior before final decode, example>`
- **Pattern**: multiple FSM outputs depend on overlapping sets of states.
- **Strategy**: precompute state groups and derive outputs from those groups.
- **Example**:
  ```verilog
  // BEFORE
  assign active = (state == READ) | (state == WRITE) | (state == START);

  // AFTER
  wire state_is_read  = (state == READ);
  wire state_is_write = (state == WRITE);
  wire state_is_start = (state == START);
  wire state_group_rw = state_is_read | state_is_write;
  assign active = state_group_rw | state_is_start;
  ```

### 26. `<CPU / multi-cycle controller with timing-state decode, pre-decode machine-cycle and timing-state bits, example>`
- **Pattern**: CPU-style control with `MCycle`, `TState`, instruction groups, microstate families.
- **Strategy**: add a layer of pre-decoded boolean timing/state signals.
- **Example**:
  ```verilog
  // BEFORE
  assign is_fetch_t2 = (MCycle == 3'd1) && (TState == 3'd2);

  // AFTER
  wire mc_is_1 = (MCycle == 3'd1);
  wire ts_is_2 = (TState == 3'd2);
  wire is_fetch_t2 = mc_is_1 & ts_is_2;
  ```

### 27. `<long combinational expression with unclear synthesis boundary, add explicit intermediate wires to guide mapping, example>`
- **Pattern**: deeply nested expressions or mixed-width arithmetic where structure is hard for the tool to exploit.
- **Strategy**: add named staging wires at logical boundaries.
- **Example**:
  ```verilog
  // BEFORE
  wire [31:0] out = ((a * b) + c) >> sh;

  // AFTER
  wire [31:0] stage1 = a * b;
  wire [31:0] stage2 = stage1 + c;
  wire [31:0] out = stage2 >> sh;
  ```

### 28. `<mixed-width arithmetic or truncation boundaries, make width extension/truncation explicit in named wires, example>`
- **Pattern**: hidden casts, implicit sign extension, mixed-width arithmetic.
- **Strategy**: isolate width conversions explicitly so synthesis has clearer boundaries.
- **Example**:
  ```verilog
  // BEFORE
  wire [15:0] sum_ext = a + b;

  // AFTER
  wire [15:0] a_ext = {8'b0, a[7:0]};
  wire [15:0] b_ext = {8'b0, b[7:0]};
  wire [15:0] sum_ext = a_ext + b_ext;
  ```

---

## Low-confidence

### 29. `<aggressive arithmetic branch parallelization, compute all arithmetic branches and late-select across complex arithmetic, example>`
- **Pattern**: several arithmetic branches with overflow, signedness, or truncation subtleties.
- **Strategy**: compute everything in parallel and mux at the end. SEC failures are common.
- **Example**:
  ```verilog
  // BEFORE
  always @(*) begin
    if (sel)
      out = a + b;
    else
      out = c - d;
  end

  // AFTER
  wire [W-1:0] br0 = a + b;
  wire [W-1:0] br1 = c - d;
  assign out = sel ? br0 : br1;
  ```

### 30. `<control flattening around arithmetic-heavy paths, rewrite state/control logic to expose arithmetic in parallel, example>`
- **Pattern**: arithmetic embedded inside a complex control structure.
- **Strategy**: flatten control and let arithmetic branches surface as parallel computations.
- **Example**:
  ```verilog
  // BEFORE
  always @(*) begin
    case (state)
      S0: out = a + b;
      S1: out = a - b;
      default: out = v0;
    endcase
  end

  // AFTER
  wire [W-1:0] v1 = a + b;
  wire [W-1:0] v2 = a - b;
  assign out = (state == S0) ? v1 :
               (state == S1) ? v2 : v0;
  ```

### 31. `<arithmetic chain tree balancing with carry/overflow sensitivity, rebalance addition/subtraction structure, example>`
- **Pattern**: long arithmetic chain where operator ordering affects carry or signed behavior.
- **Strategy**: rebalance the arithmetic tree only when overflow, carry, saturation, and truncation behavior are proven unchanged.
- **Example**:
  ```verilog
  // BEFORE
  wire [W-1:0] y = ((a + b) + c) + d;

  // AFTER
  wire [W-1:0] t0 = a + b;
  wire [W-1:0] t1 = c + d;
  wire [W-1:0] y = t0 + t1;
  ```

### 32. `<aggressive mux tree restructuring when synthesis already optimizes muxes well, explicitly force custom mux hierarchy, example>`
- **Pattern**: wide mux path without a clearly demonstrated structural issue.
- **Strategy**: manually rewrite the mux network. May help occasionally, but often not worth it.
- **Example**:
  ```verilog
  // BEFORE
  assign y = s1 ? (s0 ? d3 : d2) : (s0 ? d1 : d0);

  // AFTER
  wire m0 = s0 ? d1 : d0;
  wire m1 = s0 ? d3 : d2;
  assign y = s1 ? m1 : m0;
  ```

### 33. `<explicit wire decomposition solely for hoped timing gain, split expression into many named wires without structural change, example>`
- **Pattern**: deep expression where no real algebraic or architectural change is introduced.
- **Strategy**: add intermediate wires just to “help synthesis.” Improvement is often negligible.
- **Example**:
  ```verilog
  // BEFORE
  wire [W-1:0] y = a + b + c + d;

  // AFTER
  wire [W-1:0] t0 = a + b;
  wire [W-1:0] t1 = t0 + c;
  wire [W-1:0] y = t1 + d;
  ```

### 34. `<registering decode/control outputs to break timing when architectural latency is uncertain, insert sequential boundary speculatively, example>`
- **Pattern**: tempting long control path, but no clear proof that an extra cycle is legal.
- **Strategy**: add a register only as a last resort.
- **Example**:
  ```verilog
  // BEFORE
  assign out = sel ? a : b;

  // AFTER
  reg sel_r;
  always @(posedge clk) begin
    sel_r <= sel;
  end
  assign out = sel_r ? a : b;
  ```

---

## Do not use

### 35. `<count-up to count-down rewrite or reverse counter direction, change counter direction to simplify terminal detect, example>`
- **Pattern**: `count == MAX` is on the critical path and zero-detect looks cheaper.
- **Strategy**: do **not** rewrite count-up logic into count-down logic just to get zero-detect.
- **Example**:
  ```verilog
  // BEFORE
  always @(posedge clk) begin
    if (en)
      count <= count + 1'b1;
  end
  wire hit_max = (count == MAX_COUNT);

  // AFTER (DO NOT USE)
  always @(posedge clk) begin
    if (en)
      count <= count - 1'b1;
  end
  wire hit_max = (count == 0);
  ```

### 36. `<priority if-else chain flattened into parallel AND-OR without guaranteed mutual exclusivity, remove priority semantics, example>`
- **Pattern**: if-else or priority case where multiple inputs may be simultaneously true.
- **Strategy**: do **not** flatten into parallel logic unless mutual exclusion is formally guaranteed.
- **Example**:
  ```verilog
  // BEFORE
  always @(*) begin
    if (req0)
      grant = 2'b00;
    else if (req1)
      grant = 2'b01;
    else
      grant = 2'b11;
  end

  // AFTER (DO NOT USE)
  assign grant[0] = req1;
  assign grant[1] = ~req0 & ~req1;
  ```

### 37. `<pre-registering mux selector / control selector on active data path, add register to selector to shorten mux path, example>`
- **Pattern**: selector signal is on the critical path of a mux network.
- **Strategy**: do **not** register the selector unless the design explicitly allows the control to arrive one cycle later.
- **Example**:
  ```verilog
  // BEFORE
  assign out = sel ? a : b;

  // AFTER (DO NOT USE)
  reg sel_r;
  always @(posedge clk) sel_r <= sel;
  assign out = sel_r ? a : b;
  ```

### 38. `<control-signal pre-registration across module boundary for timing only, insert control pipeline stage without protocol redesign, example>`
- **Pattern**: cross-module control signal is long and timing-critical.
- **Strategy**: do **not** add a register stage casually.
- **Example**:
  ```verilog
  // BEFORE
  child u0(.req(req), .ack(ack));

  // AFTER (DO NOT USE)
  reg req_r;
  always @(posedge clk) req_r <= req;
  child u0(.req(req_r), .ack(ack));
  ```

### 39. `<operand width reduction / interface width reduction for speed, narrow datapath or module inputs to reduce logic, example>`
- **Pattern**: a wide module input or intermediate result appears over-provisioned.
- **Strategy**: do **not** shrink widths unless numerical equivalence is proved.
- **Example**:
  ```verilog
  // BEFORE
  module foo(input [2*W-1:0] in_data, output [W-1:0] out_data);

  // AFTER (DO NOT USE)
  module foo(input [W-1:0] in_data, output [W-1:0] out_data);
  ```

### 40. `<algebraic restructuring that changes arithmetic corner behavior, rewrite expression form without proof of overflow/signed equivalence, example>`
- **Pattern**: trying to simplify arithmetic by changing grouping or fused operations.
- **Strategy**: do **not** apply algebraic rewrites casually.
- **Example**:
  ```verilog
  // BEFORE
  assign y = (a - b) + c;

  // AFTER (DO NOT USE)
  assign y = a + (c - b);
  ```

### 41. `<fused subtract-multiply / aggressive arithmetic fusion, collapse arithmetic stages into a new combined structure, example>`
- **Pattern**: subtract/multiply/add chain with timing pressure.
- **Strategy**: do **not** fuse or reorder aggressively unless you have a strong formal proof.
- **Example**:
  ```verilog
  // BEFORE
  wire [W-1:0] t = a - b;
  assign y = t * c;

  // AFTER (DO NOT USE)
  assign y = (a * c) - (b * c);
  ```

### 42. `<changing LFSR feedback or polynomial structure, rewrite feedback network for timing, example>`
- **Pattern**: LFSR or scrambler feedback path is critical.
- **Strategy**: do **not** alter the feedback polynomial/structure.
- **Example**:
  ```verilog
  // BEFORE
  assign feedback = lfsr[7] ^ lfsr[5];

  // AFTER (DO NOT USE)
  assign feedback = lfsr[7] ^ lfsr[6];
  ```

### 43. `<modifying memory array addressing / decode architecture from RTL timing path, rewrite memory indexing or address decode casually, example>`
- **Pattern**: address decode or array access appears on the critical path.
- **Strategy**: do **not** casually rewrite memory addressing.
- **Example**:
  ```verilog
  // BEFORE
  assign rd_data = mem[addr];

  // AFTER (DO NOT USE)
  assign rd_data = (addr_sel ? mem[addr_hi] : mem[addr_lo]);
  ```

### 44. `<optimizing pure register self-loop / constraint-only paths as if they were RTL logic problems, rewrite RTL for clock-to-q/setup-only reports, example>`
- **Pattern**: path is mostly register-to-register constraint behavior rather than meaningful combinational logic.
- **Strategy**: do **not** attack these with RTL rewrites.
- **Example**:
  ```verilog
  // BEFORE
  always @(posedge clk)
    q <= d;

  // AFTER (DO NOT USE)
  // arbitrary RTL restructuring here does not solve a clocking/physical constraint path
  always @(posedge clk)
    q <= d;
  ```

### 45. `<expression simplification that removes helpful intermediate boundaries, inline everything into one direct expression, example>`
- **Pattern**: rewriting to “clean up” code by removing named intermediates.
- **Strategy**: do **not** assume fewer wires means better timing.
- **Example**:
  ```verilog
  // BEFORE
  wire [W-1:0] t0 = a + b;
  wire [W-1:0] y  = t0 + c;

  // AFTER (DO NOT USE)
  wire [W-1:0] y = a + b + c;
  ```

### 46. `<restructured comparison ordering that changes corner-case evaluation semantics, reorder sign/magnitude checks for early exit, example>`
- **Pattern**: comparisons with signed, bounded, or asymmetric behavior.
- **Strategy**: do **not** reorder the logical test sequence unless equivalence is proven for all corners.
- **Example**:
  ```verilog
  // BEFORE
  assign sat = (x > POS_LIM) || (x < NEG_LIM);

  // AFTER (DO NOT USE)
  assign sat = x[W-1] ? (x < NEG_LIM) : (x > POS_LIM);
  ```

### 47. `<aggressive tree balancing on paths labeled combinational_depth without understanding arithmetic semantics, mechanically rebalance everything, example>`
- **Pattern**: timing report says “combinational depth” and the response is blanket tree balancing.
- **Strategy**: do **not** rebalance blindly, especially on arithmetic-heavy logic.
- **Example**:
  ```verilog
  // BEFORE
  wire [W-1:0] y = (((a + b) + c) + d) + e;

  // AFTER (DO NOT USE)
  wire [W-1:0] t0 = a + b;
  wire [W-1:0] t1 = c + d;
  wire [W-1:0] y  = (t0 + t1) + e;
  ```

---

## Practical usage notes

- Start with **High-confidence** skills first, especially: condition pre-computation, one-hot pre-decode, CSE, and fanout reduction by duplication.
- Use **Medium-confidence** skills when the timing root cause is clear and equivalence reasoning is still local.
- Treat **Low-confidence** skills as targeted experiments, one at a time.
- Treat **Do not use** as strong default prohibitions unless you have very strong design-specific proof.
- In general, prefer **pre-computation over restructuring** and **local simplification over architectural rewrites**.
