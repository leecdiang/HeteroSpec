from pathlib import Path
import json,datetime,hashlib,subprocess
R=Path(__file__).parent;G='C:/Users/DIANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def load(n):return json.loads((R/n).read_text(encoding='utf8'))
def sha(n):return hashlib.sha256((R/n).read_bytes()).hexdigest()
assert load('C_VERIFICATION.json')['status']=='PASS' and load('C_VERIFICATION.json')['scientific_gate']=='PASS'
panel=load('D_INPUTS.json');assert len(panel)==56
manifest=dict(units=[dict(unit_id=f'D/{round}/{p["id"]}',task=p['id'],round=round) for round in [1,2] for p in panel],config=dict(label='CANONICAL_PREFILL_INPLACE_PHASE_BINDING',native=True,k=2,ub=1,prefill=128,cap=128,capture=False,plain=True),qualification='full canonical cap128 IDs/EOG/length/endpoint versus frozen old ordinary R, complete untrimmed raw retained; two-round raw repeat stability',stop_rule='First candidate qualification failure gates all further candidate work and E; full frozen matrix includes explicit unexecuted rows. No replacements/retries.',tasks_already_exposed=56,nonwarm_max=112)
(R/'D_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
files={n:sha(n) for n in ['D_INPUTS.json','D_REFERENCES.json','D_INPUT_IDENTITY_AUDIT.json','D_MANIFEST.json','run_D.py','validate_D.py','prepare_D.py','candidate_runner.py','C_FREEZE.json','C_VERIFICATION.json']}
files.update(load('C_FREEZE.json')['binaries'])
if (R/'D_ENDPOINT_NAMESPACE_AMENDMENT.json').exists():
 for n in ['D_ENDPOINT_NAMESPACE_AMENDMENT.json','D_REFERENCES_PRE_NAMESPACE_CORRECTION.json','D_FREEZE_PRE_NAMESPACE_CORRECTION.json','D_QUALIFICATION_PRE_NAMESPACE_CORRECTION.json','correct_D_endpoint_namespace.py']:
  files[n]=sha(n)
freeze=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,unchanged_candidate_family=True,C_actual_binary_epoch='3be8db4d6c98c9466dd61414f8ee9b7dc4b3e4d6')
(R/'D_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
subprocess.run([G,'add','D_INPUTS.json','D_REFERENCES.json','D_INPUT_IDENTITY_AUDIT.json','D_MANIFEST.json','D_FREEZE.json','run_D.py','validate_D.py','prepare_D.py','freeze_D.py','C_VERIFICATION.json'],cwd=R,check=True)
if (R/'D_ENDPOINT_NAMESPACE_AMENDMENT.json').exists():subprocess.run([G,'add','D_ENDPOINT_NAMESPACE_AMENDMENT.json','D_REFERENCES_PRE_NAMESPACE_CORRECTION.json','D_FREEZE_PRE_NAMESPACE_CORRECTION.json','D_QUALIFICATION_PRE_NAMESPACE_CORRECTION.json','correct_D_endpoint_namespace.py','audit_D_stop.py'],cwd=R,check=True)
subprocess.run([G,'commit','-m','Freeze 56 exposed task two-round qualification of unchanged candidate'],cwd=R,check=True)
print(subprocess.check_output([G,'rev-parse','HEAD'],cwd=R,text=True).strip())
