"""Zero-forward construction and identity audit of the already exposed 56-task panel."""
from pathlib import Path
import json,hashlib
R=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prefpath=Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json');pref=load(prefpath);hist=load(R/'dependencies/HISTORICAL_EXPECTED.json');old=load(R/'dependencies/INPUTS.json');panel=[];refs={}
for task,item in pref.items():
 ids=load(item['ids']);text=Path(item['text']).read_text(encoding='utf8');p=dict(id=task,prompt_ids=ids,formatted_prompt=text,cap=128,cohort='old_exposed_HumanEval24',identity=dict(manifest_sha256=sha(prefpath),prompt_text_sha256=sha(item['text']),prompt_ids_sha256=sha(item['ids'])))
 a=[hist[task+'/R/'+str(round)] for round in [1,2,3]];assert all(v['ids']==a[0]['ids'] and v['eog']==a[0]['eog'] and v['endpoint']==a[0]['endpoint'] for v in a)
 refs[task]=dict(ids=a[0]['ids'],eog=a[0]['eog'],reason='CAP' if a[0]['endpoint']=='CAP128' else a[0]['endpoint'],source_endpoint_literal=a[0]['endpoint'],source='immutable inherited scalar R complete cap128 exports',manifest_sha256=sha(R/'dependencies/HISTORICAL_EXPECTED.json'));panel.append(p)
core=Path(load(R/'STAGE0.json')['restores'][0]['path']);records=[(p,load(p)) for p in (core/'raw').glob('*/RESULT.json')]
for cohort in ['shared','unused']:
 for inp in old[cohort]:
  task=inp['id'];rs=[(p,r) for p,r in records if r['unit_id'].startswith('B/') and not r['warm'] and r['task']==task and r['config']['label']=='R_reference'];assert len(rs)==4
  ep=rs[0][1]['endpoint'];assert all(r['endpoint']==ep for _,r in rs)
  rawpath=core/next(f for f in rs[0][1]['files'] if f.endswith('/capture.json'));raw=load(rawpath);assert raw['prompt_ids']==inp['prompt_ids'] and ep['raw_suffix']==0 and raw['ids']==ep['ids']
  p=dict(inp);p['cohort']='old_exposed_shared_MBPP24' if cohort=='shared' else 'old_exposed_MBPP8';p['exposure']='already exposed in PR63';p['identity']=dict(input_manifest_sha256=sha(R/'dependencies/INPUTS.json'),source_raw_sha256=sha(rawpath));panel.append(p)
  refs[task]=dict(ids=ep['ids'],eog=ep['eog'],reason=ep['reason'],source='restored immutable PR63 paid ordinary R; all four rounds stable',source_units=[r['unit_id'] for _,r in rs],source_raw_sha256=sha(rawpath),archive_sha256=load(R/'STAGE0.json')['restores'][0]['sha256'])
assert len(panel)==56==len({p['id'] for p in panel})==len(refs)
for p in panel:
 assert len(p['prompt_ids'])+128+2+4<=1024 and len(refs[p['id']]['ids'])<=128
for name,data in [('D_INPUTS.json',panel),('D_REFERENCES.json',refs)]:
 (R/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(R/'D_INPUT_IDENTITY_AUDIT.json').write_text(json.dumps(dict(status='PASS',tasks=56,groups={'old_HE':24,'shared_MBPP':24,'exposed_old_MBPP8':8},reference_round_stability=True,input_reference_identity=True,paid_new_references=0,model_requests=0,scope='All already exposed; old R used only offline, never a fresh cost baseline'),indent=2)+'\n',encoding='utf8')
print('56 exposed input identities and full old R references verified, zero model forwards')
