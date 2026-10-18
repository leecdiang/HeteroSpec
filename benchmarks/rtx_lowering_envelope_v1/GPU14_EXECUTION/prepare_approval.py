"""CPU/transport preflight only; never loads a backend or queries a device."""
import datetime, hashlib, json, subprocess, urllib.request
from pathlib import Path
E=Path(__file__).resolve().parent
R=E.parent/'repair_timer_v1'
COMMIT='9aefd4c722ac78421994052e41412c2c0417d73b'
EXPECTED='65a6a60b726572305e29f73e2d852936af9e4c87d9740cba5f95f97f738bd290'
def save(name,obj):
    with (E/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False); f.write('\n')
def git(*args):return subprocess.check_output(['git','-C','D:/hs113',*args])
assert git('rev-parse','HEAD').decode().strip()==COMMIT
assert git('branch','--show-current').decode().strip()=='design/rtx-native-lowering-envelope-20261015'
f0=(R/'GPU14_F0.json').read_bytes()
assert hashlib.sha256(f0).hexdigest()==EXPECTED
assert f0==(R/'REMOTE_GPU14_F0_BYTES.json').read_bytes()
assert not Path(json.loads(f0)['execution_root']).exists()
# All existing tracked bytes must still equal the reviewed commit. New evidence is untracked.
assert not git('diff','--name-only',COMMIT).strip()
token=subprocess.check_output(['gh','auth','token']).decode().strip()
endpoint='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/repair_timer_v1/GPU14_F0.json?ref='+COMMIT
req=urllib.request.Request(endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-GPU14-authorized-readback'})
with urllib.request.urlopen(req,timeout=45) as response:
    assert response.status==200 and response.headers.get('Content-Encoding','identity')=='identity'
    remote=response.read()
assert remote==f0
with (E/'REVIEWED_REMOTE_F0_BYTES.json').open('xb') as out:out.write(remote)
save('PREFLIGHT.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewed_commit=COMMIT,F0_sha256=EXPECTED,authenticated_remote_bytes=True,bytes=len(remote),endpoint=endpoint,tracked_bytes_equal_reviewed_commit=True,new_execution_root_absent=True,preflight_device_queries=0,preflight_native_starts=0,driver_identity_gate='Frozen controller performs planned readiness query before each host; no extra query'))
message=(E/'USER_APPROVAL.txt').read_text(encoding='utf-8').rstrip('\n')
save('AUTHOR_APPROVAL.json',dict(stage='TIMER_REPAIR_GPU14',F0_sha256=EXPECTED,reviewed_commit=COMMIT,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),time_semantics='Actual local receipt recording time after the human message; no fabricated earlier approval time',author_message=message,author_message_sha256=hashlib.sha256(message.encode()).hexdigest(),run_id='pr113-timer-gpu-regression-v1',authority='Current explicit human message in this chat',historical_F0_status_unchanged=True,limits=json.loads(f0)['limits']))
print('PASS reviewed commit/F0/remote bytes; separate current human approval saved; no device query or native start')
