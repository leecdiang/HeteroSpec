"""New weak SEARCH_ALIAS coverage using retained, real e04-v4 link evidence.

The full retained trace is expected to REFUSE its separate demangling ambiguity.
No compiler, linker, executable, DLL loader, model or GPU is invoked.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
FRONTEND = HERE.parent
RUN = FRONTEND / "run-v4"
spec = importlib.util.spec_from_file_location("e04_link_witness_v2", FRONTEND / "link_witness_v2.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def alias_object(alias="__set_app_type", target="_set_app_type", tag=0,
                 search=3, target_storage=2):
    strings = target.encode() + b"\0" + alias.encode() + b"\0"
    target_name = b"\0" * 4 + struct.pack("<I", 4)
    alias_name = b"\0" * 4 + struct.pack("<I", 5 + len(target))
    header = struct.pack("<HHIIIHH", 0x8664, 0, 0, 20, 3, 0, 0)
    target_record = target_name + struct.pack("<IhHBB", 0, 0, 0, target_storage, 0)
    alias_record = alias_name + struct.pack("<IhHBB", 0, 0, 0, 105, 1)
    auxiliary = struct.pack("<II", tag, search) + b"\0" * 10
    return header + target_record + alias_record + auxiliary + struct.pack("<I", 4 + len(strings)) + strings


def ar_record(name, data):
    header = (name.encode().ljust(16) + b"0".ljust(12) + b"0".ljust(6)
              + b"0".ljust(6) + b"100644".ljust(8)
              + str(len(data)).encode().ljust(10) + b"`\n")
    return header + data + (b"\n" if len(data) & 1 else b"")


class WeakAliasWitness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads((RUN / "RECIPE.json").read_bytes())
        cls.archive_paths = cls.recipe["cores"]["loop4"]["archives"]
        path = next(p for p in cls.archive_paths if p.endswith("api-ms-win-crt-runtime-l1-1-0.lib"))
        cls.archive = w.Archive(path)
        cls.trace = ((RUN / "loop4-link.stdout.log").read_text(encoding="utf8")
                     + (RUN / "loop4-link.stderr.log").read_text(encoding="utf8"))
        cls.map_text = (RUN / "build/loop4/worker.map").read_text(encoding="utf8")

    def test_real_loaded_alias_selects_exact_auxiliary_member(self):
        # This is a genuine single-line excerpt, not a complete-link receipt.
        lines = [line for line in self.trace.splitlines()
                 if re.search(r"Loaded api-ms-win-crt-runtime-l1-1-0.lib\(.+\) for __set_app_type$", line)]
        self.assertEqual(len(lines), 1)
        result = w.analyze_link_inputs(lines[0], [self.archive.path])
        entry = result["selected_members"][0]
        self.assertEqual(entry["header_offset"], 24392)
        self.assertEqual(entry["bytes"], 183)
        payload = self.archive.member_data(next(m for m in self.archive.members if m["header_offset"] == 24392))
        self.assertEqual(entry["member_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(w.defined_symbols(payload), {"__set_app_type"})
        self.assertEqual(entry["trigger_symbols"], ["__set_app_type"])

    def test_real_alias_import_and_strong_import_are_distinct_bytes(self):
        alias = self.archive.select("api-ms-win-crt-runtime-l1-1-0.dll", "__imp___set_app_type")
        strong = self.archive.select("api-ms-win-crt-runtime-l1-1-0.dll", "_set_app_type")
        self.assertEqual(alias["header_offset"], 24636)
        self.assertEqual(strong["header_offset"], 19098)
        self.assertNotEqual(alias["member_sha256"], strong["member_sha256"])

    def test_search_alias_target_must_be_existing_primary_external(self):
        self.assertEqual(w.defined_symbols(alias_object()), {"__set_app_type"})
        for kwargs in ({"tag": 999}, {"tag": 1}, {"tag": 2}, {"target_storage": 3}):
            with self.subTest(kwargs=kwargs), self.assertRaises(w.WitnessError):
                w.defined_symbols(alias_object(**kwargs))

    def test_non_alias_weak_search_policy_not_admitted_as_resolution(self):
        for search in (0, 1, 2, 4, 999):
            self.assertEqual(w.defined_symbols(alias_object(search=search)), set())

    def test_differing_duplicate_alias_payloads_still_refused(self):
        with tempfile.TemporaryDirectory(prefix="weak-alias-", dir=HERE) as folder:
            path = Path(folder) / "ambiguous.lib"
            data = b"!<arch>\n" + ar_record("same.obj/", alias_object())
            data += ar_record("same.obj/", alias_object(target="other_target"))
            path.write_bytes(data)
            with self.assertRaisesRegex(w.WitnessError, "Ambiguous same-name"):
                w.analyze_link_inputs(f"Loaded {path}(same.obj) for __set_app_type", [path])

    def test_truncated_or_wrong_auxiliary_not_accepted(self):
        malformed = bytearray(alias_object())
        malformed[20 + 18 + 17] = 0
        with self.assertRaises(w.WitnessError):
            w.defined_symbols(bytes(malformed))
        with self.assertRaises(w.WitnessError):
            w.defined_symbols(alias_object()[:60])

    def test_complete_real_trace_keeps_separate_demangling_refusal(self):
        with self.assertRaisesRegex(w.WitnessError, r"libllama.a\(llama.cpp.obj\).*vtable for llama_model_llama"):
            w.analyze_link_inputs(self.trace, self.archive_paths, map_text=self.map_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
