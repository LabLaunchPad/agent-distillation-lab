# Roadmap

- Shot 1 (P0, this): scaffolding + evidence ledger + schema stub + redaction stub. No training.
- Shot 2: OpenCode capture (`export --sanitize` / read-only SQLite) → redact → validate v1 → `data/trajectories/*.jsonl`.
- Shot 3: quality/selection (dedupe, LESS-style influence filter, 20–50 case eval packs for SWE + WebGen/DesignBench axes).
- Shot 4: SFT only (TRL `SFTTrainer`), offline, small-model smoke test.
- Shot 5: DPO then Step-GRPO (TRL), multi-model compare, adversarial/robustness harness.

Out of scope Shot 1: any training, multi-model runners, adversarial harness.
