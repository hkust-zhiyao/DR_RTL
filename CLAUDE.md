# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RTL synthesis and SEC-based verification automation framework.
- Automates logic synthesis using Synopsys Design Compiler (DC)
- Runs Jasper SEC to verify equivalence between optimized and original RTL
- Supports iterative RTL timing optimization in an agent-driven workflow


## RTL Timing Optimization Workflow
```
For each major version (v0 to v9):
    Run 5 minor attempts (vX.1 to vX.5)
    Select best SEC-pass minor → Promote to next major

Stop after v10 is created
```

### Steps Per Minor

1. **ANALYZE**: @agent-rtl-timing-analyzer
2. **OPTIMIZE**: @agent-rtl-optimizer  
3. **EVALUATE**: @agent-rtl-synthesis-evaluator
4. **RECORD**: Update iter.json with results and score

### After All 5 Minors

5. **SELECT**: Best SEC-pass minor (lowest score)
6. **PROMOTE**: Rename to next major version
7. **UPDATE**: history.json


## Diversity Strategy

Orchestrator defines the strategy for each minor attempt at runtime.

**Available options**:
- Path selection: top-K by slack, path range, endpoint clustering, high fanout, module-focused, random sample
- Optimization focus: combinational, sequential, mixed

Orchestrator should ensure diversity across the 5 minors to explore different optimization opportunities.


## Scoring Formula

Lower score = better.
```
score = 0.5 × WNS_norm + 0.35 × TNS_norm + 0.15 × Area_norm + penalty

WNS_norm  = (WNS - WNS_baseline) / |WNS_baseline|
TNS_norm  = (TNS - TNS_baseline) / |TNS_baseline|
Area_norm = (Area - Area_baseline) / Area_baseline

penalty = 0.5 if Area_norm > 0.10, else 0
```


## Version Control
```
v0 (baseline)
├── v0.1 ... v0.5 → Best → v1
v1
├── v1.1 ... v1.5 → Best → v2
...
v9
├── v9.1 ... v9.5 → Best → v9 (DONE)
```

### Files
```
rtl/
├── <design>.v0.v       # baseline
├── <design>.v0.1.v     # minor attempts
├── ...
├── <design>.v1.v       # promoted from best v0.x
└── <design>.v5.v       # final
```


## Iteration Data

**File**: `syn_flow/log/<design>.<version>.iter.json`
```json
{
  "design": "<design>",
  "base_version": "v0",
  "target_version": "v0.1",
  "diversity_strategy": {
    "minor_index": 1,
    "path_selection": "<orchestrator defined>",
    "optimization_focus": "<orchestrator defined>"
  },
  "wns_before": -0.45,
  "tns_before": -12.3,
  "area_baseline": 12000,
  "critical_paths": [...],
  "evaluation": {
    "sec_status": "pass",
    "wns_after": -0.32,
    "tns_after": -7.5,
    "area": 12200
  },
  "scoring": {
    "wns_norm": -0.289,
    "tns_norm": -0.390,
    "area_norm": 0.017,
    "area_penalty": 0,
    "score": -0.278
  }
}
```


## History

**File**: `syn_flow/history/<design>.history.json`
```json
{
  "design": "alu",
  "baseline": { "wns": -0.45, "tns": -12.3, "area": 12000 },
  "best_version": "v2",
  "best_ppa": { "wns": -0.18, "tns": -4.2, "area": 12350 },
  "end_reason": null,
  "major_rounds": [
    {
      "major_version": "v0",
      "minors": [
        { "version": "v0.1", "sec": "pass", "score": -0.245, "promoted": false },
        { "version": "v0.2", "sec": "fail", "score": null, "promoted": false },
        { "version": "v0.3", "sec": "pass", "score": -0.298, "promoted": true }
      ],
      "promoted_to": "v1"
    }
  ]
}
```


## End Criteria

Stop when:
- `v10` is created → `end_reason = "max_major_reached"`
- Completed all 10 major rounds with no promotions → `end_reason = "no_improvement"`


## Agent Rules

- Orchestrator delegates to agents, does NOT run synthesis directly
- Sub-agents have no memory between invocations
- Always optimize from current major version (best_version)
- Each minor is independent


## User Command

When user requests optimization:
1. Initialize: Evaluate v0, create history.json
2. Loop: 10 major rounds × 5 minors each
3. Select & Promote: Best minor → next major
4. Report: best_version and final PPA