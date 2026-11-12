import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e04_link_witness", ROOT / "link_witness.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def ar_record(name, payload):
    header = (name.encode().ljust(16) + b"0".ljust(12) + b"0".ljust(6) +
              b"0".ljust(6) + b"100644".ljust(8) + str(len(payload)).encode().ljust(10) + b"`\n")
    if len(header) != 60:
        raise ValueError("test archive name too long")
    return header + payload + (b"\n" if len(payload) & 1 else b"")


def archive(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"!<arch>\n" + b"".join(ar_record(n, d) for n, d in records))
    return path


def short_import(symbol, dll="KERNEL32.dll"):
    body = symbol.encode() + b"\0" + dll.encode() + b"\0"
    return struct.pack("<HHHHIIHH", 0, 0xFFFF, 0, 0x8664, 0, len(body), 0, 4) + body


def coff(symbol, big=False):
    name = symbol.encode()
    long = len(name) > 8
    encoded = b"\0" * 4 + struct.pack("<I", 4) if long else name.ljust(8, b"\0")
    strings = struct.pack("<I", 4 + (len(name) + 1 if long else 0)) + (name + b"\0" if long else b"")
    if big:
        header = struct.pack("<HHHHI", 0, 0xFFFF, 2, 0x8664, 0) + b"\0" * 16 + struct.pack("<IIIIIII", 0, 0, 0, 0, 1, 56, 1)
        symbol_data = encoded + struct.pack("<IiHBB", 0, 1, 0, 2, 0)
    else:
        header = struct.pack("<HHIIIHH", 0x8664, 1, 0, 20, 1, 0, 0)
        symbol_data = encoded + struct.pack("<IhHBB", 0, 1, 0, 2, 0)
    return header + symbol_data + strings


class LinkWitness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_actual_container_and_selected_member_hashes(self):
        p = archive(self.dir / "a.lib", [("used.obj/", b"used\0"), ("unused.obj/", b"unused")])
        result = module.analyze_link_inputs(f"lld-link: Loaded {p}(used.obj) for symbol wanted", [p])
        self.assertEqual(result["selected_member_count"], 1)
        self.assertEqual(result["archives"][0]["sha256"], hashlib.sha256(p.read_bytes()).hexdigest())
        self.assertEqual(result["selected_members"][0]["member_sha256"], hashlib.sha256(b"used\0").hexdigest())
        self.assertEqual(result["selected_members"][0]["trigger_symbols"], ["wanted"])

    def test_gnu_coff_and_bsd_long_names(self):
        gnu = "folder/a_very_long_member.obj"
        coff_name = "another_long_member.obj"
        bsd = b"bsd_long_member_name.obj"
        table = gnu.encode() + b"/\n" + coff_name.encode() + b"\0"
        offset = len(gnu) + 2
        p = archive(self.dir / "long.a", [("//", table), ("/0", b"one"),
                      ("/" + str(offset), b"two"), ("#1/" + str(len(bsd)), bsd + b"three")])
        trace = "\n".join(f"lld-link: Loaded {p}({name}) for x" for name in (gnu, coff_name, bsd.decode()))
        result = module.analyze_link_inputs(trace, [p])
        self.assertEqual({e["member_name"] for e in result["selected_members"]}, {gnu, coff_name, bsd.decode()})

    def test_short_import_duplicate_names_disambiguated_by_symbol(self):
        p = archive(self.dir / "kernel32.lib", [("KERNEL32.dll/", short_import("GetLastError")),
                                                ("KERNEL32.dll/", short_import("CloseHandle"))])
        result = module.analyze_link_inputs(f"lld-link: Loaded {p}(KERNEL32.dll) for __imp_CloseHandle", [p])
        chosen = result["selected_members"][0]
        self.assertEqual(chosen["member_sha256"], hashlib.sha256(short_import("CloseHandle")).hexdigest())

    def test_standard_coff_and_bigobj_symbols_disambiguate(self):
        p = archive(self.dir / "symbols.a", [("same.obj/", coff("very_long_symbol_name")),
                                               ("same.obj/", coff("other_long_symbol_name", big=True))])
        result = module.analyze_link_inputs(f"Loaded {p}(same.obj) for other_long_symbol_name", [p])
        self.assertEqual(result["selected_members"][0]["member_sha256"], hashlib.sha256(coff("other_long_symbol_name", big=True)).hexdigest())

    def test_different_ambiguous_member_bytes_refuse(self):
        p = archive(self.dir / "ambiguous.a", [("same.obj/", b"one"), ("same.obj/", b"two")])
        with self.assertRaisesRegex(module.WitnessError, "Ambiguous"):
            module.analyze_link_inputs(f"Loaded {p}(same.obj) for no_definition", [p])

    def test_identical_duplicate_bytes_report_all_equivalent_offsets(self):
        p = archive(self.dir / "identical.a", [("same.obj/", b"same"), ("same.obj/", b"same")])
        result = module.analyze_link_inputs(f"Loaded {p}(same.obj) for x", [p])
        self.assertEqual(len(result["selected_members"][0]["equivalent_candidate_offsets"]), 2)

    def test_unknown_absolute_archive_does_not_fallback_to_basename(self):
        p = archive(self.dir / "known.lib", [("one.obj/", b"one")])
        fake = self.dir / "other" / "known.lib"
        with self.assertRaisesRegex(module.WitnessError, "Unknown traced absolute"):
            module.analyze_link_inputs(f"Loaded {fake}(one.obj) for x", [p])

    def test_bare_ambiguous_archive_name_refuses(self):
        a = archive(self.dir / "a" / "same.lib", [("one.obj/", b"a")])
        b = archive(self.dir / "b" / "same.lib", [("one.obj/", b"b")])
        with self.assertRaisesRegex(module.WitnessError, "ambiguous"):
            module.analyze_link_inputs("Loaded same.lib(one.obj) for x", [a, b])

    def test_missing_trace_missing_member_and_unsupported_format_refuse(self):
        p = archive(self.dir / "a.lib", [("one.obj/", b"one")])
        for trace in ("lld-link: Reading a.lib", f"Loaded {p}(missing.obj) for x", f"Loaded {p} for x", f"Loaded {p}(one.obj)"):
            with self.assertRaises(module.WitnessError):
                module.analyze_link_inputs(trace, [p])

    def test_truncated_archive_and_bad_symbol_table_refuse(self):
        p = self.dir / "bad.a";p.write_bytes(b"!<arch>\ntruncated")
        with self.assertRaisesRegex(module.WitnessError, "Truncated"):
            module.Archive(p)
        malformed = struct.pack("<HHIIIHH", 0x8664, 1, 0, 10000, 500, 0, 0)
        p = archive(self.dir / "bad-symbols.a", [("same.obj/", malformed), ("same.obj/", b"other")])
        with self.assertRaisesRegex(module.WitnessError, "symbol table"):
            module.analyze_link_inputs(f"Loaded {p}(same.obj) for wanted", [p])

    def test_reading_import_members_resolve_with_actual_map_symbols(self):
        p = archive(self.dir / "kernel32.lib", [("KERNEL32.dll/", short_import("GetLastError")),
                                                ("KERNEL32.dll/", short_import("CloseHandle"))])
        trace = f"lld-link: Reading {p}(KERNEL32.dll)\nlld-link: Reading {p}(KERNEL32.dll)\n"
        map_text = " 0002:00000000 __imp_GetLastError 0000000140002000 kernel32:KERNEL32.dll\n 0002:00000008 __imp_CloseHandle 0000000140002008 kernel32:KERNEL32.dll\n"
        result = module.analyze_link_inputs(trace, [p], map_text=map_text)
        self.assertEqual(result["selected_member_count"], 2)
        self.assertEqual(result["reading_member_lines"], 2)
        self.assertEqual(result["reading_groups"][0]["distinct_payloads"], 2)
        with self.assertRaisesRegex(module.WitnessError, "occurrence mismatch"):
            module.analyze_link_inputs(trace, [p], map_text=map_text.splitlines()[0])

    def test_map_without_actual_extraction_trace_and_unfrozen_map_refuse(self):
        p = archive(self.dir / "one.lib", [("one.obj/", coff("one"))])
        map_text = " 0001:00000000 one 0000000140001000 one:one.obj\n"
        with self.assertRaisesRegex(module.WitnessError, "No recognized"):
            module.analyze_link_inputs("", [p], map_text=map_text)
        with self.assertRaisesRegex(module.WitnessError, "unfrozen archive"):
            module.analyze_link_inputs(f"Loaded {p}(one.obj) for one", [p], map_text=map_text.replace("one:one.obj", "unknown:other.obj"))

    def test_quoted_archive_paths_with_spaces(self):
        p = archive(self.dir / "directory with spaces" / "space.lib", [("one.obj/", b"one")])
        result = module.analyze_link_inputs(f'lld-link: Reading "{p}(one.obj)"\nlld-link: Loaded "{p}(one.obj)" for chosen', [p])
        self.assertEqual(result["selected_member_count"], 1)


if __name__ == "__main__":
    unittest.main()
