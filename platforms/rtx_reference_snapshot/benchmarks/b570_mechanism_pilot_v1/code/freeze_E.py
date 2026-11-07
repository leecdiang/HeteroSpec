from pathlib import Path
import json,datetime,hashlib,subprocess
R=Path(__file__).parent;G='C:/Users/DIANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def load(n):return json.loads((R/n).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert load('D_VERIFICATION.json')['status']=='PASS' and load('D_VERIFICATION.json')['scientific_gate']=='PASS'
panel=load('E_INPUTS.json');assert len(panel)>=8
base=dict(prefill=128,cap=128,capture=False,plain=True)
candidate=dict(base,label='candidate',native=True,k=2,ub=1,executable=str(R/'candidate-build/Release/b570-candidate-native.exe'))
matched=dict(base,label='matched_target',native=False,ub=1,executable=str(R/'candidate-build/Release/b570-candidate-target.exe'))
reference=dict(base,label='ordinary_R',native=False,ub=128,executable='C:/hs/b570-closeout-v1/build/Release/b570-closeout-target.exe')
n1=dict(base,label='old_N1',native=True,k=2,ub=1,executable='C:/hs/b570-closeout-v1/build/Release/b570-closeout-native.exe');n1.pop('plain')
modes=[reference,matched,candidate,n1];sessions=[];bridge=[]
for round in [1,2]:
 conf=dict(matched,label='matched_bridge',round=round,capture=round==1)
 bridge.append(dict(config=conf,units=[dict(unit_id=f'E/BRIDGE/{round}/{t}',task=t) for t in ['HumanEval/42','HumanEval/145','HumanEval/134','MBPP/72']]))
 order=modes if round==1 else list(reversed(modes))
 for index,mode in enumerate(order):
  offset=((round-1)*7+index*3)%len(panel);sequence=panel[offset:]+panel[:offset];conf=dict(mode,round=round)
  sessions.append(dict(config=conf,hash_rotation_offset=offset,units=[dict(unit_id=f'E/FORMAL/{round}/{conf["label"]}/{p["id"]}',task=p['id']) for p in sequence]))
manifest=dict(bridge_sessions=bridge,formal_sessions=sessions,formal_tasks=len(panel),formal_max=len(panel)*8,bridge_max=8,total_nonwarm_max=8+len(panel)*8,qualification='candidate and matched target all complete IDs/EOG/length/endpoints equal paid native R in both rounds; R and each mode repeated raw stable',costs='unadjusted generation, whole and actual high-resolution host E2E; online phase reserve/reset/sync/draft/KV mutations all included; cold session load/cleanup and charged warmups separately disclosed',ratios='baseline/candidate; per-task two-round median costs then ratios then task GM; per-round directions also reported',gate=dict(generation_GM_min=1.05,whole_GM_min=1.03,both_rounds_faster=True),no_third_round_or_candidate_changes=True,no_output_based_selection=True)
(R/'E_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
files={n:sha(R/n) for n in ['E_MANIFEST.json','E_INPUTS.json','E_EXPOSURE_AUDIT.json','E_EXPOSURE_CATALOG.json','E_BUDGET_AMENDMENT.json','E_TOKENIZATION_BINDINGS.json','E_REMOTE_SNAPSHOT.json','formal_runner.py','prepare_E_runner.py','prepare_E.py','run_E.py','validate_E.py','validate_E_bridge.py','C_FREEZE.json','D_VERIFICATION.json','DEV_INPUTS.json','HISTORICAL_PARENTS.json']}
files.update(load('C_FREEZE.json')['binaries'])
for conf in modes:files[conf['executable']]=sha(conf['executable'])
freeze=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,unchanged_C_candidate=True,actual_new_source_family_count=1,new_input_output_before_freeze=0,old_R_and_N1_runtime='original published DLLs, hash bound external dependencies',session_configuration_order=[(s['config']['round'],s['config']['label']) for s in sessions])
(R/'E_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
subprocess.run([G,'add','E_MANIFEST.json','E_INPUTS.json','E_EXPOSURE_AUDIT.json','E_EXPOSURE_CATALOG.json','E_BUDGET_AMENDMENT.json','E_TOKENIZATION_BINDINGS.json','formal_runner.py','prepare_E_runner.py','prepare_E.py','run_E.py','validate_E.py','validate_E_bridge.py','E_FREEZE.json','freeze_E.py','D_VERIFICATION.json','E_REMOTE_SNAPSHOT.json'],cwd=R,check=True)
subprocess.run([G,'commit','-m','Freeze accessible-unused balanced confirmation with prepaid matched capture bridge'],cwd=R,check=True)
print(subprocess.check_output([G,'rev-parse','HEAD'],cwd=R,text=True).strip())
