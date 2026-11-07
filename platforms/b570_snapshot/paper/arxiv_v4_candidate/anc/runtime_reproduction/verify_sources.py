"""Verify byte identity of the copied source excerpts; no GPU or network."""
import hashlib
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "PROVENANCE.json").read_text())
    receipts = []
    for entry in manifest["files"]:
        path = root / entry["local"]
        data = path.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if blob != entry["git_blob"]:
            raise SystemExit("source identity mismatch: " + entry["local"])
        receipts.append({"file": entry["local"], "bytes": len(data),
                         "git_blob": blob, "sha256": hashlib.sha256(data).hexdigest()})
    print(json.dumps({"status": "PASS", "files": receipts,
                      "new_native_executions": 0}, indent=2))

if __name__ == "__main__":
    main()
