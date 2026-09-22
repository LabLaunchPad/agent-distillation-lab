# Architecture

Principles: evidence-first (ADR-001), provider-agnostic/local-first (ADR-002), versioned schema (ADR-003).

## Components (P0 only: capture → validate → store)

```
OpenCode sessions → capture (Shot 2) → redact → validate (schemas/trajectory.v1.json) → data/trajectories/ (local JSONL)
```

Future only: select (LESS-style) → SFT (Shot 4) → DPO/GRPO (Shot 5). Not built in Shot 1.

## Capability matrix

| Capability | Shot 1 (P0) | Shot 2 | Shot 4/5 |
|---|---|---|---|
| Trajectory capture (OpenCode export/SQLite) | stub | build | — |
| Redaction + secret scan | stub (`src/redact.py`) | enforce | — |
| Schema validation (v1) | stub schema | enforce | — |
| SWE tasks (SWE-bench/Gym/Smith format) | schema-compatible | capture | SFT |
| Web tasks (DesignBench axes, WebGen-Bench grading) | schema-compatible | capture | SFT + Step-GRPO |
| Preference/RL (DPO/GRPO via TRL) | out of scope | out of scope | build |

## Storage (local)

- `data/trajectories/*.jsonl` — one trajectory per line, schema v1 (gitignored, created Shot 2).
- No cloud, no DB, no new deps. Stdlib only.
