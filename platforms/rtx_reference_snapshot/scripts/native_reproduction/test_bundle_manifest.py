import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import bundle_manifest as bm


class BundleManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "stage"
        self.root.mkdir()
        (self.root / "fixture.bin").write_bytes(b"\x00\xff\r\nexact\x00bytes")
        (self.root / "build.txt").write_text("build recipe\n")
        self.manifest = self.root / "manifest.json"

    def make(self):
        bm.create(self.root, ["fixture.bin", "build.txt"], "rtx", self.manifest)
        return bm.read_json(self.manifest)

    def test_fresh_copy_and_partial_identity(self):
        m = self.make()
        copied = Path(self.tmp.name) / "fresh"
        shutil.copytree(self.root, copied)
        result = bm.verify(copied, bm.read_json(copied / "manifest.json"))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["native_qualification"], "NOT_ASSESSED")
        self.assertEqual(m["identity_completeness"]["status"], "PARTIAL")
        self.assertEqual([x["path"] for x in m["files"]], ["build.txt", "fixture.bin"])

    def test_same_size_tamper(self):
        m = self.make()
        p = self.root / "fixture.bin"
        p.write_bytes(p.read_bytes().replace(b"exact", b"other"))
        r = bm.verify(self.root, m)
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual([x["path"] for x in r["changed"]], ["fixture.bin"])

    def test_missing(self):
        m = self.make()
        (self.root / "build.txt").unlink()
        self.assertEqual(bm.verify(self.root, m)["missing"], ["build.txt"])

    def test_existing_manifest_never_overwritten(self):
        self.make()
        old = self.manifest.read_bytes()
        with self.assertRaises(FileExistsError):
            bm.create(self.root, ["fixture.bin"], "b570", self.manifest)
        self.assertEqual(self.manifest.read_bytes(), old)

    def test_path_escape_and_absolute_rejected(self):
        for path in ("../fixture.bin", "/tmp/file", "C:\\secret\\file", "C:relative", "."):
            with self.subTest(path=path), self.assertRaises(ValueError):
                bm.resolve_file(self.root, path)

    def test_external_symlink_rejected_during_create_and_verify(self):
        outside = Path(self.tmp.name) / "outside.bin"
        outside.write_bytes(b"outside")
        link = self.root / "external.bin"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation unavailable on this host")
        with self.assertRaises(ValueError):
            bm.create(self.root, ["external.bin"], "rtx", self.manifest)
        m = self.make()
        (self.root / "fixture.bin").unlink()
        (self.root / "fixture.bin").symlink_to(outside)
        with self.assertRaises(ValueError):
            bm.verify(self.root, m)

    def test_duplicate_and_invalid_manifest_rejected(self):
        m = self.make()
        m["files"].append(m["files"][0].copy())
        with self.assertRaises(ValueError):
            bm.verify(self.root, m)
        with self.assertRaises(ValueError):
            bm.verify(self.root, {"schema": 1, "platform": "rtx", "files": []})

    def test_cli_failure_exit_and_no_write(self):
        self.make()
        (self.root / "fixture.bin").unlink()
        original = self.manifest.read_bytes()
        result = subprocess.run([sys.executable, str(Path(bm.__file__)), "verify",
                                 "--root", str(self.root), "--manifest", str(self.manifest)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["missing"], ["fixture.bin"])
        self.assertEqual(self.manifest.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
