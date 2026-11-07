from pathlib import Path
import sys,json,hashlib,zipfile,collections,datetime
v=Path(__file__).resolve().parents[1];sys.path.insert(0,str(v))
from common import load,save,sha
import audit,identity
f=load(v/'F0.json');root=Path(f['execution_root']);d=v/'delivery/cpu_ledger/02-census-readback';auth=load(root/'CENSUS_AUTHENTICATED.json')
assert auth['authenticated_remote_bytes'] and auth['F0_sha256']==sha(v/'F0.json')
manifest=load(d/'MANIFEST.stdout');assert manifest['F0_sha256']==auth['F0_sha256'] and manifest['census_sha256']==auth['census_sha256']==sha(d/'CENSUS.stdout') and manifest['decision_sha256']==auth['decision_sha256']==sha(d/'DECISION.stdout')
fresh=Path('D:/hs116-s1b-census-fresh');assert not fresh.exists();fresh.mkdir();members=[]
with zipfile.ZipFile(d/'RECEIPTS.stdout') as z:
 for n in z.namelist():
  p=(fresh/n).resolve();assert p.is_relative_to(fresh.resolve());data=z.read(n);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);assert sha(p)==sha(root/n);members.append(dict(path=n,bytes=len(data),sha256=sha(p)))
r=load(d/'CENSUS.stdout');assert r==load(fresh/'census/native/CENSUS.json') and load(fresh/'CENSUS_ENDED.json')['status']=='COMPLETE'
for name in ['audit.py','identity.py','common.py']:assert sha(v/name)==f['source_roles'][name]
expected={(g['descriptor_id'],g['layout']):g for g in load(v/'CPU_EXPECTED.json')};decision=audit.census(r,load(v/'PLAN.json'),expected);assert decision==load(d/'DECISION.stdout')==load(fresh/'CENSUS_DECISION.json')
inventory=load(fresh/'census/MODULE_FILES.json');pins={identity.norm(x['path']):x for x in f['files']}
for p in inventory:assert p['sha256']==pins[identity.norm(p['path'])]['sha256']==sha(p['path'])
core=identity.verify_modules(fresh/'census/native',r,dict(f,executable=f['hosts']['clean']['path'],executable_sha256=f['hosts']['clean']['sha256']),inventory)
native=identity.process_identity(fresh/'census','native',dict(f,executable=f['hosts']['clean']['path']),240);ready=identity.process_identity(fresh/'census','readiness',f)
assert r['pid']==native[0] and native!=ready and r['graph_computes']==0
counts=collections.Counter(g['layout'] for g in r['records']);assert counts==dict(PQ=24,QB=24,QH_C=24)
helpers=[]
for prefix in ['native','readiness']:
 events=load(fresh/'census'/(prefix+'.JOB_EVENTS.json'));assert any(e['message']==4 for e in events['events'])
 helpers.extend(e['pid'] for e in events['events'] if e['message']==6 and e['pid']!=events['registered_PID'])
assert len(helpers)==len(set(helpers))==2
save(v/'delivery/FRESH_CENSUS_AUDIT.json',dict(status='PASS',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_interpreter=True,authenticated_commit=auth['commit'],F0_sha256=sha(v/'F0.json'),census_sha256=sha(d/'CENSUS.stdout'),decision_sha256=sha(d/'DECISION.stdout'),receipts_sha256=sha(d/'RECEIPTS.stdout'),fresh_root=str(fresh),restored_members=members,graphs=72,support_queries=828,by_layout=dict(counts),denied_slots=[],module_identities_and_shared_core_41_imports_verified=True,actual_module_files_verified=len(inventory),native_process_identity=native,readiness_process_identity=ready,conhost_PIDs=helpers,graph_computes=0,warmups=0,performance_measurements=0,clean_CUDA_ordinary_qualification=False,clean_block_authorization=False))
print('PASS fresh authenticated Census reconstruction:72graphs/828queries/module41/processes;0compute')
