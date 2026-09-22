"""Shot 4 tests: disagreement analysis + preference pair. Stdlib unittest."""
import json
import os
import unittest

from src.compare import (active_selection, disagrees, duplicate_rate,
                         failure_modes, quality_distribution,
                         verdict_distribution)
from src.multiteacher import make_pair, select_sft_messages

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rec(teacher, verdict, sha, failed=()):
    return {"teacher": teacher, "verdict": verdict, "artifact_sha256": sha,
            "checks": {"functional": [{"name": n, "passed": False} for n in failed]}}


class TestCompare(unittest.TestCase):
    def test_verdict_distribution(self):
        rs = [_rec("a", "GOLD", "s1"), _rec("b", "SILVER", "s2"), _rec("c", "FAIL", "s3")]
        self.assertEqual(verdict_distribution(rs), {"GOLD": 1, "SILVER": 1, "FAIL": 1})

    def test_duplicate_rate(self):
        self.assertEqual(duplicate_rate([_rec("a", "GOLD", "s"), _rec("b", "GOLD", "s")]), 0.5)
        self.assertEqual(duplicate_rate([_rec("a", "GOLD", "s1"), _rec("b", "GOLD", "s2")]), 0.0)

    def test_failure_modes_counts_real_names(self):
        rs = [_rec("b", "SILVER", "s2", ["viewport_375"]), _rec("c", "FAIL", "s3", ["has_title", "viewport_375"])]
        fm = failure_modes(rs)
        self.assertEqual(fm["viewport_375"], 2)
        self.assertEqual(fm["has_title"], 1)

    def test_disagreement_and_active_selection(self):
        rs = [_rec("gold-t", "GOLD", "s1"), _rec("sil-t", "SILVER", "s2"), _rec("fail-t", "FAIL", "s3")]
        self.assertTrue(disagrees(rs))
        self.assertFalse(disagrees([_rec("a", "GOLD", "s1"), _rec("b", "GOLD", "s2")]))
        self.assertEqual(active_selection(rs), ["sil-t", "fail-t", "gold-t"])

    def test_make_pair_chosen_beats_rejected(self):
        rs = [_rec("gold-t", "GOLD", "s1"), _rec("fail-t", "FAIL", "s3")]
        pair = make_pair(rs, "t", "p")
        self.assertEqual(pair["chosen"]["verdict"], "GOLD")
        self.assertEqual(pair["rejected"]["verdict"], "FAIL")
        self.assertIsNone(make_pair([_rec("a", "GOLD", "s1")], "t", "p"))

    def test_sft_selection_skips_size_aside(self):
        traj = {"messages": [
            {"role": "assistant", "content": "2717 bytes, well under 15KB. Done."},
            {"role": "assistant", "content": "2717 bytes, well under 15KB. Done.\nDone. Real summary here."}]}
        msgs = select_sft_messages("prompt", traj)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertNotIn("2717 bytes", msgs[1]["content"])
        self.assertIn("Real summary", msgs[1]["content"])

    def test_preference_schema_shape(self):
        with open(os.path.join(_HERE, "schemas", "preference.v1.json"), encoding="utf-8") as f:
            schema = json.load(f)
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")
        self.assertIn("chosen", schema["required"])
        self.assertIn("rejected", schema["required"])


if __name__ == "__main__":
    unittest.main()
