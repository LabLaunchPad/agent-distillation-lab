# Shot 3 evidence report — P0 vertical slice (one complete frontend loop)

Date: 2026-09-22. Branch: `shot-3-slice`. Base: main @ eb3368d. Seed: 42.

## 1. Task (seeded, deterministic)

`src/taskgen.py::generate(42)` -> `restaurant-landing:s42`, "Verde Fork landing page".
Same seed -> same prompt (stdlib `random.Random(42)`; name list order fixed).
Single-file static restaurant landing page, all requirements machine-checkable.

## 2. Real teacher run (isolated workspace, not the repo)

- Teacher: `opencode/ling-3.0-flash-fin-free` (repo default model, one teacher only).
- `opencode run --format json --model <teacher> --dir <tmp>/shot3-s42` (fresh dir, nothing else in it).
- Session `ses_f3546fd31ffeSYD8WK8ULAhE1r`: 5 messages / 17 parts / 3 tool calls
  (1 file-write + 2 size checks), 3 step-finish `tool-calls` markers as errors.
- Output: `index.html`, 2717 bytes (<15KB). Workspace diff = 1 new file, nothing else.
- Trajectory captured via Shot 2 pipeline (`load_session` read-only -> `normalize` ->
  `validate`): 6576 bytes, sha256 `daafa463…`, stored `data/trajectories/shot3-s42.jsonl`
  (local only, gitignored). Permission table empty live again — tolerated, plumbed as `[]`.

## 3. Independent verification (not the teacher)

`src/verify.py` (stdlib `html.parser` + regex, reads the real file; every check computed):
functional 6/6, responsive 3/3 (viewport meta + fluid CSS + `@media`, method=static),
a11y 4/4 -> **GOLD**. Fingerprint: py3.13.15 / Windows-11 / opencode 1.18.32 / seed 42
(`cd07c18f…`). Eval schema `schemas/eval.v1.json`, `validate_eval()` added. Artifact
sha256 `2e7bddb6…` (verified file) vs redacted-artifact sha `7dd8f8ad…` (redaction changes
bytes — expected, both recorded in `data/curated/shot3-s42.json`).

## 4. Real browser renders (375 / 768 / 1440)

Playwright CLI (pre-installed, v1.63.0) + installed Edge (`--channel msedge`, zero
downloads) over local `http.server`: `data/renders/shot3-s42-{375,768,1440}.png`
(29/37/43KB, hashes in curated record). Inspected all three: header stacks Centered at
375 (media query fires), horizontal at 768/1440, no overflow/overlap, menu prices
right-aligned, footer present. Visual quality: clean, coherent — GOLD stands.
Renders local only (gitignored); hashes committed via curated record.

## 5. Curated record + SFT example (derived, not hand-written)

- `data/curated/shot3-s42.json`: task/seed/teacher/session/trajectory+artifact shas,
  eval verdict+scores, render hashes, fingerprint, permissions. Committed (`-f`, small).
- `data/sft/shot3-s42.jsonl`: 1 line, user=seeded prompt, assistant=trajectory final
  message (redacted), provenance with both shas. 1230 bytes. Committed (`-f`, small).
- Known wart: assistant target concatenates teacher's size-check aside
  ("2717 bytes…Done.") with its final summary — genuine trajectory content, kept as-is;
  message-selection policy is Shot 4 scope.

## 6. Tests (stdlib unittest, 12/12 pass)

`python -m unittest discover -s tests` -> OK (9 Shot 2 + 3 new `test_verify.py`:
good HTML scores GOLD, bad HTML really fails, `verify_artifact` end-to-end incl. sha).

## 7. Files added/changed

`src/taskgen.py`, `src/verify.py`, `src/validate.py` (+`validate_eval`),
`schemas/eval.v1.json`, `tests/test_verify.py`, `data/curated/shot3-s42.json`,
`data/sft/shot3-s42.jsonl`, `docs/evidence/shot-3-report.md`.
No new deps (stdlib only). No multi-teacher logic, no adversarial harness (Shots 4/5).

## 8. Skipped / Shot 4 readiness

Skipped: per-message SFT selection, multi-seed/task batching, learned thresholds.
