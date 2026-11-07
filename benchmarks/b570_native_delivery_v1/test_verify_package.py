"""CPU-only rejection tests for delivery integrity and output isolation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_package as verifier


def encoded(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def row(name, payload, origin=None):
    result = {"path": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    if origin:
        result["origin_member"] = origin
    return result


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "package"
        self.root.mkdir()
        original_payloads = {"references/qual-2/result.json": b"original evidence\n",
                             "kit/audit_request.py": b"# pinned CPU auditor\n",
                             "kit/INPUT_PANEL.json": b"[]\n"}
        original = {"schema": 1, "platform": "b570", "files": [row(k, v) for k, v in original_payloads.items()]}
        original_bytes = encoded(original)
        original_sha = hashlib.sha256(original_bytes).hexdigest()
        self.source_pin = patch.object(verifier, "SOURCE_MANIFEST_SHA256", original_sha)
        self.source_pin.start()
        self.addCleanup(self.source_pin.stop)
        payloads = dict(original_payloads)
        payloads["provenance/ORIGINAL_MANIFEST.json"] = original_bytes
        payloads["provenance/SOURCE_ARCHIVE.json"] = encoded({
            "archive_sha256": verifier.SOURCE_ARCHIVE_SHA256,
            "archive_bytes": verifier.SOURCE_ARCHIVE_BYTES})
        payloads["delivery/README.md"] = b"new documentation\n"
        for name, payload in payloads.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        self.manifest = {"schema": 1, "platform": "b570", "package_kind": "four_input_references",
                         "source_archive_sha256": verifier.SOURCE_ARCHIVE_SHA256,
                         "source_manifest_sha256": original_sha,
                         "files": [row(k, v, k if k in original_payloads else None) for k, v in payloads.items()]}
        self.save()

    def save(self):
        (self.root / "manifest.json").write_bytes(encoded(self.manifest))

    def rejected(self, text):
        with self.assertRaisesRegex(ValueError, text):
            verifier.verify_integrity(self.root)

    def test_valid_inventory(self):
        result = verifier.verify_integrity(self.root)
        self.assertEqual(result["verified_files"], 6)
        self.assertEqual(result["verified_original_members"], 3)

    def test_same_size_tampering(self):
        target = self.root / "references/qual-2/result.json"
        target.write_bytes(b"X" + target.read_bytes()[1:])
        self.rejected("integrity mismatch")

    def test_missing_and_extra_members(self):
        target = self.root / "delivery/README.md"
        content = target.read_bytes()
        target.unlink()
        self.rejected("missing=.*delivery/README")
        target.write_bytes(content)
        (self.root / "unlisted.bin").write_bytes(b"unlisted")
        self.rejected("extra=.*unlisted")

    def test_duplicate_and_case_alias_rows(self):
        self.manifest["files"].append(dict(self.manifest["files"][0]))
        self.save()
        self.rejected("Duplicate/aliased")
        self.manifest["files"][-1]["path"] = self.manifest["files"][0]["path"].upper()
        self.save()
        self.rejected("Duplicate/aliased")

    def test_unsafe_paths(self):
        for path in (".", "../outside.bin", "/absolute.bin", "C:/outside.bin", "foo\\bar", "a//b", "a/./b"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    verifier.portable_path(path)

    def test_modified_origin_with_updated_outer_hash_is_rejected(self):
        target = self.root / "references/qual-2/result.json"
        target.write_bytes(b"changed and rehashed\n")
        self.manifest["files"][0] = row("references/qual-2/result.json", target.read_bytes(), "references/qual-2/result.json")
        self.save()
        self.rejected("Original member identity mismatch")

    def test_removed_origin_binding_is_rejected(self):
        del self.manifest["files"][0]["origin_member"]
        self.save()
        self.rejected("lacks provenance")

    def test_rewritten_original_manifest_is_rejected(self):
        target = self.root / "provenance/ORIGINAL_MANIFEST.json"
        changed = target.read_bytes() + b" "
        target.write_bytes(changed)
        for index, item in enumerate(self.manifest["files"]):
            if item["path"] == "provenance/ORIGINAL_MANIFEST.json":
                self.manifest["files"][index] = row(item["path"], changed)
        self.manifest["source_manifest_sha256"] = hashlib.sha256(changed).hexdigest()
        self.save()
        self.rejected("Wrong original manifest")

    def test_duplicate_json_key_is_rejected(self):
        (self.root / "manifest.json").write_text('{"schema":1,"schema":1}', encoding="utf-8")
        self.rejected("Duplicate JSON key")

    def test_output_must_be_new_and_external(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            verifier.verify_package(self.root, self.root / "new-audit")
        self.assertFalse((self.root / "new-audit").exists())
        existing = Path(self.temp.name) / "already"
        existing.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            verifier.verify_package(self.root, existing)


if __name__ == "__main__":
    unittest.main()
