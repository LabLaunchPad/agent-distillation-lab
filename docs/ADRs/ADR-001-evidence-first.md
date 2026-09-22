# ADR-001: Evidence-first

Status: accepted. Date: 2026-09-22.

Context: Distillation claims are cheap; traces + evals are proof (OpenAI Stored Completions + Evals loop; WebGen-Bench 647 tests).

Decision: Every design/training claim links to `docs/research/evidence-ledger.md`. No trajectory ships without `test_result`/`resolved` or grader refs where applicable.

Consequences: Slower start, reproducible gains. Schema carries provenance fields.
