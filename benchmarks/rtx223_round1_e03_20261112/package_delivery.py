"""Export source/receipts plus explicitly hash-bound review artifacts."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
TEXT = {".py", ".md", ".json", ".jsonl", ".log", ".txt", ".patch", ".cu", ".cuh", ".hpp", ".h", ".cpp", ".inc", ".ps1", ".c", ".def", ".rsp", ".inl"}
TOP_DIRS = {"src", "tests", "qualification", "native", "build_tools", "request", "audit", "review", "upstream221", "upstream213", "upstream215", "provenance", "resources", "delivery", "continuation", "e03", "runtime"}
BAD_PARTS = {".git", "__pycache__", "compiler_copy", "ledger_copies", "private", "cache", "temp", "bin"}


def selected():
    out = []
    original = json.loads((ROOT / "runtime/SOURCE_PREPARED.json").read_bytes())["old_source_sha256"]
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
        if len(rel.parts) > 2 and rel.parts[0] == "runtime":
            variant = rel.parts[1]
            if variant.startswith("reconstruct"):
                continue  # verified restoration output is reproducible, not another source distribution
            if variant == "source" or variant.startswith("final-source"):
                member = Path(*rel.parts[2:]).as_posix()
                if original.get(member) == hashlib.sha256(p.read_bytes()).hexdigest():
                    continue  # pinned unchanged core is supplied through delta-v2/ORIGIN_MANIFEST.json
        if rel.parts[:2] == ("audit", "recovered_operand") and p.name != "PROVENANCE.json":
            continue
        if rel.as_posix() in ("delivery/DELIVERY_MANIFEST.json", "delivery/ZIP_VERIFIED.json", "delivery/GITHUB_PUBLICATION.json"):
            continue
        p.read_bytes().decode("utf8")  # refuse arbitrary/binary content under text names
        out.append(p)
    return sorted(out)


def explicit_artifacts():
    rows = json.loads((ROOT / "e03/BINARY_ALLOWLIST.json").read_bytes())["files"]
    for row in rows:
        relative = Path(row["path"])
        if relative.is_absolute() or relative.drive or ".." in relative.parts:
            raise ValueError("Unsafe binary artifact path")
        path = (ROOT / relative).resolve(strict=True)
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Explicit artifact identity differs")
    return rows


def cpu_ledger_files():
    """Own CPU fixture/new-family databases only; never old/copied thread DBs."""
    output = []
    prefixes = (ROOT / "continuation/safety", ROOT / "continuation/review")
    for base in prefixes:
        if not base.exists():
            continue
        for p in base.rglob("*.sqlite"):
            rel = p.relative_to(ROOT)
            if any(part in BAD_PARTS for part in rel.parts):
                continue
            if "raw" in rel.parts or rel.as_posix() == "continuation/safety/runtime/family-ledger.sqlite":
                output.append(p)
    return sorted(output)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--payload", type=Path)
    args = ap.parse_args()
    files = selected()
    cpu_ledgers = cpu_ledger_files()
    artifacts = explicit_artifacts()
    manifest = {"schema": "heterospec.rtx221-round1.delivery.v1", "files": [
        {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "published_in_Git": p.stat().st_size <= 512 * 1024,
         "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
         "git_blob": hashlib.sha1(b"blob " + str(p.stat().st_size).encode() + b"\0" + p.read_bytes()).hexdigest()}
        for p in files], "zip_only_CPU_ledgers": [
            {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "published_in_Git": False}
            for p in cpu_ledgers],
        "zip_only_explicit_artifacts": [{**row, "bytes": (ROOT / row["path"]).stat().st_size} for row in artifacts],
        "exclusions": ["model weights", "historical model numeric payloads", "unrelated thread databases", "toolchain copies", "unlisted executable and object/library products", "private contextual lookup payloads", "unchanged original core source reproducible from the pinned kit"],
        "native_work": "NOT_RUN", "verdict": "INCONCLUSIVE", "epoch": "rtx223-round1-20261112-e03", "manifest_self_included": False}
    dest = ROOT / "delivery/DELIVERY_MANIFEST.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(manifest, indent=2), encoding="utf8")
    all_files = files + [dest]
    git_files = [p for p in all_files if p == dest or p.stat().st_size <= 512 * 1024]
    zip_files = all_files + cpu_ledgers + [ROOT / row["path"] for row in artifacts]
    if args.zip:
        if args.zip.exists():
            raise FileExistsError(args.zip)
        with zipfile.ZipFile(args.zip, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for p in zip_files:
                z.write(p, p.relative_to(ROOT).as_posix())
        with zipfile.ZipFile(args.zip) as z:
            if z.namelist() != [p.relative_to(ROOT).as_posix() for p in zip_files]:
                raise ValueError("ZIP inventory differs")
            for p in zip_files:
                if z.read(p.relative_to(ROOT).as_posix()) != p.read_bytes():
                    raise ValueError("ZIP bytes differ: " + str(p))
        receipt = {"zip": str(args.zip.resolve()), "files": len(zip_files), "Git_text_files": len(git_files), "zip_only_large_text_files": len(all_files) - len(git_files), "zip_only_CPU_ledgers": len(cpu_ledgers), "zip_only_explicit_artifacts": len(artifacts), "bytes": args.zip.stat().st_size,
                   "sha256": hashlib.sha256(args.zip.read_bytes()).hexdigest(), "every_entry_rehashed": True}
        (ROOT / "delivery/ZIP_VERIFIED.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
        print(json.dumps(receipt))
    if args.payload:
        payload = [{"path": p.relative_to(ROOT).as_posix(), "mode": "100644", "type": "blob", "content": p.read_bytes().decode("utf8")} for p in git_files]
        args.payload.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf8")
        print(json.dumps({"payload": str(args.payload), "files": len(payload), "total_source_bytes": sum(p.stat().st_size for p in git_files)}))


if __name__ == "__main__":
    main()
