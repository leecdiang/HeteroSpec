"""Read-only final identity readback. No native/model process is launched."""
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

work=Path(__file__).parent
repo=work/'HeteroSpec'
registration='benchmarks/rtx_jsa_closeout_v1/revision_a/F0B_EXECUTION.json'
sys.path.insert(0,str((repo/registration).parent))
import runner

config=repo/registration
root=Path(json.loads(config.read_bytes())['run_root'])
assert not (root/'EXECUTION.lock').exists() and (root/'TIMING_RECORDS.json').is_file()
start=time.perf_counter()
frozen=runner.check_freeze(config,'87570e6ac4c3f5060b5086969dfc5214e7b17da2',registration)
receipt={'status':'PASS_POST_EXECUTION_FROZEN_BYTES_AND_AUTHENTICATED_READBACK',
    'execution_commit':'87570e6ac4c3f5060b5086969dfc5214e7b17da2',
    'registration_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),
    'files_checked':len(frozen['files']),'seconds':time.perf_counter()-start,
    'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_launches':0}
with (work/'POST_EXECUTION_FREEZE.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(receipt,stream,indent=2);stream.write('\n')
print(json.dumps(receipt,indent=2))
