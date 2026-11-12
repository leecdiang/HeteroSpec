"""Read old ledgers only; immutable/readonly SQLite canonical count check."""
import datetime
import hashlib
import json
import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OLD = ROOT.parent / "rtx223-round1-resume-20261112-e03"
prior = json.loads((OLD / "e03/dedup/FRESH_PROCESS_LOCK_LEDGER.json").read_text(encoding="utf-8"))
ledgers = [x for x in prior["files"] if x["path"].endswith(".sqlite")]
records = []
for entry in ledgers:
    path = pathlib.Path(entry["path"])
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    records.append({"path": str(path), "bytes": path.stat().st_size,
                    "sha256": before, "matches_e03": before == entry["sha256"]})
canonical = next(x for x in ledgers if x["path"].endswith("family-ledger.sqlite"))
path = pathlib.Path(canonical["path"])
with sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True) as db:
    tables = {table: db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
              for table in ("family", "attempts")}
after = hashlib.sha256(path.read_bytes()).hexdigest()
receipt = {
    "schema": "heterospec.e04.independent-old-ledger-preservation.v1",
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "ledgers": records, "canonical_tables": tables,
    "canonical_hash_after_read": after,
    "SQLite_mode": "ro and immutable; no journal creation or write capability requested",
    "passed": all(x["matches_e03"] for x in records) and
              after == canonical["sha256"] and tables == {"family": 1, "attempts": 0},
    "new_allowance": False, "GPU_calls": 0, "models": 0,
    "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
}
name = sys.argv[1] if len(sys.argv) > 1 else "LEDGER_PRESERVATION_INITIAL.json"
out = pathlib.Path(__file__).resolve().parent / name
if out.exists():
    raise ValueError("Refuse overwriting independent ledger receipt")
out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": receipt["passed"], "ledgers": len(records), "canonical_tables": tables}))
raise SystemExit(not receipt["passed"])
