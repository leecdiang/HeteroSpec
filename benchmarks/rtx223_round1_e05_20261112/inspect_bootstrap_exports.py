"""Check proposed B entry points as PE data. Never load or call any DLL."""
import hashlib
import json
import runpy
import sys
from pathlib import Path


e04 = Path(sys.argv[1]).resolve(strict=True)
reader = e04 / "e04/frontend/pe_identity_v2.py"
if hashlib.sha256(reader.read_bytes()).hexdigest() != "a5029ff6f885991793fb04dffb56a74bef8db188151d6cb879680f3c228fdb3c":
    raise ValueError("Unexpected offline PE parser")
inspect = runpy.run_path(str(reader))["inspect"]
targets = [
    (e04 / "e04/frontend/expected-modules-v1/cudart64_12.dll",
     "760c38928bbe5759f7b31ed6692599eb7ec83cedd5702e84c2b72028a89837e1",
     ["cudaGetDeviceCount", "cudaGetDeviceProperties_v2"]),
    (Path(sys.argv[2]), "be1ecb387e14c1c0515b3b162b44c89b480c9a12f16c60f7b82eb8b1ebc35e74",
     ["cuptiGetVersion", "cuptiSubscribe", "cuptiEnableCallback", "cuptiActivityRegisterCallbacks",
      "cuptiActivityEnable", "cuptiActivityFlushAll", "cuptiActivityGetNumDroppedRecords",
      "cuptiActivityGetNextRecord", "cuptiActivityDisable", "cuptiUnsubscribe"]),
]
images = []
passed = True
for path, expected, names in targets:
    image = inspect(path)
    exports = {name: image["exports"].get(name) for name in names}
    valid = (image["sha256"] == expected and image["is_dll"] and
             all(item and item["rva"] and item["forwarder"] is None for item in exports.values()))
    passed = passed and valid
    images.append({"name": path.name, "sha256": image["sha256"], "bytes": image["bytes"],
                   "direct_exports": exports, "matches_disk_proposal": valid})
print(json.dumps({"scope": "disk only; runtime ABI, permissions, activity coverage NOT_RUN",
                  "images": images, "pass": passed}, indent=2))
sys.exit(0 if passed else 1)
