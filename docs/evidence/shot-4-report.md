# Shot 4 evidence report — multi-teacher distillation (small set)

Date: 2026-09-22. Branch: `shot-4-multiteacher`. Base: main @ d0201b8 (PR #3 merged).
Seed: 42, one task (`restaurant-landing:s42`), 3 teachers. No scaling, no adversarial harness (Shot 5).

## 1. Teachers (same seed, teacher-model param)

`src/multiteacher.py::TEACHERS` × `taskgen.generate(42)`:
- `opencode/ling-3.0-flash-fin-free` — real Shot 3 run (session `ses_f3546…`), GOLD, scores reused from `data/curated/shot3-s42.json` (already verified, not re-fabricated).
- `fixture/silver-variant` — labeled fixture (GOOD HTML minus the `@media` query), **real `verify_artifact` run**: functional 6/6, responsive 2/3, a11y 4/4 → SILVER.
- `fixture/fail-variant` — labeled fixture (broken HTML), **real `verify_artifact` run** → FAIL (9 failed checks).
All scores computed, none invented. Live second-teacher `opencode run` deferred (cost); fixtures are explicitly flagged `"fixture": true`.

## 2. Disagreement + quality distribution (`src/compare.py`)

Verdicts: GOLD 1 / SILVER 1 / FAIL 1 (n=3, rates 0.333 each) → `disagrees = true`.
Duplicate rate 0.0 (3 distinct artifact shas). Failure modes: `viewport_375` ×2 (the SILVER miss + FAIL), FAIL-only: `has_title`, `has_h1`, `nav_links>=2`, `has_main_sections`, `has_header_footer`, `viewport_768/1440`, `html_lang`, `img_alt`.
Threshold check: SILVER case (functional all-pass + rest 6/7) lands SILVER under the rule-based cut — GOLD/SILVER boundary behaves on ≥2 distinct teachers. Calibration holds; no cut change.

## 3. SFT message-selection policy (Shot 3 wart fixed)

Per-message roles, not whole blobs: user = seeded prompt; assistant = last substantive assistant message with pure size-check asides (`^\d+ bytes…Done.`) dropped line-wise. Shot 3 trajectory → 337-char clean summary (was 1230-byte blob with aside). Implemented in `select_sft_messages()`, covered by test.

## 4. Preference / DPO / verifier exports

- `data/prefs/shot4-s42-pair.json` (schema `schemas/preference.v1.json`): chosen GOLD (real teacher) > rejected FAIL (fixture), criterion = rule-based verdict rank. No pair when teachers agree (`make_pair` → None).
- `data/dpo/shot4-s42.jsonl`: prompt + chosen assistant text + rejected (failed-check summary).
- `data/sft/shot4-s42.jsonl`: 1 line, GOLD teacher, per-message selection + provenance.
- Verifier data: curated records carry full `checks`/`scores` per teacher.

## 5. Active selection for expensive judging

`compare.active_selection()`: SILVER first (borderline), then FAIL (failure mining), then GOLD (trusted). Order on this set: silver → fail → ling-flash. Only disagreements/borderlines go to costly judges; unanimous GOLDs skip.

## 6. Tests — 19/19 pass

`python -m unittest discover -s tests` → OK (12 prior + 7 new `test_compare.py`: distribution, duplicate rate, failure-mode counts, disagreement + judging order, pair ranking + agree→None, aside-filter, schema shape).

## 7. Files added

`src/multiteacher.py`, `src/compare.py`, `schemas/preference.v1.json`, `tests/test_compare.py`, `data/curated/shot4-s42-*.json` (3), `data/sft/shot4-s42.jsonl`, `data/prefs/shot4-s42-pair.json`, `data/dpo/shot4-s42.jsonl`, `docs/evidence/shot-4-report.md`. Stdlib only.
