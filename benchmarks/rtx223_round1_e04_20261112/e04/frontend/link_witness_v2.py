"""Bind LLD COFF archive extraction traces to exact container/member bytes.

Reads only. This records linker archive extraction, not execution, numerical
qualification, or all filesystem reads made by the linker. Use alongside the
pre-build dependency freeze and the exact linker command/default-library policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Iterable


class WitnessError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise WitnessError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm_name(name: str) -> str:
    return name.replace("\\", "/").casefold()


def basename(name: str) -> str:
    return norm_name(name).rsplit("/", 1)[-1]


def _cstring(data: bytes, offset: int, limit: int | None = None) -> str:
    end_limit = len(data) if limit is None else min(len(data), limit)
    require(0 <= offset < end_limit, "COFF string offset outside payload")
    end = data.find(b"\0", offset, end_limit)
    require(end != -1, "Unterminated COFF string")
    return data[offset:end].decode("utf8", errors="strict")


def defined_symbols(data: bytes) -> set[str]:
    """Definitions usable to disambiguate duplicate COFF import member names.

    Supports standard COFF, BigObj, short import objects, and validated COFF
    weak-external SEARCH_ALIAS records. The latter are archive resolution symbols,
    not definitions of callable code. Unrecognized
    formats yield no symbols and cannot disambiguate different member bytes.
    """
    if len(data) < 20:
        return set()
    sig1, sig2, version, machine = struct.unpack_from("<HHHH", data)
    if sig1 == 0 and sig2 == 0xFFFF and version == 0:
        size = struct.unpack_from("<I", data, 12)[0]
        require(20 <= len(data) and size <= len(data) - 20,
                "Truncated short import object")
        symbol = _cstring(data, 20, 20 + size)
        return {symbol, "__imp_" + symbol}
    if sig1 == 0 and sig2 == 0xFFFF and version >= 2:
        if len(data) < 56:
            return set()
        pointer, count = struct.unpack_from("<II", data, 48)
        width, section_size, storage_offset, aux_offset = 20, 4, 18, 19
    else:
        machine = sig1
        if machine not in (0x14C, 0x8664, 0xAA64, 0x1C4):
            return set()
        pointer, count = struct.unpack_from("<II", data, 8)
        width, section_size, storage_offset, aux_offset = 18, 2, 16, 17
    if pointer == 0 or count == 0:
        return set()
    require(count <= (len(data) - pointer) // width and pointer <= len(data),
            "COFF symbol table outside member")
    string_start = pointer + count * width
    if string_start + 4 <= len(data):
        string_size = struct.unpack_from("<I", data, string_start)[0]
        require(4 <= string_size <= len(data) - string_start,
                "COFF string table outside member")
    else:
        string_size = 0
    result: set[str] = set()
    records = {}
    i = 0
    while i < count:
        offset = pointer + i * width
        if data[offset:offset + 4] == b"\0\0\0\0":
            string_offset = struct.unpack_from("<I", data, offset + 4)[0]
            require(string_size and 4 <= string_offset < string_size,
                    "COFF symbol long-name offset invalid")
            name = _cstring(data, string_start + string_offset,
                            string_start + string_size)
        else:
            name = data[offset:offset + 8].split(b"\0", 1)[0].decode("utf8")
        section = int.from_bytes(data[offset + 12:offset + 12 + section_size],
                                 "little", signed=True)
        storage = data[offset + storage_offset]
        auxiliary = data[offset + aux_offset]
        require(i + auxiliary < count, "COFF auxiliary symbol count invalid")
        records[i] = {"name": name, "section": section, "storage": storage,
                      "auxiliary": auxiliary, "offset": offset}
        if storage == 2 and (section > 0 or section == -1):
            result.add(name)
        i += 1 + auxiliary
    # Import libraries also contain zero-code weak-alias objects. Their symbol
    # table advertises the alias to the archive index, while the actual import
    # lives in another same-name member. Bind that exact alias object only when
    # the single auxiliary record says SEARCH_ALIAS (3) and its TagIndex names
    # an admitted external primary symbol in this exact member.
    for index, record in records.items():
        if record["storage"] != 105:
            continue
        require(record["auxiliary"] == 1 and record["section"] == 0,
                "Unsupported/malformed COFF weak external record")
        target, search = struct.unpack_from("<II", data, record["offset"] + width)
        if search != 3:
            continue  # Other weak-search policies do not prove alias resolution.
        require(target in records and target != index,
                "COFF weak alias target is not another primary symbol")
        target_record = records[target]
        require(target_record["storage"] == 2 and bool(target_record["name"])
                and target_record["name"] != record["name"],
                "COFF weak alias target is not a distinct ordinary external symbol")
        result.add(record["name"])
    return result


class Archive:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve(strict=True)
        self.data = self.path.read_bytes()
        require(self.data[:8] == b"!<arch>\n",
                "Only complete ar/COFF archives supported: " + str(self.path))
        self.sha256 = sha256(self.data)
        records = []
        offset = 8
        while offset < len(self.data):
            require(offset + 60 <= len(self.data), "Truncated archive header")
            header = self.data[offset:offset + 60]
            require(header[58:60] == b"`\n", "Bad archive member trailer")
            raw_name = header[:16].decode("ascii").rstrip(" ")
            length_text = header[48:58].decode("ascii").strip()
            require(bool(re.fullmatch(r"\d+", length_text)),
                    "Invalid archive member length")
            length = int(length_text)
            start = offset + 60
            require(length <= len(self.data) - start, "Truncated archive member")
            records.append({"raw_name": raw_name, "header_offset": offset,
                            "data_offset": start, "bytes": length})
            offset = start + length
            if offset & 1:
                require(offset < len(self.data), "Missing archive alignment byte")
                offset += 1
        require(offset == len(self.data), "Archive trailing bytes")
        long_tables = [r for r in records if r["raw_name"] == "//"]
        require(len(long_tables) <= 1, "Multiple archive long-name tables")
        long_data = b""
        if long_tables:
            table = long_tables[0]
            long_data = self.data[table["data_offset"]:
                                  table["data_offset"] + table["bytes"]]
        members = []
        for record in records:
            member = dict(record)
            raw_name = member.pop("raw_name")
            if raw_name in ("/", "//", "/SYM64/"):
                continue
            if raw_name.startswith("#1/"):
                amount_text = raw_name[3:]
                require(amount_text.isdigit(), "Invalid BSD archive extended name")
                amount = int(amount_text)
                require(amount <= member["bytes"], "Truncated BSD archive name")
                start = member["data_offset"]
                name = self.data[start:start + amount].rstrip(b"\0").decode("utf8")
                member["data_offset"] += amount
                member["bytes"] -= amount
            elif raw_name.startswith("/") and raw_name[1:].isdigit():
                start = int(raw_name[1:])
                require(start < len(long_data), "Archive long-name offset invalid")
                zero = long_data.find(b"\0", start)
                slash = long_data.find(b"/\n", start)
                ends = [i for i in (zero, slash) if i >= start]
                require(bool(ends), "Unterminated archive long name")
                name = long_data[start:min(ends)].decode("utf8")
            else:
                name = raw_name[:-1] if raw_name.endswith("/") else raw_name
            require(bool(name), "Empty archive member name")
            member["name"] = name
            members.append(member)
        self.members = members
        self._symbol_cache = {}

    def member_data(self, member: dict) -> bytes:
        start = member["data_offset"]
        return self.data[start:start + member["bytes"]]

    def resolution_symbols(self, member: dict) -> set[str]:
        key = member["header_offset"]
        if key not in self._symbol_cache:
            self._symbol_cache[key] = defined_symbols(self.member_data(member))
        return self._symbol_cache[key]

    def select(self, name: str, symbol: str) -> dict:
        candidates = [m for m in self.members if norm_name(m["name"]) == norm_name(name)]
        if not candidates:
            candidates = [m for m in self.members if basename(m["name"]) == basename(name)]
        require(bool(candidates), "Trace member absent from archive: " + name)
        if len(candidates) > 1:
            matching = [m for m in candidates
                        if symbol in self.resolution_symbols(m)]
            if matching:
                candidates = matching
        hashes = {sha256(self.member_data(m)) for m in candidates}
        require(len(hashes) == 1,
                "Ambiguous same-name members with differing bytes: " + str(self.path) + "(" + name + ") for " + symbol)
        chosen = min(candidates, key=lambda m: m["header_offset"])
        return {"archive_path": str(self.path), "archive_sha256": self.sha256,
                "member_name": chosen["name"],
                "header_offset": chosen["header_offset"],
                "data_offset": chosen["data_offset"], "bytes": chosen["bytes"],
                "member_sha256": sha256(self.member_data(chosen)),
                "equivalent_candidate_offsets": sorted(m["header_offset"] for m in candidates),
                "selection_basis": "exact member name, unique bytes or COFF definition/import/validated weak SEARCH_ALIAS resolution symbol"}


def _resolve_archive(reference: str, archives: list[Archive]) -> Archive:
    reference = reference.strip().strip('"')
    exact = [a for a in archives if norm_name(str(a.path)) == norm_name(reference)]
    if exact:
        require(len(exact) == 1, "Duplicate archive path input")
        return exact[0]
    normalized = norm_name(reference)
    require(not re.match(r"^(?:[a-z]:/|/)", normalized),
            "Unknown traced absolute archive path: " + reference)
    # LLD sometimes prints the basename even when the command passed full paths.
    matches = [a for a in archives if
               (norm_name(str(a.path)).endswith("/" + normalized) if "/" in normalized
                else basename(str(a.path)) == basename(reference))]
    require(len(matches) == 1,
            "Unknown or ambiguous traced archive path: " + reference)
    return matches[0]


def _member_reference(reference: str):
    return re.fullmatch(r"(.+\.(?:a|lib))\((.+)\)", reference.strip().strip('"'), re.IGNORECASE)


def _map_reference(reference: str, archives: list[Archive]):
    text = reference.strip()
    while re.match(r"^[fi]\s+", text):
        text = text.split(None, 1)[1]
    found = []
    for archive in archives:
        prefixes = {str(archive.path), str(archive.path.with_suffix("")),
                    archive.path.name, archive.path.stem}
        if archive.path.stem.startswith("lib"):
            prefixes.add(archive.path.stem[3:])
        for prefix in prefixes:
            if norm_name(text).startswith(norm_name(prefix) + ":"):
                member = text[len(prefix) + 1:]
                if member:
                    found.append((archive, member))
    unique = {(str(a.path), m): (a, m) for a, m in found}
    require(len(unique) <= 1, "Ambiguous map archive label: " + text)
    if unique:
        return next(iter(unique.values()))
    # A direct object can be printed as an absolute Windows filename.
    if ":" in text and not re.match(r"^[A-Za-z]:[\\/]", text):
        raise WitnessError("Map references an unfrozen archive/default library: " + text)
    return None


def analyze_link_inputs(trace_text: str, archive_paths: Iterable[str | Path], *,
                        map_text: str = "") -> dict:
    paths = [Path(p).resolve(strict=True) for p in archive_paths]
    require(len(paths) == len(set(paths)), "Duplicate archive paths supplied")
    archives = [Archive(p) for p in paths]
    selected: dict[tuple[str, int], dict] = {}
    loaded_lines = 0
    other_loaded_lines = []
    reading_groups: dict[tuple[str, str], dict] = {}

    def add(archive, name, symbol, evidence, line_number):
        entry = archive.select(name, symbol)
        key = (entry["archive_path"], entry["header_offset"])
        if key not in selected:
            selected[key] = entry | {"trigger_symbols": [], "trace_lines": [],
                                     "map_lines": [], "reading_lines": []}
        if evidence != "reading":
            selected[key]["trigger_symbols"].append(symbol)
        selected[key][{"loaded": "trace_lines", "map": "map_lines",
                       "reading": "reading_lines"}[evidence]].append(line_number)
        return selected[key]

    for line_number, line in enumerate(trace_text.splitlines(), 1):
        reading = re.match(r"^\s*(?:lld-link:\s*)?Reading\s+(.+?)\s*$", line)
        if reading:
            member = _member_reference(reading.group(1))
            if member:
                archive = _resolve_archive(member.group(1), archives)
                key = (str(archive.path), norm_name(member.group(2)))
                reading_groups.setdefault(key, {"archive": archive,
                    "member_name": member.group(2), "trace_lines": []})["trace_lines"].append(line_number)
        match = re.match(r"^\s*(?:lld-link:\s*)?Loaded\s+(.+?)\s+for\s+(?:symbol\s+)?(.+?)\s*$", line)
        if not match:
            require(not (re.match(r"^\s*(?:lld-link:\s*)?Loaded\s+", line)
                         and re.search(r"\.(?:a|lib)\(", line, re.IGNORECASE)),
                    "Unsupported LLD archive extraction line: " + line)
            continue
        reference, symbol = match.groups()
        reference = reference.strip('"')
        member = _member_reference(reference)
        if not member:
            require(not re.search(r"\.(?:a|lib)(?:\(|$)", reference, re.IGNORECASE),
                    "Archive extraction lacks a member witness: " + line)
            other_loaded_lines.append({"line": line_number, "text": line})
            continue
        archive = _resolve_archive(member.group(1), archives)
        add(archive, member.group(2), symbol, "loaded", line_number)
        loaded_lines += 1
    map_symbols = 0
    for line_number, line in enumerate(map_text.splitlines(), 1):
        match = re.match(r"^\s*[0-9A-Fa-f]{4}:[0-9A-Fa-f]+\s+(\S+)\s+[0-9A-Fa-f]+\s+(.+?)\s*$", line)
        if not match:
            continue
        symbol, reference = match.groups()
        mapped = _map_reference(reference, archives)
        if mapped:
            archive, member_name = mapped
            add(archive, member_name, symbol, "map", line_number)
            map_symbols += 1
    group_receipts = []
    for (archive_path, _), group in reading_groups.items():
        archive, name = group["archive"], group["member_name"]
        try:
            single = archive.select(name, "NO_TRIGGER_IN_READING_TRACE")
        except WitnessError as exc:
            if "Ambiguous same-name" not in str(exc):
                raise
            single = None
        if single:
            for line_number in group["trace_lines"]:
                add(archive, name, "NO_TRIGGER_IN_READING_TRACE", "reading", line_number)
        matches = [entry for entry in selected.values() if entry["archive_path"] == archive_path
                   and (norm_name(entry["member_name"]) == norm_name(name)
                        or basename(entry["member_name"]) == basename(name))]
        require(bool(matches), "Reading member has no unambiguous trigger/map witness: " + archive_path + "(" + name + ")")
        payloads = {entry["member_sha256"] for entry in matches}
        offsets = {offset for entry in matches for offset in entry["equivalent_candidate_offsets"]}
        occurrences = len(group["trace_lines"])
        require(len(payloads) <= occurrences <= len(offsets),
                "Reading/map member occurrence mismatch: " + archive_path + "(" + name + ")")
        group_receipts.append({"archive_path": archive_path, "member_name": name,
                               "reading_trace_lines": group["trace_lines"],
                               "resolved_member_offsets": sorted(offsets),
                               "distinct_payloads": len(payloads),
                               "basis": "Loaded/map symbol definitions plus Reading occurrence bound; exact per-line duplicate-name assignment is not exposed by LLD"})
    require(loaded_lines > 0 or reading_groups,
            "No recognized LLD archive extraction witness; use bare /verbose and /map")
    for entry in selected.values():
        require(entry["trace_lines"] or entry["reading_lines"] or any(
            group["archive_path"] == entry["archive_path"] and entry["header_offset"] in group["resolved_member_offsets"]
            for group in group_receipts), "Map member has no actual extraction trace")
    entries = sorted(selected.values(), key=lambda x: (x["archive_path"], x["header_offset"]))
    for entry in entries:
        entry["trigger_symbols"] = sorted(set(entry["trigger_symbols"]))
    return {"schema": "heterospec.e04.lld-member-witness.v2",
            "status": "PASS_TRACE_CONTAINER_MEMBER_BINDINGS",
            "trace_utf8_sha256": sha256(trace_text.encode("utf8")),
            "map_utf8_sha256": sha256(map_text.encode("utf8")) if map_text else None,
            "recognized_loaded_lines": loaded_lines,
            "reading_member_lines": sum(len(g["trace_lines"]) for g in reading_groups.values()),
            "map_resolved_symbol_lines": map_symbols,
            "reading_groups": group_receipts,
            "selected_member_count": len(entries),
            "archives": [{"path": str(a.path), "bytes": len(a.data),
                          "sha256": a.sha256, "non_metadata_members": len(a.members)}
                         for a in archives],
            "selected_members": entries,
            "other_loaded_lines": other_loaded_lines,
            "scope": "Actual LLD extraction trace and optional same-link map bound to complete archive/member bytes; not execution or numerical qualification",
            "limits": ["Direct object files and non-archive tool/default-library inputs must be frozen separately.",
                       "An archive may be passed but contribute no members; its full container identity is retained.",
                       "This parser is not an OS filesystem-access trace or proof of all linker reads.",
                       "No thin archives or unresolved ambiguous member selection is admitted.",
                       "Weak SEARCH_ALIAS objects are exact archived resolution records, not callable code; alias target existence is not execution evidence."],
            "model_requests": 0, "GPU_launches": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--archives", required=True, type=Path,
                        help="JSON array of archive paths")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--map", dest="map_path", type=Path)
    args = parser.parse_args()
    result = analyze_link_inputs(args.trace.read_text(encoding="utf8"),
                                 json.loads(args.archives.read_text(encoding="utf8")),
                                 map_text=args.map_path.read_text(encoding="utf8") if args.map_path else "")
    with args.out.open("x", encoding="utf8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({"status": result["status"],
                      "selected_member_count": result["selected_member_count"]}))
