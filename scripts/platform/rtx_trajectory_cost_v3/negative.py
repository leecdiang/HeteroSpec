"""Independent temporary-copy corruption cases; no model process or formal evidence mutation."""
import copy,hashlib,itertools,json,random,re,shutil,tempfile
from pathlib import Path
from prepare import ROOT,STUDY,save,now
import verify_common as v
import verify_B
import guards
def main():
    out=ROOT/'work/negative-fixtures';out.mkdir(exist_ok=False);cases=[]
    base=ROOT/'work/engineering-attempt1/runs/HumanEval-3-r1-H2_P_R';eog=ROOT/'work/engineering-extra/endpoints/SYNTH_EOG-r1-H2_P_R';timer=ROOT/'work/engineering-attempt1/runs/HumanEval-3-r1-E_TIMER_REFERENCE_UB1'
    def refresh(d):
        r=v.read(d/'record.json')
        for n in r['files']:r['files'][n]={'bytes':(d/n).stat().st_size,'sha256':v.sha(d/n)}
        if (d/'tape.jsonl').exists():r['tape_sha256']=v.sha(d/'tape.jsonl')
        save(d/'record.json',r)
    def changed_array(d,truncate=False):
        r=v.read(d/'record.json');ids=r['generated_ids'].copy()
        if truncate:ids.pop()
        else:ids[0]+=1
        r['generated_ids']=ids;r['array_sha256']=v.arr(ids);save(d/'record.json',r);save(d/'generated_ids.json',ids)
    def identity(d,key,value):
        r=v.read(d/'record.json');r[key]=value;r['run_id']=r['task_id'].replace('/','-')+'-r'+str(r['repetition'])+'-'+r['condition'];save(d/'record.json',r)
    def tape(d,future=False,rechain=False):
        p=d/'tape.jsonl';rows=[json.loads(x) for x in p.read_bytes().splitlines()]
        if future:rows[0]['request']['future_answer_ids']=[1,2,3]
        else:rows[0]['round']=9
        if rechain:
            previous='0'*64
            for row in rows:
                row.pop('event_sha256');row['previous_event_hash']=previous;row['event_sha256']=v.arr(row);previous=row['event_sha256']
        p.write_bytes(b''.join(json.dumps(x,separators=(',',':')).encode()+b'\n' for x in rows))
    def timer_change(d,kind):
        p=d/'stderr.log';b=p.read_bytes()
        if kind=='missing':b=re.sub(rb'HS_TIMER [^\r\n]*\r?\n?',b'',b)
        else:
            m=re.search(rb'HS_TIMER start_qpc=(\d+) end_qpc=(\d+)',b);b=b[:m.start()]+b'HS_TIMER start_qpc='+m[2]+b' end_qpc='+m[1]+b[m.end():]
        p.write_bytes(b)
    def evidence_case(name,source,change):
        d=out/name;shutil.copytree(source,d);change(d);refresh(d)
        try:v.check_run(d,metadata=STUDY)
        except (ValueError,KeyError,IndexError,TypeError) as e:cases.append({'name':name,'rejected':True,'reason':str(e),'transport_hashes_refreshed':True,'fixture_path':d.relative_to(ROOT).as_posix()})
        else:raise RuntimeError('negative evidence accepted: '+name)
    evidence_case('changed_committed_id',base,lambda d:changed_array(d))
    evidence_case('truncated_inclusive_EOG',eog,lambda d:changed_array(d,True))
    evidence_case('task_swap',base,lambda d:identity(d,'task_id','HumanEval/106'))
    evidence_case('repetition_swap',base,lambda d:identity(d,'repetition',2))
    evidence_case('tape_hash_damage',base,lambda d:tape(d))
    evidence_case('tape_round_rehashed',base,lambda d:tape(d,rechain=True))
    evidence_case('future_answer_field_rehashed',base,lambda d:tape(d,future=True,rechain=True))
    evidence_case('missing_native_timer',timer,lambda d:timer_change(d,'missing'))
    evidence_case('reverse_native_timer',timer,lambda d:timer_change(d,'reverse'))
    try:v.unique([{'run_id':'duplicate'},{'run_id':'duplicate'}])
    except ValueError as e:cases.append({'name':'duplicate_run','rejected':True,'reason':str(e),'constructed_schema_fixture':True})
    else:raise RuntimeError('duplicate accepted')
    # Synthetic state fixtures represent validated earlier checkpoints, and omit F2.
    # They are not acknowledgements and are never placed in real study metadata.
    fake=out/'state-fixture';fake.mkdir();dummy='a'*40;stamp='2000-01-01T00:00:00+00:00';p=v.read(STUDY/'JOINT_PROTOCOL.json')
    for name,obj in [('JOINT_PROTOCOL.json',p),('AUTHORIZATION.json',{'instruction':'EXECUTE_FROZEN','reviewed_source_sha':dummy}),('F0_MANIFEST.json',{'files':{}}),('F0_REMOTE_RECEIPT.json',{'synthetic_fixture':True,'commit':dummy,'remote_ref':dummy,'remote_ack_utc':stamp,'retrieved_files':{'synthetic':True},'full_retrieval_verified':True}),('B_START_REMOTE_RECEIPT.json',{'synthetic_fixture':True,'commit':dummy,'remote_ref':dummy,'remote_ack_utc':stamp,'retrieved_files':{'synthetic':True},'full_retrieval_verified':True})]:save(fake/name,obj)
    save(fake/'SYNTHETIC_TEST_STATE.json',{'test_only':True,'not_a_remote_receipt_or_authorization':True,'purpose':'earlier checkpoint prerequisites are assumed in this F2 state-machine test; real metadata rejects synthetic_fixture receipts'})
    for phase,cond in [('A_LIVE','RTX_BATCHED_K2'),('B_FORMAL','REFERENCE_UB1')]:
        import verify_joint
        try:verify_joint.launch_order(fake,phase,now())
        except ValueError as e:independent_reason=str(e)
        else:raise RuntimeError('independent chronology accepted premature phase')
        try:guards.authorize(p['A']['task_ids'][0],cond,phase,fake,ROOT)
        except (RuntimeError,FileNotFoundError) as e:
            v.require('F2' in str(e),'state fixture rejected before reaching intended F2 guard');cases.append({'name':'premature_'+phase,'rejected':True,'reason':str(e),'independent_reason':independent_reason,'synthetic_checkpoint_fixture':True,'process_launched':False})
        else:raise RuntimeError('premature phase accepted')
    # Statistical fixtures are explicitly synthetic (no HumanEval/model output).
    cs=p['B']['conditions'];tasks=['SYNTH_STATS_'+str(i) for i in range(24)];sp={'task_ids':tasks,'conditions':cs};orders=[list(x) for x in itertools.permutations(cs) for _ in range(12)];random.Random(2026100103).shuffle(orders)
    schedule=[{'block':i,'task_id':t,'repetition':r,'order':orders[i]} for i,(t,r) in enumerate(itertools.product(tasks,[1,2,3]))];rows=[]
    for b in schedule:
        for c in b['order']:
            ms=(32+int(b['task_id'].rsplit('_',1)[1])+b['repetition'])*[1,1.5,2][cs.index(c)]
            rows.append({'task_id':b['task_id'],'repetition':b['repetition'],'canonical_condition':c,'run_id':b['task_id']+'-r'+str(b['repetition'])+'-'+c,'generated_ids':[100,101,102],'timer':{'milliseconds':ms},'termination':'EOS','fixture':True})
    expected=verify_B.calculate(rows,sp,schedule);save(out/'STATISTICAL_FIXTURE.json',{'not_model_outputs':True,'rows':rows,'protocol':sp,'schedule':schedule})
    def statistic_case(name,actual,expected):
        try:verify_B.check_numbers(actual,expected)
        except ValueError as e:cases.append({'name':name,'rejected':True,'reason':str(e),'synthetic_statistical_fixture':True})
        else:raise RuntimeError('negative statistic accepted '+name)
    wrong=copy.deepcopy(expected);wrong['paths'][cs[1]]['speedup']=1/wrong['paths'][cs[1]]['speedup'];statistic_case('wrong_ratio_direction',wrong,expected)
    blocked_rows=copy.deepcopy(rows);next(x for x in blocked_rows if x['canonical_condition']==cs[1])['generated_ids']=[999,101,102];blocked=verify_B.calculate(blocked_rows,sp,schedule)
    v.require(blocked['paths'][cs[1]]['status']=='BLOCKED' and blocked['paths'][cs[1]]['speedup'] is None and blocked['paths'][cs[2]]['status']=='QUALIFIED','independent per-path gate fixture')
    wrong=copy.deepcopy(blocked);wrong['paths'][cs[1]]['speedup']=2;wrong['paths'][cs[1]]['CI']=[1.9,2.1];statistic_case('BLOCKED_written_as_speedup',wrong,blocked)
    wrong=copy.deepcopy(expected);wrong['paths'][cs[1]]['total_pairs']=144;statistic_case('wrong_gate_denominator',wrong,expected)
    save(STUDY/'NEGATIVE_VALIDATION.json',{'status':'PASS','utc':now(),'cases':cases,'formal_evidence_mutated':False,'model_processes':0,'statistical_fixture_prompts_are_synthetic':True});print('Independent negative cases rejected',len(cases),flush=True)
if __name__=='__main__':main()
