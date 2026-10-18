"""Record the actual attached numerical-only author approval and read-only preflight."""
import datetime,hashlib,json,shutil,subprocess,sys,urllib.request
from pathlib import Path
D=Path(__file__).resolve().parent;V=D.parent
sys.path.insert(0,str(V))
from common import load,save,sha

review='ba5719149c2ae5e8f0ac6d1f68a4bd5b248b5e4f'
hashes=dict(F0_sha256='73ef7106240be73ab914e4c6a36064a0d1fd6d41ce5d9c38bf65f38e8331f080',census_sha256='11d6cb5c18eb934e5d5c5e851d4bf90814088d0a52e45425666ca89ee7a4a878',decision_sha256='3051209f293f755218c2488effc43f33f78cf92714e332afa558f9009ac71db6')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=V).decode().strip()==review
assert subprocess.check_output(['git','branch','--show-current'],cwd=V).decode().strip()=='design/rtx-native-lowering-envelope-20261015'
f0=load(V/'F0.json');plan=load(V/'PLAN.json');root=Path(f0['execution_root'])
assert sha(V/'F0.json')==hashes['F0_sha256'] and (V/'F0.json').read_bytes()==(V/'REMOTE_F0_BYTES.json').read_bytes()
assert sha(root/'census/native/CENSUS.json')==hashes['census_sha256'] and sha(root/'CENSUS_DECISION.json')==hashes['decision_sha256']
assert load(root/'CENSUS_SUCCESS.json')['completed_census'] and load(root/'CENSUS_ENDED.json')['error'] is None
assert load(root/'CENSUS_DECISION.json')['numerical_admitted']
auth=load(root/'CENSUS_AUTHENTICATED.json');assert auth==load(V/'census_execution/AUTHENTICATED_CENSUS.json')
assert auth['authenticated_remote_bytes'] and all(auth[k]==v for k,v in hashes.items())
for path in (root/'numerical',root/'ACTIVE_CONTROLLER.lock',root/'NUMERICAL_FAILED.json',root/'NUMERICAL_ENDED.json',root/'NUMERICAL_WATCHDOG_STOP.json',V/'execution_ledger/NUMERICAL_CONTROLLER_STARTED.json'):
    assert not path.exists(),str(path)+' already exists: no restart'
assert len(plan['descriptors'])==72 and len(plan['numerical_slots'])==720
assert all(s['q']==1 for s in plan['numerical_slots'][:180]) and all(s['q']>1 for s in plan['numerical_slots'][180:])
assert sum(s['registered_support_queries'] for s in plan['numerical_slots'])==10836
assert f0['budget']==load(V/'BUDGET.json')
assert shutil.disk_usage(root.anchor).free>=f0['budget']['limits']['minimum_volume_free_before_start_bytes']
# No native CPU tests or device probes: the frozen controller verifies every
# pinned byte before its first readiness/native process. Check its own sources now.
for name,expected in f0['source_roles'].items():
    candidates=[p for p in f0['files'] if Path(p['path']).name==name and p['sha256']==expected]
    assert candidates and all(sha(p['path'])==expected for p in candidates),name
assert sha(f0['executable'])==f0['executable_sha256']
assert len(f0['numerical_DLLs'])==21
for name,expected in f0['numerical_DLLs'].items():assert sha(Path(f0['runtime_directory'])/name)==expected

token=subprocess.check_output(['gh','auth','token']).decode().strip()
url='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/F0.json?ref='+review
request=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-formal-numerical-author-preflight'})
with urllib.request.urlopen(request,timeout=45) as response:
    assert response.status==200;remote=response.read()
assert remote==(V/'F0.json').read_bytes()
attachment=Path('C:/Users/ASUS/.codex/attachments/63c07da8-18c8-41a8-8a0f-795fbb3e2863/已粘贴的文本.txt')
raw=attachment.read_bytes();message=raw.decode('utf-8')
assert 'FORMAL_V2_NUMERICAL_EXACT' in message and all(h in message for h in hashes.values())
with (D/'AUTHOR_MESSAGE.txt').open('xb') as out:out.write(raw)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
save(D/'AUTHOR_APPROVAL.json',dict(stage='FORMAL_V2_NUMERICAL_EXACT',run_id='pr113-formal-numerical-v2',**hashes,author_message=message,author_message_sha256=hashlib.sha256(message.encode('utf-8')).hexdigest(),attachment_bytes_sha256=hashlib.sha256(raw).hexdigest(),author_source=str(attachment),reviewed_commit=review,recorded_utc=now,time_semantics='Actual recording time of this newly received attached human authorization; no earlier approval asserted.'))
save(D/'PREFLIGHT.json',dict(recorded_utc=now,reviewed_commit=review,**hashes,remote_F0_authenticated=True,pinned_files_controller_will_verify=len(f0['files']),source_roles_verified=f0['source_roles'],numerical_DLLs_verified=f0['numerical_DLLs'],plan_sha256=sha(V/'PLAN.json'),slots=720,q1_first=180,registered_numeric_support_queries=10836,prior_numerical_start=False,prior_census_owned_seconds=load(root/'CENSUS_ENDED.json')['conservative_owned_bound_seconds'],free_volume_bytes=shutil.disk_usage(root.anchor).free,new_GPU_starts=0))
# Read every F0/PLAN field without dumping thousands of immutable pin entries.
print(json.dumps(dict(F0={k:v for k,v in f0.items() if k not in ('files','budget')},plan_keys=list(plan),first_slot=plan['numerical_slots'][0],last_slot=plan['numerical_slots'][-1],message_sha256=hashlib.sha256(raw).hexdigest()),ensure_ascii=False))
print('Numerical exact author receipt saved. No new native/device activity during preflight.')
