"""Frozen stages with hard reserved forward/live gates; no selective retry."""
import argparse,json,subprocess
from pathlib import Path
from prepare import ROOT,STUDY,save
from engine import execute,now,prompts,ah,digest
DISCOVERY=['HumanEval/'+str(i) for i in [64,106,119,128,129,3,10,19,20,28,32,44]]
def difference(a,b):
    for i in range(max(len(a),len(b))):
        x=a[i] if i<len(a) else None;y=b[i] if i<len(b) else None
        if x!=y:return {'index':i,'left_id':x,'right_id':y}
    return None
def summarize(runs,pairs):
    groups={}
    for r in runs:groups[(r['task_id'],r['repetition'],r['condition'])]=r
    rows={name:[] for name in pairs}
    for task,rep,_ in groups:
        for name,(a,b) in pairs.items():
            key=(task,rep,a)
            if key not in groups or (task,rep,b) not in groups:continue
            if any(x['task_id']==task and x['repetition']==rep for x in rows[name]):continue
            x=groups[key]['generated_ids'];y=groups[(task,rep,b)]['generated_ids'];rows[name].append({'task_id':task,'repetition':rep,'exact':x==y,'first_divergence':difference(x,y)})
    stable={}
    for task,_,condition in groups:
        key=task+'|'+condition
        if key not in stable:
            arrays=[r['generated_ids'] for r in runs if r['task_id']==task and r['condition']==condition];stable[key]=len(arrays)==3 and all(a==arrays[0] for a in arrays)
    return {'pairs':{name:{'exact_pairs':sum(x['exact'] for x in data),'total_pairs':len(data),'wholly_exact_prompts':sum(all(x['exact'] for x in data if x['task_id']==t) for t in {x['task_id'] for x in data}),'prompt_count':len({x['task_id'] for x in data}),'comparisons':data} for name,data in rows.items()},'repeat_stability':stable,'all_repeat_stable':all(stable.values())}
def check_frozen(checkpoint):
    receipt=json.loads((STUDY/(checkpoint+'_REMOTE_RECEIPT.json')).read_text(encoding='utf-8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if receipt['commit']!=head or receipt['remote_ref']!=head:raise RuntimeError('execution head differs from acknowledged freeze')
    manifest=json.loads((STUDY/(checkpoint+'_MANIFEST.json')).read_text(encoding='utf-8'))
    for name,entry in manifest['files'].items():
        if digest((ROOT/name).read_bytes())!=entry['sha256']:raise RuntimeError('frozen file changed: '+name)
    return head,receipt
def run(stage):
    checkpoint={'discovery':'F0','pre-live':'F1','live':'F2'}[stage];head,receipt=check_frozen(checkpoint)
    tasks=DISCOVERY if stage=='discovery' else json.loads((STUDY/'RESERVED_SET.json').read_text(encoding='utf-8'))['selected_task_ids']
    conditions={'discovery':['H2_P_R','R_ONLY','RTX_BATCHED_K2'],'pre-live':['REFERENCE_UB1','H2_P_R','R_ONLY'],'live':['RTX_BATCHED_K2']}[stage]
    phase=ROOT/'work'/stage;phase.mkdir(exist_ok=False)
    records={'stage':stage,'execution_head':head,'freeze_ack_utc':receipt['remote_ack_utc'],'started_utc':now(),'status':'STARTED','runs':[],'planned_executions':len(tasks)*3*len(conditions)};save(phase/'records.json',records)
    for task in tasks:
        for rep in [1,2,3]:
            tape=None
            for c in conditions:
                r=execute(task,rep,c,phase/'runs',tape_path=tape);records['runs'].append(r);save(phase/'records.json',records)
                save(ROOT/'work/progress.json',{'stage':stage,'count':len(records['runs']),'total':records['planned_executions'],'utc':now(),'latest_status':r['status']})
                if r['status']!='VALID':records.update(status='INCOMPLETE_OPERATIONAL_FAILURE',ended_utc=now());save(phase/'records.json',records);return
                if c=='H2_P_R':tape=phase/'runs'/r['run_id']/'tape.jsonl'
    records.update(status='COMPLETE',ended_utc=now());save(phase/'records.json',records)
    if stage=='discovery':
        analysis=summarize(records['runs'],{'H2_live':('H2_P_R','RTX_BATCHED_K2'),'H2_R_ONLY':('H2_P_R','R_ONLY')});passed=all(p['exact_pairs']==36 for p in analysis['pairs'].values()) and analysis['all_repeat_stable'];analysis['status']='DISCOVERY_QUALIFIED' if passed else 'DISCOVERY_NOT_QUALIFIED';analysis['reserved_forward_count']=0;save(STUDY/'DISCOVERY_REPORT.json',analysis)
    elif stage=='pre-live':
        analysis=summarize(records['runs'],{'H2_R_ONLY':('H2_P_R','R_ONLY')});passed=analysis['pairs']['H2_R_ONLY']['exact_pairs']==72 and analysis['all_repeat_stable'];analysis['status']='PRE_LIVE_QUALIFIED' if passed else ('REPEAT_INSTABILITY' if not analysis['all_repeat_stable'] else 'REPLAY_QUALIFICATION_FAILED');save(STUDY/'PRE_LIVE_QUALIFICATION.json',analysis)
        if passed:
            rows=[];g={(r['task_id'],r['repetition'],r['condition']):r for r in records['runs']}
            for task in tasks:
                for rep in [1,2,3]:
                    triple={c:g[(task,rep,c)] for c in conditions};row={'task_id':task,'repetition':rep,'input_sha256':triple['H2_P_R']['input_sha256'],'prompt_array_sha256':triple['H2_P_R']['prompt_array_sha256'],'tape_sha256':triple['H2_P_R']['tape_sha256'],'runs':{c:{'run_id':r['run_id'],'generated_ids':r['generated_ids'],'array_sha256':r['array_sha256']} for c,r in triple.items()},'predicted_reference_exact':triple['REFERENCE_UB1']['generated_ids']==triple['H2_P_R']['generated_ids'],'predicted_first_divergence':difference(triple['REFERENCE_UB1']['generated_ids'],triple['H2_P_R']['generated_ids'])};rows.append(row)
            save(STUDY/'RESERVED_PREDICTIONS.json',{'schema':'RTX_H2_V2.sealed_predictions','created_utc':now(),'live_started':False,'array_digest_contract':'SHA256 of UTF-8 json.dumps(ids,separators=(comma,colon)); file digest is distinct','rows':rows})
    else:
        pre=json.loads((ROOT/'work/pre-live/records.json').read_text(encoding='utf-8'));analysis=summarize(pre['runs']+records['runs'],{'H2_live':('H2_P_R','RTX_BATCHED_K2'),'R_ONLY_live':('R_ONLY','RTX_BATCHED_K2'),'reference_live':('REFERENCE_UB1','RTX_BATCHED_K2'),'H2_R_ONLY':('H2_P_R','R_ONLY')});divergent={r['task_id'] for r in analysis['pairs']['reference_live']['comparisons'] if not r['exact']};analysis['reference_divergent_prompts']=len(divergent)
        analysis['status']='PROSPECTIVE_REPLAY_MISMATCH' if analysis['pairs']['H2_live']['exact_pairs']!=72 else ('PROSPECTIVE_REPLAY_MATCH_DISCRIMINATING' if divergent else 'PROSPECTIVE_REPLAY_MATCH_NONDISCRIMINATING');save(STUDY/'FORMAL_REPORT.json',analysis)
    print(stage+' complete')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['discovery','pre-live','live']);a=p.parse_args();run(a.stage)
