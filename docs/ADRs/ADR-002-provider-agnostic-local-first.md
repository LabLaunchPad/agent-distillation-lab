# ADR-002: Provider-agnostic, local-first

Status: accepted. Date: 2026-09-22.

Context: OpenCode supports any Models.dev provider; SQLite/JSON export is local. Vendor lock-in kills reproducibility.

Decision: Capture from local OpenCode artifacts (`export --sanitize`, read-only SQLite). Store as local JSONL. `provider`/`model` are opaque strings in schema. No provider SDK in repo.

Consequences: Works offline; no keys needed for P0. Multi-model comparison is a query, not a rewrite.
