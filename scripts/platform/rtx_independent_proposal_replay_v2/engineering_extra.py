"""Exposed state checks, original observer equivalence, branch fixtures and negative cases."""
import json,shutil,subprocess
from pathlib import Path
from prepare import ROOT,STUDY,save
from engine import execute,Worker,format_prompt,prompts,now,canonical
import verify
def main():
    require=verify.require
    out=ROOT/'work/engineering-extra';out.mkdir(exist_ok=False);report={'started_utc':now(),'runs':[],'comparisons':[],'status':'STARTED'}
    for task in ['HumanEval/3','HumanEval/106']:
        tape=None;rr=[]
        for c in ['H2_P_R','R_ONLY','RTX_BATCHED_K2']:
            r=execute(task,1,c,out/'runs',tape_path=tape);report['runs'].append(r);rr.append(r);save(out/'records.json',report);require(r['status']=='VALID','engineering state execution failed')
            if c=='H2_P_R':tape=out/'runs'/r['run_id']/'tape.jsonl'
        report['comparisons'].append({'task_id':task,'H2_R_ONLY_exact':rr[0]['generated_ids']==rr[1]['generated_ids'],'H2_live_exact':rr[0]['generated_ids']==rr[2]['generated_ids'],'first_H2_live_divergence':verify.difference(rr[0]['generated_ids'],rr[2]['generated_ids'])})
        for c in ['REFERENCE_UB1','RTX_BATCHED_K2']:
            baseline=execute(task,1,c,out/'observer-off',native_debug='0');report['runs'].append(baseline);require(baseline['status']=='VALID','observer baseline failed')
            observed=rr[2] if c=='RTX_BATCHED_K2' else verify.read(ROOT/'work/reference-qualification/runs'/f'{task.replace("/","-")}-r1-REFERENCE_UB1/record.json')
            require(baseline['generated_ids']==observed['generated_ids'],'batch-debug observer changed committed IDs')
    # Construct proposals from already-exposed engineering output, never reserved/live data.
    # This tests R state branches; these fixtures are explicitly not independent predictions.
    fx=out/'constructed-branches';fx.mkdir();log=(fx/'events.jsonl').open('wb');w=Worker('R',2,fx,log)
    initial=w.call({'op':'init','formatted_prompt':format_prompt(prompts()['HumanEval/3'])});prefix=initial['committed_ids'].copy();pos=len(initial['prompt_ids'])
    reference=verify.read(ROOT/'work/reference-qualification/runs/HumanEval-3-r1-REFERENCE_UB1/generated_ids.json');cases=[]
    for j,(name,length,wrong) in enumerate([('zero_proposal',0,None),('one_accept_bonus',1,None),('accept_then_correction',2,1),('first_rejection',2,0),('all_accept_bonus',2,None)]):
        props=reference[len(prefix):len(prefix)+length].copy()
        if wrong is not None:props[wrong]=0
        q={'op':'verify','round':j,'position':pos,'pending':prefix[-1],'proposal_ids':props};v=w.call(q);cases.append({'name':name,'request':q,'response':v});prefix+=v['committed_ids'];pos=v['next_position']
    w.close();log.close()
    require(cases[0]['response']['accepted_proposals']==0 and cases[1]['response']['accepted_proposals']==1 and cases[2]['response']['accepted_proposals']==1 and cases[3]['response']['accepted_proposals']==0 and cases[4]['response']['accepted_proposals']==2,'constructed branch acceptance differs')
    save(fx/'FIXTURES.json',{'natural':False,'input':'exposed HumanEval/3','proposal_source':'new exposed engineering reference array; only constructed branch tests','cases':cases,'status':'PASS'})
    px=out/'constructed-proposer-widths';px.mkdir();log=(px/'events.jsonl').open('wb');rw=Worker('R',2,px,log);pw=Worker('P',2,px,log)
    ri=rw.call({'op':'init','formatted_prompt':format_prompt(prompts()['HumanEval/3'])});pw.call({'op':'init','formatted_prompt':format_prompt(prompts()['HumanEval/3'])});pos=len(ri['prompt_ids']);pending=ri['committed_ids'][-1];widths=[]
    for j,width in enumerate([0,1,2]):
        pp=pw.call({'op':'propose','position':pos,'pending':pending,'max_proposals':width});require(len(pp['proposal_ids'])==width,'actual P width fixture');v=rw.call({'op':'verify','round':j,'position':pos,'pending':pending,'proposal_ids':pp['proposal_ids']});pw.call({'op':'update','position':pos,'verified_batch':[pending]+pp['proposal_ids'],'retain_count':v['retain_count']});pos=v['next_position'];pending=v['committed_ids'][-1];widths.append({'requested':width,'actual':pp['proposal_ids']})
    pw.close();rw.close();log.close();save(px/'FIXTURES.json',{'status':'PASS','natural':False,'constructed_round_budget':True,'model_contexts':2,'widths':widths,'complete_scientific_conditions':0})
    # Independent file copies: mutate payload and update its local transport manifest
    # where appropriate, so rejection is not only an inventory hash comparison.
    source=out/'runs/HumanEval-3-r1-H2_P_R';neg=out/'negative-fixtures';neg.mkdir();negative=[]
    def case(name,mutate):
        dst=neg/name;shutil.copytree(source,dst);mutate(dst)
        try:verify.check_run(dst)
        except (ValueError,KeyError,IndexError) as e:negative.append({'name':name,'rejected':True,'reason':str(e)})
        else:raise RuntimeError('negative fixture accepted: '+name)
    def modified_id(d):
        p=d/'generated_ids.json';ids=verify.read(p);ids[0]+=1;save(p,ids);r=verify.read(d/'record.json');r['generated_ids']=ids;r['array_sha256']=verify.arr(ids);r['files'][p.name]={'bytes':p.stat().st_size,'sha256':verify.sha(p)};save(d/'record.json',r)
    def deleted_event(d):
        p=d/'events.jsonl';lines=p.read_bytes().splitlines(keepends=True);del lines[2];p.write_bytes(b''.join(lines));r=verify.read(d/'record.json');r['files'][p.name]={'bytes':p.stat().st_size,'sha256':verify.sha(p)};save(d/'record.json',r)
    def task(d):r=verify.read(d/'record.json');r['task_id']='HumanEval/106';save(d/'record.json',r)
    def tape(d):p=d/'tape.jsonl';b=p.read_bytes();p.write_bytes(b.replace(b'"round":0',b'"round":9',1));r=verify.read(d/'record.json');r['files'][p.name]={'bytes':p.stat().st_size,'sha256':verify.sha(p)};save(d/'record.json',r)
    def future(d):
        p=d/'tape.jsonl';lines=p.read_bytes().splitlines();o=json.loads(lines[0]);o['request']['future_prefix']=[1,2,3];o.pop('event_sha256');o['event_sha256']=verify.arr(o);lines[0]=canonical(o);p.write_bytes(b'\n'.join(lines)+b'\n');r=verify.read(d/'record.json');r['files'][p.name]={'bytes':p.stat().st_size,'sha256':verify.sha(p)};save(d/'record.json',r)
    for name,f in [('changed_committed_id',modified_id),('deleted_native_event',deleted_event),('changed_task',task),('tape_round_hash',tape),('future_answer_input',future)]:case(name,f)
    try:verify.provenance({'commit':'abc','remote_ref':'abc','remote_ack_utc':'2026-10-01T10:00:00Z'},'2026-10-01T09:59:59Z')
    except ValueError as e:negative.append({'name':'premature_live','rejected':True,'reason':str(e)})
    save(STUDY/'NEGATIVE_VALIDATION.json',{'status':'PASS','cases':negative,'formal_evidence_mutated':False})
    report.update(status='PASS',ended_utc=now(),constructed_branch_fixtures=5,constructed_P_width_fixtures=3,constructed_model_contexts=3,negative_rejections=len(negative),observer_equivalence_pairs=4)
    save(out/'records.json',report);save(STUDY/'STATE_QUALIFICATION.json',{k:v for k,v in report.items() if k!='runs'}|{'executions':len(report['runs']),'limitations':'Native LLAMA_BATCH_DEBUG logs actual prompt IDs, logical batches and physical splits. New worker records graph output shapes and sampled logits rows. Original L target full logits are not published; no claim of complete raw-logit equality between frontends.'})
    for r in report['runs'][:3]:verify.check_run(out/'runs'/r['run_id'],out/'runs/HumanEval-3-r1-H2_P_R/tape.jsonl' if r['condition']=='R_ONLY' else None)
    print('Extra engineering and negatives PASS')
if __name__=='__main__':main()
