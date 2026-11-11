from common98 import *
import re
modules=json.loads((ROOT/'raw/base_probe_A/MODULES.stdout').read_text(encoding='utf-8-sig'))
prior=json.loads((ROOT/'baseline/pr99/raw/p0_probe_A/MODULES.stdout').read_text(encoding='utf-8-sig'))
selected=[Path(p) for p in modules if re.search(r'igvk|vulkan-1|vcruntime|msvcp140|GPP_VK|IntelControl',p,re.I)]
pins=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),file_mtime_ns=p.stat().st_mtime_ns,also_present_in_immutable_PR99_MODULES=str(p).lower() in [str(q).lower() for q in prior]) for p in selected]
save(ROOT/'LOADED_DRIVER_RUNTIME_HASHES.json',dict(scope='Actual zero-forward ownPID module paths; full body hashes recorded after start, no claim these driver binary hashes were individually authenticated in initial F0. Initial F0 froze live driver version/Vulkan properties and full historical module-path bytes. Full numerical DLLs/exes/model SHA were authenticated before forward.',pins=pins,utc=now(),before_P1C_and_P0=True,version='32.0.101.9034',source_PID=load(ROOT/'raw/base_probe_A/IDENTITY.json')['owned_pid']))
print('DRIVER_BODIES',len(pins),flush=True)
