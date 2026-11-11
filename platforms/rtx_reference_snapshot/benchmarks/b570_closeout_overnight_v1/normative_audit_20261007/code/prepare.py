from pathlib import Path
import json,hashlib,shutil,subprocess
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).parent;BASE=Path('C:/hs/b570-closeout-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
assert not (ROOT/'AMENDMENT.json').exists()
shutil.copytree(BASE/'src',ROOT/'src');shutil.copy2(BASE/'runner.py',ROOT/'runner.py')
# Capture-only output observation: never edits logits, sampling, forwards or state.
p=ROOT/'src/observer.h';s=p.read_text(encoding='utf-8')
s=s.replace('int target_calls=0', 'std::vector<float> audit_pending_logits;\n    int target_calls=0',1)
s=s.replace('path=req.at("output");','audit_pending_logits.clear();path=req.at("output");',1)
s=s.replace('bytes(".pending_logits.f32",logits);','bytes(".pending_logits.f32",logits);if(std::getenv("HS_AUDIT_FULL_LOGITS"))audit_pending_logits=logits;',1)
needle='        if(instrument) commits.push_back('
assert s.count(needle)==1
s=s.replace(needle,'''        if(instrument && std::getenv("HS_AUDIT_FULL_LOGITS")) {
            const int nv=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(c)));
            const float * row=commits.empty() && !transfer.is_null()?audit_pending_logits.data():llama_get_logits_ith(c,idx);
            if(!row || (commits.empty() && !transfer.is_null() && audit_pending_logits.size()!=size_t(nv)))throw std::runtime_error("Audit logits unavailable");
            bytes(".decision-"+std::to_string(commits.size())+".f32",std::vector<float>(row,row+nv));
        }
'''+needle,1)
p.write_text(s,encoding='utf-8',newline='\n')
p=ROOT/'runner.py';s=p.read_text(encoding='utf-8');needle="env.update(HS_PREFILL_OUTPUT=str(self.dir/'initial.json'),HS_PREFILL_UB=str(config['prefill']))";assert s.count(needle)==1;s=s.replace(needle,needle+"\n  if config.get('audit_full_logits'):env['HS_AUDIT_FULL_LOGITS']='1'",1);p.write_text(s,encoding='utf-8',newline='\n')
inputs=load(BASE/'INPUTS.json');tasks={t['id']:t for v in inputs.values() for t in v}
old=load(BASE/'dependencies/B570/HISTORICAL_EXPECTED.json')
oldinputs=load(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
bridge=[dict(id=t,prompt_ids=load(oldinputs[t]['ids'])) for t in ['HumanEval/134','HumanEval/58']]
def cfg(label,native=False,k=2,ub=1,prefill=128,**kw):return dict(label=label,native=native,k=k,ub=ub,prefill=prefill,cap=128,capture=True,audit_full_logits=True,**kw)
modes=[cfg('R_reference',ub=128,plain=True),cfg('T_matched',matched=True),cfg('N0_ordinary',True,prefill=1),cfg('N1_repaired',True)]
save(ROOT/'BRIDGE_SCHEDULE.json',[dict(config=c,inputs=bridge) for c in modes])
# Original C-only selector narrowed prompt section 9. Expand to complete B/C/E
# failures; no speed sorting. First two distinct task/config pairs at k1/UB2
# are /42 then /145 in the frozen pilot input order.
selected=[]
er=[r for r in load(BASE/'E_PILOT_RESULTS.json') if not r['warm']]
br=[r for r in load(BASE/'B_RESULTS.json') if not r['warm']]
for k,u in sorted({(r['config']['k'],r['config']['ub']) for r in er+br if r['config']['native']}):
 for t in inputs['shared']+inputs['unused']+inputs['pilot_old']:
  cand=[r for r in er+br if r['task']==t['id'] and r['config']['native'] and r['config']['prefill']==128 and (r['config']['k'],r['config']['ub'])==(k,u)]
  ref=[r for r in br if r['task']==t['id'] and r['config']['label']=='R_reference']
  reference=ref[0]['endpoint']['ids'] if ref else old[t['id']+'/R/1']['ids']
  if cand and any(r['endpoint']['ids']!=reference for r in cand):selected.append(dict(task=t['id'],k=k,ub=u,cap=128,original_units=[r['unit_id'] for r in cand]));
  if len(selected)==2:break
 if len(selected)==2:break
assert [(p['task'],p['k'],p['ub']) for p in selected]==[('HumanEval/42',1,2),('HumanEval/145',1,2)]
sessions=[]
for pi,pair in enumerate(selected):
 modes=[cfg('R_reference',ub=128,plain=True),cfg('T_matched',ub=pair['ub'],matched=True),cfg('M_failed',True,k=pair['k'],ub=pair['ub']),cfg('N1_repaired',True),cfg('M_ordinary',True,k=pair['k'],ub=pair['ub'],prefill=pair['ub'],plain=True)]
 sessions.extend(dict(config=dict(c,pair=pi),inputs=[tasks[pair['task']]]) for c in modes)
save(ROOT/'MECHANISM_SUPPLEMENT_SCHEDULE.json',sessions)
start=datetime.now(timezone.utc);window=dict(utc=start.isoformat(),new_experiment_stop_utc=(start+timedelta(hours=3)).isoformat(),deadline_utc=(start+timedelta(hours=4,minutes=15)).isoformat())
save(ROOT/'STARTUP.json',window)
save(ROOT/'AMENDMENT.json',dict(**window,study='B570_CLOSEOUT_AUDIT_V1',authorization='User: 做一次实验规范性审核...如果有欠缺，就继续补',reason='Prompt section 9 was narrowed to C-only failures. Preserve original scientific batch; add bounded natural parents on first two failed pairs in frozen width/cap/task order including E. No performance samples, selection tuning or replacement of failures.',prior_science_head='bd5e3963757857f7ce5cd6a7a87bb04d6eb48d8d',prior_archive_sha256=load(BASE/'ARCHIVE_RESTORE.json')['archive_sha256'],prior_root=str(BASE),selection=selected,planned_bridge=8,planned_diagnostic_parents=10,planned_warm=14,planned_auxiliary_forward=0,state_cross='NOT_IMPLEMENTED: natural mid-trajectory target/draft/post-sample sampler checkpoint absent in these frontends; no causal cross claimed',instrumentation='Read-only full float32 target logits at every natural commit; capture-only timings. No oracle input/reference forcing or arithmetic/ABI/kernel/loop modifications.',before_sources={str(p.relative_to(BASE)):sha(p) for p in list((BASE/'src').glob('*'))+[BASE/'runner.py']},after_sources={str(p.relative_to(ROOT)):sha(p) for p in list((ROOT/'src').glob('*'))+[ROOT/'runner.py']},models=load(BASE/'PROTOCOL.json')['models'],original_numerical_assets=load(BASE/'EXECUTION_FREEZE.json')['numerical_assets']))
save(ROOT/'HISTORICAL_EXPECTED.json',old)
shutil.copy2(BASE/'TOKENIZATION_PROOF.json',ROOT/'TOKENIZATION_PROOF.json')
(ROOT/'build/Release').mkdir(parents=True)
for p in (BASE/'build/Release').glob('*.dll'):shutil.copy2(p,ROOT/'build/Release'/p.name)
subprocess.run(['git','init','--quiet',str(ROOT)],check=True);subprocess.run(['git','config','core.autocrlf','false'],cwd=ROOT,check=True)
(ROOT/'.gitignore').write_text('build/\nraw/\nsessions/\narchive/\n__pycache__/\n*.log\nLOCK.json\nSTATUS.json\n',encoding='ascii')
subprocess.run(['git','add','.'],cwd=ROOT,check=True);subprocess.run(['git','commit','-m','Freeze bounded B570 normative audit supplement and read-only logit observer before inference'],cwd=ROOT,check=True)
print({'status':'FROZEN','selection':selected,'planned_requests':18,'warm':14},flush=True)
