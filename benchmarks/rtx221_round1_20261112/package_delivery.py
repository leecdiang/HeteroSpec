"""Export compact review artifacts; never package models, old ledgers or tools."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
TEXT = {".py", ".md", ".json", ".log", ".cu", ".cuh", ".hpp", ".h", ".cpp", ".inc"}
TOP_DIRS = {"src", "tests", "qualification", "native", "build_tools", "request", "audit", "review", "upstream221", "upstream213", "upstream215", "provenance", "resources", "delivery"}
BAD_PARTS = {".git", "__pycache__", "compiler_copy", "ledger_copies", "private", "cache", "temp", "bin"}


def selected():
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in BAD_PARTS or "cache" in part.lower() for part in rel.parts[:-1]):
            continue
        if len(rel.parts) > 1 and rel.parts[0] not in TOP_DIRS:
            continue
        if p.suffix not in TEXT and p.name not in (".gitignore", ".gitattributes", "UPSTREAM_LICENSE"):
            continue
        if rel.parts[:2] == ("audit", "recovered_operand") and p.name != "PROVENANCE.json":
            continue
        if rel.as_posix() in ("delivery/DELIVERY_MANIFEST.json", "delivery/ZIP_VERIFIED.json", "delivery/GITHUB_PUBLICATION.json"):
            continue
        p.read_bytes().decode("utf8")  # refuse arbitrary/binary content under text names
        out.append(p)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--payload", type=Path)
    args = ap.parse_args()
    files = selected()
    manifest = {"schema": "heterospec.rtx221-round1.delivery.v1", "files": [
        {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
         "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
         "git_blob": hashlib.sha1(b"blob " + str(p.stat().st_size).encode() + b"\0" + p.read_bytes()).hexdigest()}
        for p in files], "exclusions": ["model weights", "all historical/new numeric binary payloads", "copied old ledgers", "toolchain copies", "executable and object/library products", "private contextual lookup payloads"],
        "native_work": "NOT_RUN", "verdict": "INCONCLUSIVE", "manifest_self_included": False}
    dest = ROOT / "delivery/DELIVERY_MANIFEST.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(manifest, indent=2), encoding="utf8")
    all_files = files + [dest]
    if args.zip:
        if args.zip.exists():
            raise FileExistsError(args.zip)
        with zipfile.ZipFile(args.zip, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for p in all_files:
                z.write(p, p.relative_to(ROOT).as_posix())
        with zipfile.ZipFile(args.zip) as z:
            if z.namelist() != [p.relative_to(ROOT).as_posix() for p in all_files]:
                raise ValueError("ZIP inventory differs")
            for p in all_files:
                if z.read(p.relative_to(ROOT).as_posix()) != p.read_bytes():
                    raise ValueError("ZIP bytes differ: " + str(p))
        receipt = {"zip": str(args.zip.resolve()), "files": len(all_files), "bytes": args.zip.stat().st_size,
                   "sha256": hashlib.sha256(args.zip.read_bytes()).hexdigest(), "every_entry_rehashed": True}
        (ROOT / "delivery/ZIP_VERIFIED.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
        print(json.dumps(receipt))
    if args.payload:
        payload = [{"path": p.relative_to(ROOT).as_posix(), "mode": "100644", "type": "blob", "content": p.read_bytes().decode("utf8")} for p in all_files]
        args.payload.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf8")
        print(json.dumps({"payload": str(args.payload), "files": len(payload), "total_source_bytes": sum(p.stat().st_size for p in all_files)}))


if __name__ == "__main__":
    main()
