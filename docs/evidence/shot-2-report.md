# Shot 2 evidence report — OpenCode trajectory capture foundation

Date: 2026-09-22. Branch: `shot-2-capture`. Base: main @ 49f77d6.

## 1. Real OpenCode compatibility probe (no fabricated data)

```
opencode --version          -> 1.18.32
opencode db path            -> C:\Users\pithu\.local\share\opencode\opencode.db
opencode export --sanitize  -> supported (flag present in export --help)
probe(): {"db_path": ".../opencode.db", "export_sanitize": true,
          "opencode_bin": ".../npm/opencode.CMD", "opencode_version": "1.18.32"}
```

## 2. Real DB surface (read-only `mode=ro` via stdlib sqlite3, never written)

Tables/rows: `session` 318, `message` 16413 (roles: assistant 15290 / user 1132),
`part` 72420 (tool 24435, step-start 15131, step-finish 15111, reasoning 11782,
text 5305, patch 495, file 92), `permission` 0 rows (table exists:
action/resource — captured, empty), `event` 301129.
Key shapes: message data `{agent,model,role,summary,time}`;
tool part `{callID, tool:str, state:{status,input,output/title,error,time}}`;
patch part `{files,hash,type}`; step-finish `{cost,reason,tokens,type}`.
Export shape: `{info:{id,agent,model{id,providerID},title,directory,...},
messages:[{info:{role,...}, parts:[...]}]}`.

## 3. Live end-to-end capture (latest real session, redacted in-memory)

`load_session` -> `normalize` -> `validate`: session with 15 messages / 60 parts
-> trajectory 31748 bytes, sha256 `32562369…`, 21 tool_calls (incl. `patch`
file-changes), 13 errors captured, model `opencode/muse-spark-1.3-contributor-free`.
Trajectory + provenance validate against v1 schemas. Raw session content never
leaves the machine; only shapes/counts are reported here.

## 4. Contract coverage

1. Compatibility probe — `capture.probe()` (version, db path, `--sanitize` flag).
2. Session identification — `session.id` from export `info` or `session` row.
3. Tool calls / file changes / commands — tool parts + patch parts + bash inputs.
4. Errors / permissions — `state.status=error`, `state.error`, step-finish
   `reason`; `permission` table (empty live, plumbed through).
5. Normalized to trajectory.v1 — `normalize()` returns exact-schema dict.
6. artifact.v1 + provenance.v1 — `to_artifact()`; full provenance
   (session_id, opencode_version, sanitized, captured_at) validated separately.

Guarantees: redact-then-scan (`src/redact.py` + `scan_residual`, refusal on
residual); deterministic bytes (`sort_keys`, compact separators, sha256);
output target `data/trajectories/*.jsonl` (gitignored, local only).
Fixture: `fixtures/opencode-export.fixture.json` is synthetic and labeled
`"fixture": true` — the only non-real data in the repo.

## 5. Tests (stdlib unittest, 9/9 pass)

`python -m unittest discover -s tests` -> OK (9 tests, incl. live read-only DB
integration + replay determinism: same fixture -> identical bytes,
sha256 `b5c69380…`, JSONL round-trip stable).

## 6. Files added

`src/capture.py`, `src/validate.py`, `schemas/artifact.v1.json`,
`schemas/provenance.v1.json`, `fixtures/opencode-export.fixture.json`,
`tests/test_capture.py`, `tests/test_replay.py`, `docs/evidence/shot-2-report.md`.
No new deps (stdlib only). `data/` untouched by commits (gitignored).

## 7. Skipped / Shot 3

Skipped: LESS-style selection, eval packs, SFT — Shot 3/4 scope.
