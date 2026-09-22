"""Shot 2 replay test: same input -> identical bytes/hash; JSONL round-trip stable."""
import os
import unittest

from src.capture import canonical, load_export_file, normalize, sha256
from src.validate import validate_trajectory

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "fixtures", "opencode-export.fixture.json")
KW = dict(opencode_version="1.18.32", captured_at="2026-09-22T00:00:00+00:00")


class TestReplay(unittest.TestCase):
    def test_replay_identical_bytes(self):
        first = canonical(normalize(load_export_file(FIXTURE), **KW)[0])
        for _ in range(3):
            rep = canonical(normalize(load_export_file(FIXTURE), **KW)[0])
            self.assertEqual(rep, first)
        print(f"\nreplay sha256: {sha256(first)} bytes: {len(first)}")

    def test_jsonl_roundtrip_stable(self):
        traj = normalize(load_export_file(FIXTURE), **KW)[0]
        line = canonical(traj).decode()
        import json
        back = json.loads(line)  # one trajectory per line
        self.assertTrue(validate_trajectory(back))
        self.assertEqual(canonical(back), canonical(traj))


if __name__ == "__main__":
    unittest.main()
