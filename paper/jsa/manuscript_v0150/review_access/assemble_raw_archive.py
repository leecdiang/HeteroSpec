#!/usr/bin/env python3
"""Check ordered raw parts and assemble an archive, without extracting or executing it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--archive", required=True)
parser.add_argument("--parts-dir", type=Path, required=True, help="Directory with the listed part basenames")
parser.add_argument("--output", type=Path, required=True, help="New output file; never overwrite an existing file")
args = parser.parse_args()
plan = json.loads((Path(__file__).resolve().parent / "RAW_ARCHIVE_ACCESS.json").read_text())
matches = [x for x in plan["archives"] if x["id"] == args.archive]
if len(matches) != 1:
    raise SystemExit("Choose an archive ID from RAW_ARCHIVE_ACCESS.json")
record = matches[0]
args.output.parent.mkdir(parents=True, exist_ok=True)
if args.output.exists():
    raise SystemExit("Output already exists; use a new destination")
whole = hashlib.sha256()
size = 0
temporary = None
try:
    with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as output:
        temporary = Path(output.name)
        for part in record["parts"]:
            name = part["name"]
            if Path(name).name != name or name in {".", ".."}:
                raise ValueError("Unsafe part name")
            path = args.parts_dir / name
            current = hashlib.sha256()
            count = 0
            with path.open("rb") as source:
                while block := source.read(1024 * 1024):
                    count += len(block)
                    current.update(block)
                    whole.update(block)
                    output.write(block)
            if count != part["bytes"] or current.hexdigest() != part["sha256"]:
                raise ValueError(f"Part hash/length mismatch: {name}")
            size += count
        if size != record["archive_bytes"] or whole.hexdigest() != record["archive_sha256"]:
            raise ValueError("Whole archive hash/length mismatch")
    # Atomic creation without replacing a destination created during verification.
    os.link(temporary, args.output)
    print(f"PASS: {args.archive}, {size} bytes, SHA256 {whole.hexdigest()}")
    print("Archive transport verified. Logical-file restoration and scientific audits remain separate.")
finally:
    if temporary is not None:
        temporary.unlink(missing_ok=True)
