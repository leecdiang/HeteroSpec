"""Bind disk identities and classify possible loader inputs without mapping executable code."""
from collections import defaultdict, deque
from pathlib import Path
import argparse
import hashlib
import json
import mmap
import os
import runpy
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
E04 = ROOT.parent / "rtx223-round1-resume-20261112-e04"
STAGED = E04 / "e04/frontend/expected-modules-v1"
SYSTEM = Path(os.environ["SystemRoot"]).resolve() / "System32"
CUPTI = Path("E:/rtx170/profiler/sdk/nvidia/cuda_cupti/bin/cupti64_2025.2.1.dll")
PELIB = E04 / "e04/frontend/pe_identity_v2.py"
PYTHON = Path("D:/HeteroSpec-PC/python311/python.exe")


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def pe_directory(raw):
    pe, = struct.unpack_from("<I", raw, 60)
    if raw[pe:pe+4] != b"PE\0\0":
        raise ValueError("PE signature")
    n, = struct.unpack_from("<H", raw, pe+6)
    opt, = struct.unpack_from("<H", raw, pe+20)
    sections = {}
    for i in range(n):
        off = pe+24+opt+i*40
        name = raw[off:off+8].rstrip(b"\0").decode("ascii", errors="replace")
        sections[name] = struct.unpack_from("<IIII", raw, off+8)
    return pe, sections


def version(path):
    """Read VS_FIXEDFILEINFO only from a checked RT_VERSION resource."""
    with path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as raw:
        pe, sections = pe_directory(raw)
        def offset(rva, size):
            for virtual, base, length, start in sections.values():
                delta = rva - base
                if 0 <= delta and delta + size <= length and start+delta+size <= len(raw):
                    return start+delta
            raise ValueError("resource RVA out of bounds")
        table = pe+24+(112 if struct.unpack_from("<H", raw, pe+24)[0] == 0x20b else 96)
        rva, size = struct.unpack_from("<II", raw, table+16)
        if not rva or size < 16:
            return None
        base = offset(rva, size)
        def entries(rel):
            if rel+16 > size:
                raise ValueError("resource header out of bounds")
            n, m = struct.unpack_from("<HH", raw, base+rel+12)
            if rel+16+(n+m)*8 > size:
                raise ValueError("resource table out of bounds")
            return [struct.unpack_from("<II", raw, base+rel+16+i*8) for i in range(n+m)]
        types = [value for key, value in entries(0) if key == 16]
        if not types:
            return None
        ref = types[0]
        for _ in range(2):
            if not ref & 0x80000000:
                raise ValueError("version resource tree")
            ref = entries(ref & 0x7fffffff)[0][1]
        if ref & 0x80000000 or ref+16 > size:
            raise ValueError("version resource leaf")
        data_rva, data_len = struct.unpack_from("<II", raw, base+ref)
        start = offset(data_rva, data_len)
        key = "VS_VERSION_INFO\0".encode("utf-16le")
        if raw[start+6:start+6+len(key)] != key:
            return None
        fixed = start + ((6+len(key)+3) & ~3)
        if fixed + 16 > start + data_len:
            return None
        sign, _, ms, ls = struct.unpack_from("<IIII", raw, fixed)
        return ".".join(map(str, [ms>>16, ms&0xffff, ls>>16, ls&0xffff])) if sign==0xfeef04bd else None


def identity(path):
    path = Path(path).resolve(strict=True)
    before = path.stat()
    record = {"path": str(path), "sha256": sha(path), "bytes": before.st_size,
              "file_id": {"volume": before.st_dev, "inode": before.st_ino}}
    if path.suffix.lower() in (".exe", ".dll", ".pyd"):
        record["version"] = version(path)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError(f"file changed during read: {path}")
    return record


def api_sets():
    path = SYSTEM / "apisetschema.dll"
    raw = path.read_bytes()
    _, sections = pe_directory(raw)
    virtual, _, length, start = sections[".apiset"]
    buf = raw[start:start+min(length,virtual)]
    version_, size, _, count, at, _, _ = struct.unpack_from("<7I", buf)
    if version_ != 6 or size > len(buf) or count > 100000:
        raise ValueError("unsupported API set schema")
    def utf(pos, length):
        if pos+length > size:
            raise ValueError("invalid contract string")
        return buf[pos:pos+length].decode("utf-16le").lower()
    result = {}
    hashed = {}
    for i in range(count):
        _, name_off, name_len, hash_len, values, n = struct.unpack_from("<6I", buf, at+i*24)
        choices = {}
        for j in range(n):
            _, key, keylen, host, hostlen = struct.unpack_from("<5I", buf, values+j*20)
            choices[utf(key,keylen)] = utf(host,hostlen)
        result[utf(name_off,name_len)+".dll"] = choices
        prefix = utf(name_off,hash_len)
        if prefix in hashed and hashed[prefix] != choices:
            raise ValueError("ambiguous API set hashed-prefix hosts")
        hashed[prefix] = choices
    return result, hashed


def ordinal_exports(path):
    """Map unnamed ordinal forwarders as well as named export aliases."""
    with path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as raw:
        pe, sections = pe_directory(raw)
        start, nbytes = struct.unpack_from("<II", raw, pe+24+112)
        if not start:
            return {}
        def offset(rva, length):
            for _, addr, size, at in sections.values():
                delta = rva-addr
                if 0 <= delta and delta+length <= size and at+delta+length <= len(raw):
                    return at+delta
            raise ValueError("export table outside mapped file")
        hdr = offset(start,40)
        base, count, _, funcs = struct.unpack_from("<4I",raw,hdr+16)
        data = offset(funcs,4*count)
        result = {}
        for i in range(count):
            address, = struct.unpack_from("<I",raw,data+4*i)
            if start <= address < start+nbytes:
                pos = offset(address,1)
                end = raw.find(b"\0",pos,min(len(raw),pos+32768))
                if end < 0:
                    raise ValueError("invalid ordinal forwarder")
                result["#"+str(base+i)] = {"forwarder": raw[pos:end].decode("ascii")}
        return result


def collect_deployment(images, out):
    location = json.loads((STAGED/"MODULE_CLOSURE_v3.json").read_bytes())
    staged = sorted(STAGED.glob("*.dll"))
    records = {f.name.lower():identity(f) for f in [*staged, CUPTI, SYSTEM/"nvcuda.dll", SYSTEM/"nvml.dll"]}
    if len(staged) != 9:
        raise ValueError("staged membership changed")
    for path in staged:
        if records[path.name.lower()]["sha256"] != location["modules"][path.name.lower()]["sha256"]:
            raise ValueError(f"e04 drift {path}")
    e05_expected = {
        CUPTI.name: "be1ecb387e14c1c0515b3b162b44c89b480c9a12f16c60f7b82eb8b1ebc35e74",
        "nvcuda.dll": "f2b550e83f56b7b819efe382d712d125ee180341f012bd0aba2288320609a45a"}
    if any(records[k]["sha256"] != v for k,v in e05_expected.items()):
        raise ValueError("e05 metering or driver loader drift")
    roots = [Path(r["path"]) for r in records.values()] + images
    # NT process bootstrap and the default Win32/CRT forward targets.
    roots += [SYSTEM/n for n in ("ntdll.dll", "kernelbase.dll", "kernel32.dll", "msvcrt.dll", "ucrtbase.dll")]
    # The installed display driver's actual loader copies identify its DriverStore package.
    candidates = SYSTEM/"DriverStore/FileRepository"
    for package in sorted(candidates.glob("nv*.inf_*")):
        loader = package/"nvcuda_loader64.dll"
        if loader.is_file() and sha(loader) == records["nvcuda.dll"]["sha256"]:
            for name in ("nvcuda64.dll","nvcuda_loader64.dll","nvml.dll","nvml_loader.dll","nvapi64.dll","nvapi64_impl.dll"):
                path = package/name
                if path.is_file():
                    roots.append(path)
    if sha(PELIB) != "a5029ff6f885991793fb04dffb56a74bef8db188151d6cb879680f3c228fdb3c":
        raise ValueError("offline parser changed")
    inspect = runpy.run_path(str(PELIB))["inspect"]
    apis, compatible_contracts = api_sets()
    unresolved, skips, edges = set(), set(), set()
    known = {p.name.lower():p for p in staged}
    cache = {}
    paths = set()
    origins = defaultdict(set)
    queue = deque((p,"root") for p in roots)
    looked_up = set()
    forward_queue = deque()

    def locate(importer, name):
        name = name.lower()
        if Path(name).name != name:
            raise ValueError("import escapes directory")
        if name.startswith(("api-", "ext-")):
            prefix, _, minor = name.removesuffix(".dll").rpartition("-")
            choices = apis.get(name)
            if choices is None:
                choices = compatible_contracts.get(prefix,{}) if minor.isdigit() else {}
            name = choices.get(importer.name.lower(), choices.get("", ""))
            if not name:
                return None
        if name in known:
            return known[name]
        if candidates in importer.parents and (importer.parent/name).is_file():
            return (importer.parent/name).resolve()
        return (SYSTEM/name).resolve() if (SYSTEM/name).is_file() else None

    while queue or forward_queue:
        if queue:
            path, why = queue.popleft()
            path = path.resolve()
            origins[path].add(why)
            if path in paths:
                continue
            paths.add(path)
            pe = inspect(path)
            cache[path] = pe["exports"]
            cache[path].update(ordinal_exports(path))
            for lib, symbols in pe["import_symbols"].items():
                target = locate(path, lib)
                if target:
                    queue.append((target,path.name+" imports "+lib))
                    edges.add((str(path),lib,str(target)))
                    forward_queue.extend((target,s if isinstance(s,str) else "#"+str(s["ordinal"])) for s in symbols)
                else:
                    unresolved.add((path.name,lib))
            skips.update((path.name,s,"delay route not preapproved on name alone") for s in pe["delay_imports"])
        else:
            path, symbol = forward_queue.popleft()
            if (path,symbol) in looked_up:
                continue
            looked_up.add((path,symbol))
            forwarded = cache[path].get(symbol,{}).get("forwarder")
            if forwarded:
                name, func = forwarded.rsplit(".",1)
                name = name if name.lower().endswith(".dll") else name+".dll"
                target = locate(path,name)
                if target:
                    queue.append((target,path.name+" forwards "+symbol))
                    edges.add((str(path),name,str(target)))
                    forward_queue.append((target,func))
                else:
                    unresolved.add((path.name,name))
    extra = []
    module_paths = {Path(r["path"]) for r in records.values()}
    for path in sorted(paths - module_paths - set(images), key=str):
        extra.append({"name":path.name.lower(),**identity(path),"reviewed":True,
                      "reason":sorted(origins[path])})
    write(out, {"schema":"heterospec.e06.deployment.v1","modules":records,"candidates":extra,
          "api_set_schema":identity(SYSTEM/"apisetschema.dll"), "native_outputs_used_as_import_roots":list(map(str,images)),
          "scope":"offline roots, non-delay PE imports and their selected named/ordinal forward and API-set targets; unknown identities must stop; concurrent or short-lived image load not certified.",
          "unresolved_imports":sorted(unresolved),"other_routes":sorted(skips),
          "actual_loaded_modules":"NOT_RUN","actual_driver_paths":"NOT_RUN"})
    write(out.with_suffix(".edges.json"), sorted(edges))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("images", type=Path, nargs="*")
    args = parser.parse_args()
    collect_deployment([p.resolve(strict=True) for p in args.images], args.out.resolve())
