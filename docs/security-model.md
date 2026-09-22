# Security model

1. Local-first: trajectories stay in `data/` (gitignored). No cloud upload in P0.
2. Redaction at capture: `src/redact.py` strips `sk-*`, bearer tokens, emails, private keys before validation/storage. Shot 2 must call it.
3. Secret scanning: run `gh secret-scanning` / `gitleaks` or `git diff --cached | grep -Ei 'sk-|AKIA|BEGIN .*PRIVATE'` before every commit; never commit `.env`, `auth.json`, `opencode.db`.
4. Least privilege: read-only access to OpenCode SQLite (`mode=ro`); never write to agent store.
5. Provenance: record `source` + `license` per trajectory; drop non-permissive (MIT/Apache/BSD) like Open-SWE-Traces.
