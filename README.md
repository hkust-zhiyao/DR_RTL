# Dr. RTL: Autonomous Agentic RTL Optimization through Tool-Grounded Self-Improvement

Agent-driven framework for iterative RTL timing optimization, with synthesis and sequential equivalence checking (SEC) in the loop.

Claude Code sub-agents analyze synthesized timing reports, propose RTL-level transformations, and verify each attempt against the original design. Over up to 10 major rounds (5 minor attempts each), the best-scoring SEC-passing version is promoted forward.

## Directory layout

```
drrtl/
├── CLAUDE.md               # Orchestrator rules (workflow, scoring, end criteria)
├── .claude/
│   ├── agents/             # Sub-agent definitions (timing, optimizer, evaluator, skill extractor)
│   └── skill/rtl-opt/      # RTL optimization skill pack
├── rtl_dataset/            # Baseline RTL designs (v0) — aes, arm_cpu*, tv80, i2c, pcie, ...
├── syn_flow/               # Optimization loop working directory
│   ├── rtl/                # Versioned RTL: <design>.v0.v, <design>.v0.1.v, ...
│   ├── log/                # Per-iteration iter.json files
│   ├── history/            # Per-design history.json (major rounds + promotions)
│   ├── output/             # Synthesis outputs: PPA_report.json, timing_word.json, SEC_result.txt
│   ├── design_all.json     # Design config: [top, clk, rst, ext]
│   ├── run_remote.py       # SSH + SCP wrapper that runs synthesis on the EDA host
│   └── add_design_remote.py
└── syn_flow_eda/           # Runs on the EDA machine (DC / Formality / Jasper SEC)
    ├── run_design.py       # Orchestrates dc_shell, fm_shell, jaspergold
    ├── scr/                # TCL templates: syn.tcl, fm.tcl, sec.tcl
    ├── lib/nangate.db      # Nangate standard-cell library
    └── reports/ netlist/ output/ log/
```

## Workflow

For each major version `v0` → `v9`:
1. Run 5 minor attempts (`vX.1` … `vX.5`), each with a distinct diversity strategy chosen by the orchestrator.
2. For every minor: **analyze** critical paths → **optimize** RTL → **synthesize + SEC** → **record** score.
3. Pick the lowest-scoring SEC-passing minor, promote it to the next major version.

Stop when `v10` is created (`max_major_reached`) or a full round completes with no promotion (`no_improvement`).

See `CLAUDE.md` for the authoritative spec.

## Sub-agents

| Agent | Role |
|---|---|
| `rtl-timing-analyzer` | Select K=10–25 critical paths from `timing_word.json`, diagnose root causes, classify amenability. |
| `rtl-optimizer` | Apply RTL transformations; SEC validates functional equivalence. |
| `rtl-synthesis-evaluator` | Run remote synthesis + SEC via a single Python command. Execution only. |
| `rtl-opt-skill-extractor` / `-per-design` | Distill reusable optimization patterns from completed trajectories. |

## Scoring

Lower is better. Baseline is `v0` for each design.

```
score = 0.5·WNS_norm + 0.35·TNS_norm + 0.15·Area_norm + penalty
WNS_norm  = (WNS  − WNS_baseline)  / |WNS_baseline|
TNS_norm  = (TNS  − TNS_baseline)  / |TNS_baseline|
Area_norm = (Area − Area_baseline) / Area_baseline
penalty   = 0.5 if Area_norm > 0.10 else 0
```

## Running

The orchestrator (Claude Code) drives the loop. Synthesis itself runs remotely:

```bash
# From syn_flow/: upload RTL, run DC + SEC on the EDA host, download reports
python3 run_remote.py <design> <version>      # e.g. tv80 v0.1

# Locally on the EDA host (syn_flow_eda/):
python3 run_design.py <design> <version>      # dc_shell → jaspergold → parse reports
```

Requires Synopsys Design Compiler, Synopsys Formality, and Cadence JasperGold on the EDA host, plus `paramiko` and `scp` locally.

## Artifacts per iteration

- `syn_flow/log/<design>.<version>.iter.json` — diversity strategy, critical paths, before/after metrics, score.
- `syn_flow/history/<design>.history.json` — baseline PPA, best version, promotion log across major rounds.
- `syn_flow/output/<design>.<version>/` — `PPA_report.json`, `timing_word.json`, `SEC_result.txt`.
