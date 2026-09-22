# agent-distillation-lab

Evidence-first AI distillation / data-engineering lab. Local-first, provider-agnostic.

Status: Shot 1 (P0 foundation). No training code yet.

## Layout

- `docs/research/` — evidence ledger + summary (sources for all design choices)
- `docs/architecture.md` — principles, components, capability matrix
- `docs/ADRs/` — ADR-001..003
- `docs/roadmap.md` — Shots 1–5
- `docs/security-model.md` — local-first, redaction, secret scanning
- `schemas/trajectory.v1.json` — versioned trajectory schema stub (v1)
- `src/redact.py` — stdlib-only redaction stub

## Quickstart (Shot 1)

```sh
python -c "from src.redact import redact; print(redact('key sk-abc123 secret'))"
```

No deps. Python 3.10+ stdlib only.

## Next (Shot 2)

OpenCode trajectory capture → validate against `schemas/trajectory.v1.json` → store locally.
