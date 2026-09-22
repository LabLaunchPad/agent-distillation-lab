"""Shot 3 tests: verifier runs for real on good/bad HTML. Stdlib unittest."""
import os
import tempfile
import unittest

from src.verify import (check_a11y, check_functional, check_responsive,
                        evaluate, parse_html, verify_artifact)

GOOD = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>T</title><style>.w{max-width:60rem;width:100%;display:flex}
@media (max-width:40rem){.w{display:block}}</style></head>
<body><header><nav><a href="#m">M</a><a href="#c">C</a></nav></header>
<main><h1>T</h1><h2 id="m">Menu</h2><h2 id="c">Contact</h2></main>
<footer>F</footer></body></html>"""
BAD = "<html><head><title></title></head><body><p>no</p><img src=x></body></html>"


def _tmp(html):
    fd, p = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    return p


class TestVerify(unittest.TestCase):
    def test_good_scores_gold(self):
        p = _tmp(GOOD)
        try:
            f = parse_html(p)
            ev = evaluate(check_functional(f), check_responsive(f), check_a11y(f))
            self.assertEqual(ev["verdict"], "GOLD", ev)
        finally:
            os.remove(p)

    def test_bad_not_gold(self):
        p = _tmp(BAD)
        try:
            f = parse_html(p)
            ev = evaluate(check_functional(f), check_responsive(f), check_a11y(f))
            self.assertNotEqual(ev["verdict"], "GOLD", ev)
            fails = [c for g in (check_functional(f), check_a11y(f)) for c in g
                     if not c["passed"]]
            self.assertTrue(fails)  # real failures, not fabricated passes
        finally:
            os.remove(p)

    def test_verify_artifact_end_to_end(self):
        p = _tmp(GOOD)
        try:
            rec = verify_artifact(p, seed=42)
            self.assertEqual(rec["schema_version"], "1.0")
            self.assertEqual(rec["verdict"], "GOLD")
            self.assertEqual(len(rec["artifact_sha256"]), 64)
            self.assertIn("sha256", rec["fingerprint"])
        finally:
            os.remove(p)


if __name__ == "__main__":
    unittest.main()
