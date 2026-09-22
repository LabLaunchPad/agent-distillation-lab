"""Shot 2 unit+integration tests. Stdlib unittest only."""
import json
import os
import sqlite3
import unittest

from src.capture import (canonical, load_export_file, normalize, probe,
                         scan_residual, sha256, to_artifact)
from src.validate import (validate_artifact, validate_provenance,
                          validate_trajectory)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURE = os.path.join(ROOT, "fixtures", "opencode-export.fixture.json")


def fixture_record():
    return load_export_file(FIXTURE)


class TestProbe(unittest.TestCase):
    def test_probe_real_surface(self):
        p = probe()
        self.assertIn("opencode_version", p)
        self.assertIn("db_path", p)
        # real binary present in this env; sanitize flag must exist
        self.assertTrue(p.get("export_sanitize"), f"probe: {p}")


class TestNormalize(unittest.TestCase):
    def test_fixture_normalizes_and_validates(self):
        traj, prov, errors = normalize(fixture_record(), opencode_version="1.18.32",
                                       captured_at="2026-09-22T00:00:00+00:00")
        self.assertTrue(validate_trajectory(traj))
        self.assertTrue(validate_provenance(prov))
        self.assertEqual(traj["session_id"], "ses_fixture001")
        self.assertEqual(traj["provider"], "opencode")
        self.assertEqual(len(traj["messages"]), 2)
        names = [c["name"] for c in traj["tool_calls"]]
        self.assertIn("write", names)
        self.assertIn("bash", names)
        self.assertIn("patch", names)  # file changes surfaced
        self.assertTrue(errors)  # bash error + captured

    def test_redaction_before_write(self):
        traj, _, _ = normalize(fixture_record(), captured_at="2026-09-22T00:00:00+00:00")
        blob = canonical(traj).decode()
        self.assertNotIn("sk-abc123XYZ", blob)
        self.assertNotIn("a@b.com", blob)
        self.assertIn("[REDACTED_API_KEY]", blob)
        self.assertEqual(scan_residual(blob), 0)

    def test_residual_scanner_catches_raw_secrets(self):
        self.assertGreater(scan_residual("key sk-abc123XYZ q"), 0)
        self.assertEqual(scan_residual("[REDACTED_API_KEY]"), 0)

    def test_determinism(self):
        kw = dict(opencode_version="1.18.32", captured_at="2026-09-22T00:00:00+00:00")
        a = canonical(normalize(fixture_record(), **kw)[0])
        b = canonical(normalize(fixture_record(), **kw)[0])
        self.assertEqual(a, b)
        self.assertEqual(sha256(a), sha256(b))

    def test_artifact(self):
        art = to_artifact("ses_fixture001", "patch", "diff --git x.py")
        self.assertTrue(validate_artifact(art))
        self.assertEqual(len(art["sha256"]), 64)


class TestLiveDbReadOnly(unittest.TestCase):
    def test_real_db_readable_without_write(self):
        p = probe()
        db = p.get("db_path", "")
        if not db or not os.path.exists(db):
            self.skipTest(f"no live opencode.db ({db})")
        con = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
        try:
            n = con.execute("SELECT COUNT(*) FROM session").fetchone()[0]
            self.assertGreater(n, 0)
            sid = con.execute("SELECT id FROM session ORDER BY rowid DESC LIMIT 1").fetchone()[0]
        finally:
            con.close()
        from src.capture import load_session
        rec = load_session(db, sid)
        traj, prov, _ = normalize(rec, captured_at="2026-09-22T00:00:00+00:00")
        self.assertTrue(validate_trajectory(traj))
        self.assertTrue(validate_provenance(prov))


if __name__ == "__main__":
    unittest.main()
