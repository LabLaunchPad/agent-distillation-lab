"""Shot 4: teacher-disagreement analysis. Stdlib only."""
from collections import Counter

# ponytail: plain Counter dicts; pandas when records > ~10k.
def verdict_distribution(records):
    return dict(Counter(r["verdict"] for r in records))


def duplicate_rate(records):
    """1 - unique_artifact_shas/total (1.0 = all identical)."""
    if not records:
        return 0.0
    return 1.0 - len({r["artifact_sha256"] for r in records}) / len(records)


def failure_modes(records):
    """Count failed check names across all FAIL/SILVER records."""
    counts = Counter()
    for r in records:
        for group in (r.get("checks") or {}).values():
            if not isinstance(group, list):
                continue  # shorthand (e.g. {"note": ...}) carries no checks
            for c in group:
                if not c.get("passed"):
                    counts[c.get("name", "unknown")] += 1
    return dict(counts)


def quality_distribution(records):
    dist = verdict_distribution(records)
    n = len(records) or 1
    return {k: {"count": v, "rate": round(v / n, 3)} for k, v in sorted(dist.items())}


def disagrees(records):
    return len({r["verdict"] for r in records}) > 1


def active_selection(records):
    """Cheapest-first order for expensive judging: borderline SILVER,
    then FAIL (failure mining), then GOLD (already trusted)."""
    pri = {"SILVER": 0, "FAIL": 1, "GOLD": 2}
    return [r["teacher"] for r in sorted(records, key=lambda r: pri.get(r["verdict"], 9))]
