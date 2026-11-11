import os
import argparse
import hashlib
import json
from pathlib import Path
from huggingface_hub import model_info, snapshot_download

repo_id = "Qwen/Qwen3-8B"
root = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
target = root / "models" / "qwen3-8b"
revision = "b968826d9c46dd6066d109eabc6255188de91218"
parser = argparse.ArgumentParser()
parser.add_argument("--manifest-only", action="store_true")
args = parser.parse_args()
if not args.manifest_only:
    snapshot_download(
        repo_id=repo_id,
        revision=revision,
        local_dir=target,
        max_workers=1,
    )
files = []
for p in sorted(target.rglob("*")):
    if p.is_file() and ".cache" not in p.parts:
        h = hashlib.sha256()
        with p.open("rb") as f:
            while chunk := f.read(8 * 1024 * 1024):
                h.update(chunk)
        files.append({"path": str(p.relative_to(target)), "bytes": p.stat().st_size, "sha256": h.hexdigest()})
manifest = {"repo_id": repo_id, "revision": revision, "files": files, "total_bytes": sum(x["bytes"] for x in files)}
(root / "env" / "qwen3-8b-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"repo_id": repo_id, "revision": revision, "file_count": len(files), "total_bytes": manifest["total_bytes"]}, indent=2))
