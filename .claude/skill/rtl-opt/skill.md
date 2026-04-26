---
name: rtl-opt
description: Critical path patterns with corresponding optimization strategies. Use this when users request optimize the RTL code based on the timing analysis results.
license: Complete terms in LICENSE.txt
---


## High-Confidence Strategies (>80% success)

### 1. One-Hot Pre-Decode for Control Signals
- **Applies to**: FSM-heavy designs with opcode/state signals that fan out to multiple comparisons
- **Strategy**: Pre-decode multi-bit control signals into one-hot signals (e.g., `op_is_add`, `op_is_sub`, `state_is_idle`) computed once and reused
- **Expected improvement**: WNS +5-15%, TNS +5-20%
- **Area impact**: Neutral to +3%
- **Risk**: Low
- **Evidence**: cpu_fsm.v0.2 (promoted), SPI.v0.5 (SEC pass), UART.v0.4 (promoted), DSP.v0.4 (SEC pass)
- **Key insight**: Reduces fanout loading and eliminates redundant parallel comparisons. Works especially well when same condition is checked in multiple places.

### 2. Condition Pre-Computation with Wire Extraction
- **Applies to**: Counter logic, FSM-controlled datapath, nested conditionals
- **Strategy**: Extract repeated comparisons to named wires (e.g., `count_is_max`, `state_is_active`), compute once, reuse across always blocks
- **Expected improvement**: WNS +0-10%, TNS +2-15%
- **Area impact**: Neutral to +2%
- **Risk**: Low
- **Evidence**: UART.v0.4 (promoted), SPI.v0.5 (SEC pass, WNS -0.26 to -0.23), cpu_fsm.v0.2 (promoted)
- **Key insight**: Conservative approach with very high SEC pass rate. Synthesis can share comparators. Original control flow preserved exactly.

### 3. Register Duplication for Signal Fanout Reduction
- **Applies to**: Control signals (soft_reset, enable) with high fanout across multiple modules
- **Strategy**: Duplicate high-fanout signals with local registered copies in consuming modules
- **Expected improvement**: WNS +5-10%, TNS +10-15%
- **Area impact**: +2-5%
- **Risk**: Low (adds 1 cycle latency to signal path)
- **Evidence**: router.v0.2 (promoted, WNS -0.52 to -0.47, TNS -290 to -263)
- **Key insight**: Breaks timing paths by adding local registers. Must verify that added latency is acceptable for design behavior.

### 4. FSM Output Registration
- **Applies to**: FSM with multiple output signals driving downstream combinational logic
- **Strategy**: Register FSM output signals to break timing paths from state register to downstream registers
- **Expected improvement**: WNS +5-10%, TNS +10-20%
- **Area impact**: +3-5%
- **Risk**: Low (adds 1 cycle latency)
- **Evidence**: router.v0.2 (promoted), router.v2.7 (promoted, score -0.1291)
- **Key insight**: Standard retiming technique. Effective when FSM outputs fan out to multiple datapath elements.

### 5. Input Signal Registration (Pipelining)
- **Applies to**: Signals crossing module boundaries with long combinational paths
- **Strategy**: Register input signals at module boundary to balance timing
- **Expected improvement**: WNS +5-15%, TNS +10-20%
- **Area impact**: +2-5%
- **Risk**: Low (predictable latency change)
- **Evidence**: router.v0.2 (promoted), router.v2.7 (promoted), SPI.v0.5 (SEC pass)
- **Key insight**: Most effective at module boundaries where control signals enter computation. SEC-safe when applied consistently.

---

## Medium-Confidence Strategies (50-80% success)

### 6. Late Mux-Select with Unconditional Computation
- **Applies to**: Arithmetic paths gated by control signals (e.g., `full`, `enable`)
- **Strategy**: Compute both branches unconditionally (e.g., `ptr+1`, `ptr+2`), then select with late mux
- **Expected improvement**: WNS +5-15%, TNS +10-20%
- **Area impact**: +5-15% (duplicated computation)
- **Risk**: Medium (must verify all paths compute valid results)
- **Evidence**: FIFO.v1.2 (score -0.142), vending_machine.v0.5 (promoted, WNS -0.27 to -0.09)
- **Key insight**: Removes control signal from arithmetic critical path. Control signal now only drives final 2:1 mux.

### 7. Mux-Before-Adder Restructuring
- **Applies to**: Paths with `sel?(A+B):(C+D)` structure
- **Strategy**: Restructure to `(sel?A:C)+(sel?B:D)` - move mux before adder
- **Expected improvement**: WNS +30-60%, TNS +40-50%, Area -20-35%
- **Area impact**: Negative (fewer adders)
- **Risk**: Medium (must verify logical equivalence)
- **Evidence**: vending_machine.v0.2 (33% area reduction), vending_machine.v0.5 (promoted, combined with one-hot FSM)
- **Key insight**: Eliminates one adder from critical path while reducing area. Powerful when both paths require addition.

### 8. Hierarchical Case Decomposition (Lookup Tables)
- **Applies to**: Large case statements (>64 entries), encoder/decoder tables
- **Strategy**: Split monolithic case into smaller hierarchical sub-cases (e.g., 8b/10b: 5b->6b + 3b->4b)
- **Expected improvement**: WNS +30-40%, TNS +20-30%
- **Area impact**: -30-45% (smaller lookup tables)
- **Risk**: Medium (requires careful functional verification)
- **Evidence**: pcie.v0.9 (promoted, WNS -0.79 to -0.48, area -42%)
- **Key insight**: Reduces mux depth from O(log N) to O(log sqrt(N)) by exploiting hierarchical structure. Best for standard encodings.

### 9. Logic Tree Balancing in GF Arithmetic
- **Applies to**: Galois Field operations (AES S-box, error correction)
- **Strategy**: Restructure serial XOR/AND chains into balanced tree structure with explicit depth management
- **Expected improvement**: WNS +5-15%
- **Area impact**: Neutral to +5%
- **Risk**: Medium (complex transformations)
- **Evidence**: datapath.v0.4 (SEC pass), datapath.v3.4 (promoted, WNS -0.88 to -0.84)
- **Key insight**: Pre-compute all bit-level XORs in parallel at depth 1, combine in balanced tree. Requires careful analysis of dependencies.

### 10. Common Subexpression Elimination (CSE)
- **Applies to**: Designs with repeated arithmetic/comparison expressions
- **Strategy**: Extract shared subexpressions to named wires, compute once
- **Expected improvement**: WNS +2-10%, TNS +5-15%
- **Area impact**: Neutral to -5%
- **Risk**: Medium
- **Evidence**: SPI.v0.5 (SEC pass), cpu_fsm.v0.2 (promoted), datapath.v0.4 (SEC pass)
- **Key insight**: Synthesis often does CSE automatically, but explicit extraction can guide optimization. Most effective for redundant comparisons.

### 11. One-Hot FSM Encoding with Direct Bit Equations
- **Applies to**: FSM with 4+ states using binary encoding
- **Strategy**: Convert to one-hot encoding with direct AND-OR equations for next-state logic
- **Expected improvement**: WNS +30-60%, TNS +30-50%
- **Area impact**: Variable (-30% to +100% depending on state count)
- **Risk**: Medium (encoding change may fail SEC if not done carefully)
- **Evidence**: vending_machine.v0.3 (WNS -0.27 to -0.09, but area doubled), vending_machine.v0.5 (promoted with balanced area), ticket_machine.v0.8 (promoted)
- **Key insight**: Eliminates case statement decode depth. Best combined with mux restructuring to control area. May require careful output logic restructuring.

---

## Low-Confidence / Risky (use with caution)

### 12. Parallel Evaluation with Logic Flattening
- **Applies to**: Priority-encoded if-else chains in FSM
- **Strategy**: Replace if-else priority chain with parallel AND-OR equations
- **Expected improvement**: WNS +30-40% when successful
- **Area impact**: Variable
- **Risk**: High (frequently fails SEC due to subtle priority differences)
- **Evidence**: ticket_machine.v0.1 (SEC FAILED despite 39% WNS improvement)
- **Key insight**: Priority semantics may be lost in transformation. If-else and case statements may not be functionally equivalent to AND-OR. Use only when priority is not required.

### 13. Count-Down Counter Restructuring
- **Applies to**: Counters with comparison to parameter (e.g., `count == MAX_COUNT`)
- **Strategy**: Convert count-up with comparison to count-down with zero-detect
- **Expected improvement**: Potentially significant (removes wide comparator)
- **Area impact**: Neutral
- **Risk**: High (changes counting behavior, frequently fails SEC)
- **Evidence**: UART.v0.1 (SEC FAILED), UART.v0.3 (SEC FAILED)
- **Key insight**: Zero-detect is simpler than N-bit equality, but behavior changes from counting 0->N to N->0. This changes when terminal count occurs relative to reload, often breaking equivalence.

### 14. Explicit Intermediate Wire Decomposition
- **Applies to**: Deeply nested expressions, cascaded multipliers
- **Strategy**: Decompose nested expressions into named intermediate wires for synthesis guidance
- **Expected improvement**: WNS +2-5%
- **Area impact**: Neutral
- **Risk**: Medium (depends heavily on synthesis tool behavior)
- **Evidence**: LSTM.v0.8 (SEC pass but minimal improvement), LSTM.v0.2 (score -0.108)
- **Key insight**: Conservative approach that rarely hurts but may not help. Synthesis may ignore wire decomposition. Most effective for very deep combinational chains.

### 15. Aggressive Mux Tree Restructuring
- **Applies to**: Wide 4:1 muxes, unbalanced mux trees
- **Strategy**: Convert flat 4:1 mux to balanced 2-level 2:1 mux tree
- **Expected improvement**: WNS +5-10%
- **Area impact**: +5-10%
- **Risk**: Medium (synthesis may undo restructuring)
- **Evidence**: DSP.v0.4 (SEC pass, score 0.020 - modest improvement)
- **Key insight**: Modern synthesis tools are good at mux optimization. Explicit restructuring may conflict with synthesis decisions.

---

## Anti-Patterns (avoid)

### A1. Changing Counter Direction (Count-Up to Count-Down)
- **Problem**: Changes when terminal count is generated relative to counter operations
- **Evidence**: UART.v0.1, UART.v0.3 (both SEC FAILED)
- **Recommendation**: Keep original counter direction. Instead, use pre-computed comparison wires.

### A2. Aggressive Priority Chain Flattening
- **Problem**: If-else priority semantics may be lost when converted to parallel AND-OR
- **Evidence**: ticket_machine.v0.1 (SEC FAILED despite timing improvement)
- **Recommendation**: Preserve if-else structure when inputs can be active simultaneously. Only flatten when mutual exclusion is guaranteed.

### A3. Pre-Registering Selector Signals in Mux Paths
- **Problem**: Adds latency to control path, changing when mux selection occurs
- **Evidence**: vending_machine.v0.4 (SEC FAILED - pre-registering sel caused latency change)
- **Recommendation**: Keep selector signals combinational. Register datapath signals instead.

### A4. Modifying Memory Array Addressing
- **Problem**: Inherent fanout in memory address decode cannot be optimized without architectural changes
- **Evidence**: cpu_fsm (paths 2, 7 skipped as out-of-scope)
- **Recommendation**: Accept memory paths as fixed. Focus optimization on surrounding logic.

### A5. Optimizing Register Self-Loop Paths
- **Problem**: Timing reports showing reg->reg paths are clock-to-Q + setup constraints, not logic paths
- **Evidence**: DSP (paths 7-10 skipped - register self-loop constraints)
- **Recommendation**: Ignore these paths in optimization. They require clock tree optimization, not RTL changes.

### A6. Changing LFSR Feedback Structure
- **Problem**: LFSR polynomials are mathematically defined; structural changes break function
- **Evidence**: pcie (paths 3, 4 skipped - LFSR feedback paths)
- **Recommendation**: Accept LFSR timing as fixed. Optimize surrounding scrambler/descrambler logic instead.

---

## Path Type to Strategy Mapping

| Path Characteristic | Recommended Strategy | Confidence |
|---------------------|---------------------|------------|
| FSM state decode to output | One-hot pre-decode (#1), FSM output registration (#4) | High |
| Counter with comparison | Condition pre-computation (#2), wire extraction | High |
| High-fanout control signal | Register duplication (#3), input registration (#5) | High |
| Arithmetic gated by control | Late mux-select (#6), mux-before-adder (#7) | Medium |
| Large case/lookup table | Hierarchical decomposition (#8) | Medium |
| GF/crypto arithmetic | Logic tree balancing (#9), CSE (#10) | Medium |
| Binary-encoded FSM | One-hot encoding (#11) - with caution | Medium |
| Deeply nested ternary | Wire decomposition (#14) - modest benefit | Low |
| Priority-encoded chain | AVOID parallel flattening | Anti-pattern |
| Memory array paths | SKIP - out of scope | N/A |

---

## Strategy Success by Design Type

| Design Type | Best Strategies | SEC Pass Rate |
|-------------|-----------------|---------------|
| FSM-heavy (ticket_machine, vending_machine) | One-hot (#1, #11), mux-before-adder (#7) | 60% |
| Communication (UART, SPI, router) | Input registration (#5), FSM output reg (#4), condition pre-compute (#2) | 70% |
| Pipeline (router, FIFO) | Register duplication (#3), input registration (#5) | 80% |
| Datapath (DSP, LSTM, datapath) | Tree balancing (#9), CSE (#10), wire decomposition (#14) | 65% |
| Encoder/Decoder (pcie) | Hierarchical decomposition (#8) | 85% |
| Controller (cpu_fsm, controller) | One-hot pre-decode (#1), condition pre-compute (#2) | 90% |

---

## Statistics

| Strategy | Attempts | Successes | Rate | Avg WNS Improvement |
|----------|----------|-----------|------|---------------------|
| One-hot pre-decode | 12 | 11 | 92% | +8% |
| Condition pre-computation | 18 | 16 | 89% | +5% |
| Register duplication | 8 | 7 | 88% | +7% |
| FSM output registration | 10 | 9 | 90% | +8% |
| Input signal registration | 14 | 12 | 86% | +10% |
| Late mux-select | 6 | 4 | 67% | +12% |
| Mux-before-adder | 4 | 3 | 75% | +40% |
| Hierarchical decomposition | 5 | 4 | 80% | +35% |
| Logic tree balancing | 8 | 5 | 63% | +6% |
| CSE | 10 | 7 | 70% | +4% |
| One-hot FSM encoding | 8 | 5 | 63% | +35% |
| Parallel logic flattening | 6 | 2 | 33% | +35% (when successful) |
| Count direction change | 4 | 0 | 0% | N/A |
| Wire decomposition | 12 | 10 | 83% | +3% |

---

## Design-Specific Observations

### High-Success Designs (>70% SEC pass across iterations)
- **cpu_fsm**: 47/50 SEC pass (94%). Responds well to one-hot pre-decode, register file indexing optimization.
- **FIFO**: 48/50 SEC pass (96%). Pipeline-friendly; late mux-select and input registration work well.
- **pcie**: 48/50 SEC pass (96%). Hierarchical decoder decomposition highly effective.
- **SPI**: 49/50 SEC pass (98%). Conservative optimizations most successful.
- **datapath**: 45/50 SEC pass (90%). GF arithmetic tree balancing effective.

### Medium-Success Designs (50-70% SEC pass)
- **vending_machine**: 38/50 SEC pass (76%). One-hot FSM works but area-sensitive.
- **router**: 35/50 SEC pass (70%). Sequential optimizations work; combinational changes risky.
- **DSP**: 37/50 SEC pass (74%). Multiplier-limited; mux restructuring helpful for non-multiplier paths.
- **LSTM**: 28/50 SEC pass (56%). Very deep combinational paths; conservative approaches needed.

### Low-Success Designs (<50% SEC pass)
- **UART**: 24/50 SEC pass (48%). Counter logic very sensitive to restructuring.
- **ticket_machine**: 25/50 SEC pass (50%). FSM encoding changes frequently fail.
- **simple_spi**: 5/13 SEC pass (38%). Design appears highly optimized; aggressive changes cause synthesis failures.
- **cpu_pipe**: 22/50 SEC pass (44%). Complex pipeline timing; many SEC failures.

---

## Lessons Learned

1. **Conservative wins over aggressive**: High SEC pass rate more important than large improvements. A 5% improvement that passes SEC beats a 30% improvement that fails.

2. **Sequential optimizations are safer**: Adding registers (strategies #3, #4, #5) rarely break SEC. Combinational restructuring is higher risk.

3. **Pre-computation beats restructuring**: Extracting conditions to wires (#1, #2) is safer than restructuring logic (#7, #11, #12).

4. **Design complexity matters**: Simple designs (FIFO, SPI) tolerate more aggressive optimization. Complex designs (LSTM, cpu_pipe) need conservative approaches.

5. **Module-focused optimization works**: Targeting specific modules (pcie decoder, datapath sBox) more successful than whole-design changes.

6. **Diversity strategy helps discovery**: Different path selection (endpoint clustering, high fanout, module-focused) finds different optimization opportunities.

7. **Baseline sensitivity varies**: Some designs (simple_spi) are already highly optimized; aggressive changes cause synthesis failures rather than SEC failures.

---

## Recommended Workflow

1. **Start with low-risk strategies** (#1, #2, #3, #4, #5) - high SEC pass rate
2. **Measure improvement** before trying higher-risk strategies
3. **Module-focus** when design has clear timing bottleneck
4. **Avoid anti-patterns** - counter direction, priority flattening, selector registration
5. **Accept architectural limits** - multipliers, memories, LFSRs
6. **Combine strategies** when individual strategies plateau (e.g., one-hot + mux-before-adder)
# RTL Optimization Skill Summary

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
