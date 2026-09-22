"""Shot 4: multi-teacher runner. Stdlib only.

Same seed x N teachers -> verify each -> curated/SFT + prefs/DPO.
Reuses taskgen.generate / verify.verify_artifact. Teacher A is the real
Shot 3 run; other teachers are clearly-labeled fixtures (real verify
scores, computed not fabricated) unless a live opencode run is available.
"""
import json
import os
import re

from src.taskgen import generate
from src.verify import verify_artifact

# ponytail: 3-entry list is the whole "registry"; DB/config when teachers > ~10.
TEACHERS = [
    "opencode/ling-3.0-flash-fin-free",  # real Shot 3 run (GOLD)
    "fixture/silver-variant",  # labeled fixture: drops the @media query
    "fixture/fail-variant",  # labeled fixture: broken HTML
]

_RANK = {"GOLD": 3, "SILVER": 2, "FAIL": 1}

# ponytail: regex aside-filter; ML selector only if this misfires on real data.
_ASIDE = re.compile(r"^\s*\d[\d,]*\s*bytes.*done\.?\s*$", re.IGNORECASE)


def select_sft_messages(prompt, trajectory):
    """Per-message SFT policy (Shot 3 calibration): user=seeded prompt,
    assistant=last substantive assistant message (pure size-check asides
    like '2717 bytes...Done.' are skipped, not concatenated)."""
    msgs = (trajectory or {}).get("messages", [])
    assistants = [m.get("content", "") for m in msgs if m.get("role") == "assistant"]
    substantive = [t for t in assistants if t and not _ASIDE.match(t.strip())]
    # last substantive message may still bundle an aside line; drop such lines.
    pick = substantive[-1] if substantive else (assistants[-1] if assistants else "")
    lines = [ln for ln in pick.splitlines() if not _ASIDE.match(ln.strip())]
    return [{"role": "user", "content": prompt},
            {"role": "assistant", "content": "\n".join(lines).strip()}]


def run_seed(seed=42, html_by_teacher=None, out_dir="."):
    """Verify one html artifact per teacher; emit curated + sft records.

    html_by_teacher: {teacher: html_path}. Missing entries are skipped
    (no fabrication). Returns list of curated records.
    """
    task = generate(seed)
    records = []
    for teacher in TEACHERS:
        path = (html_by_teacher or {}).get(teacher)
        if not path or not os.path.exists(path):
            continue  # ponytail: skip, never invent a score
        ev = verify_artifact(path, seed=seed)
        rec = {"task_id": task["task_id"], "seed": seed, "teacher": teacher,
               "fixture": teacher.startswith("fixture/"),
               "artifact_sha256": ev["artifact_sha256"],
               "verdict": ev["verdict"], "scores": ev["scores"],
               "checks": ev.get("checks", {}),
               "fingerprint": ev.get("fingerprint", {})}
        records.append(rec)
        _write_jsonl(os.path.join(out_dir, "data", "sft", f"shot4-s{seed}.jsonl"),
                     {"task_id": task["task_id"], "seed": seed,
                      "teacher": teacher, "verdict": ev["verdict"],
                      "messages": select_sft_messages(task["prompt"], {"messages": []}),
                      "provenance": {"artifact_sha256": ev["artifact_sha256"]}})
    for rec in records:
        with open(os.path.join(out_dir, "data", "curated",
                               f"shot4-s{seed}-{rec['verdict'].lower()}.json"),
                  "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1, sort_keys=True)
    return records


def make_pair(records, task_id, prompt):
    """Best (chosen) vs worst (rejected) by GOLD>SILVER>FAIL. None if agree."""
    if len({r["verdict"] for r in records}) < 2:
        return None  # no disagreement -> no pair
    ordered = sorted(records, key=lambda r: _RANK[r["verdict"]])
    lo, hi = ordered[0], ordered[-1]
    return {"schema_version": "1.0", "task_id": task_id, "prompt": prompt,
            "chosen": {"teacher": hi["teacher"], "verdict": hi["verdict"],
                       "artifact_sha256": hi["artifact_sha256"]},
            "rejected": {"teacher": lo["teacher"], "verdict": lo["verdict"],
                         "artifact_sha256": lo["artifact_sha256"]},
            "criterion": "verify verdict GOLD>SILVER>FAIL, rule-based"}


def _write_jsonl(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True) + "\n")


if __name__ == "__main__":
    print(json.dumps({"seed_task": generate(42)["task_id"], "teachers": TEACHERS}))
