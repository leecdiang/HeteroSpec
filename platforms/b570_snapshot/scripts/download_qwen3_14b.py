import os
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import snapshot_download


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
REPO = "Qwen/Qwen3-14B"
REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"
DEST = ROOT / "models" / "qwen3-14b"


snapshot_download(
    repo_id=REPO,
    revision=REVISION,
    local_dir=DEST,
    max_workers=1,
    allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt", "*.jinja", "LICENSE", "README.md"],
)

files = []
for path in sorted(DEST.rglob("*")):
    if path.is_file() and ".cache" not in path.parts:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                digest.update(block)
        files.append({"path": str(path.relative_to(DEST)), "bytes": path.stat().st_size, "sha256": digest.hexdigest()})

manifest = {
    "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    "repo": REPO, "revision": REVISION, "path": str(DEST), "files": files,
}
(ROOT / "env" / "qwen3-14b-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASS", "files": len(files), "bytes": sum(item["bytes"] for item in files), "path": str(DEST)}, indent=2))
