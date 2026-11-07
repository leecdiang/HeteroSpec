import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

REPO_ID = "OpenVINO/Qwen3-0.6B-int4-ov"
ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
MODEL_DIR = ROOT / "models" / "qwen3-0.6b-int4-ov"
METADATA = ROOT / "env" / "qwen3-0.6b-int4-ov-manifest.json"

os.environ.setdefault("HF_HOME", str(ROOT / "hf-cache"))
info = HfApi().model_info(REPO_ID)
revision = info.sha
print(f"repo={REPO_ID}")
print(f"resolved_revision={revision}")

snapshot_download(
    repo_id=REPO_ID,
    revision=revision,
    local_dir=MODEL_DIR,
)

files = []
for path in sorted(p for p in MODEL_DIR.rglob("*") if p.is_file() and ".cache" not in p.parts):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    files.append({
        "path": path.relative_to(MODEL_DIR).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    })

payload = {
    "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
    "repo_id": REPO_ID,
    "resolved_revision": revision,
    "local_dir": str(MODEL_DIR),
    "total_bytes": sum(item["bytes"] for item in files),
    "files": files,
}
METADATA.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"files={len(files)}")
print(f"total_bytes={payload['total_bytes']}")
print(f"manifest={METADATA}")
