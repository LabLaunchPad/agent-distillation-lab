"""Shot 3: one tiny seeded task generator. Stdlib only."""
import random

# ponytail: single-task dict; add variants here only when Shot 4 needs them.
_TASKS = {
    "restaurant-landing": (
        "Build a single-file static restaurant landing page named index.html in the "
        "current directory. Requirements: <html lang>, <title>, viewport meta, header "
        "with nav (2+ links), main with h1 + menu section (3+ items) + contact section, "
        "footer, one <style> block with fluid CSS (max-width, flexible units) and one "
        "media query, every <img> (if any) with alt text. No external deps, no JS "
        "frameworks. Keep it small (<15KB)."
    ),
    "restaurant-name": ["Verde Fork", "Salt & Ember", "Mesa Verde", "Copper Ladle"],
}


def generate(seed=42):
    """Deterministic: seed picks the restaurant name variant."""
    rng = random.Random(seed)
    name = rng.choice(_TASKS["restaurant-name"])
    prompt = _TASKS["restaurant-landing"].replace("restaurant", name, 1)
    return {"task_id": f"restaurant-landing:s{seed}", "title": f"{name} landing page",
            "prompt": f"Restaurant name: {name}. " + _TASKS["restaurant-landing"],
            "seed": seed}


if __name__ == "__main__":
    import json
    print(json.dumps(generate(), indent=2))
