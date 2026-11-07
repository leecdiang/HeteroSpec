"""Audit all complete native runs and the state/current-call matrix."""
import array, csv, hashlib, json, math
from pathlib import Path
from parse_state import State,compare

HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
def logits(p):
    b=p.read_bytes();a=array.array('f',b);assert len(a)==151936 and all(math.isfinite(v) for v in a)
    top=sorted(range(len(a)),key=lambda i:a[i],reverse=True)[:2]
    return b,a,{'top1':top[0],'top2':top[1],'score1':a[top[0]],'score2':a[top[1]],'margin':a[top[0]]-a[top[1]]}
def main():
    out=HERE/'generated/analysis';out.mkdir(exist_ok=True)
    engineering=[read(p) for p in sorted((HERE/'runs/engineering').glob('*/RESULT.json'))]
    formal=[(p.parent,read(p)) for p in sorted((HERE/'runs/formal').glob('*/RESULT.json'))]
    assert len(engineering)==12 and len(formal)==24
    for d,r in formal:
        assert r['valid'] and r['historical_equal'] and r['same_path_natural_decision_equal']
        assert all(sha(d/name)==h for name,h in r['files'].items())
    rows=[];kv=[];effects=[]
    for task in [15,25,18,31]:
        for rep in range(1,4):
            pair=[(d,r) for d,r in formal if r['task']==task and r['repetition']==rep]
            pair.sort(key=lambda x:x[1]['condition']);assert len(pair)==2
            da,ra=pair[0];db,rb=pair[1];ca=ra['checkpoint'];cb=rb['checkpoint']
            contract_keys=['committed_ids','retained_prefix','tokens','positions','sequence_ids','logits_mask','bounds','sampler']
            aligned=all(ca[k]==cb[k] for k in contract_keys);assert aligned
            sa,sb=State(da/'live/donor.state'),State(db/'live/donor.state')
            assert sa.positions==list(range(ca['positions'][0]))
            prompt_count=len(ca['retained_prefix'])-len(ca['committed_ids'])+1
            k=compare(sa,sb,prompt_count);kv.append({'task':task,'repetition':rep,**k})
            cell={}
            for d,r in pair:
                c=r['checkpoint']
                for f in c['forks']:
                    key=(r['condition'],f['ub']);cell[key]=f
                    for row in range(len(f['sampled_ids'])):
                        p=d/f"live/ub{f['ub']}_row{row}.f32";_,_,top=logits(p)
                        rows.append({'task':task,'rep':rep,'donor':r['condition'],'current_ub':f['ub'],'row':row,
                                     'selected_id':f['sampled_ids'][row],'raw_logit_sha256':sha(p),**top})
            def ids(n,u):return cell[(n,u)]['sampled_ids']
            ce=[ids(n,2)!=ids(n,1) for n in ['N0','N1']]
            se=[ids('N0',u)!=ids('N1',u) for u in [2,1]]
            effects.append({'task':task,'repetition':rep,'aligned':aligned,'committed_count':len(ca['committed_ids']),
                            'state_serialized_equal':sa.data==sb.data,'logical_prompt_kv_equal':k['prompt_kv_equal'],
                            'current_call_decision_effect_by_donor':ce,'donor_decision_effect_by_current_ub':se,
                            'matrix':{n:{str(u):{'sampled_ids':cell[(n,u)]['sampled_ids'],
                                      'auxiliary_ids':cell[(n,u)]['auxiliary_ids']} for u in [2,1]} for n in ['N0','N1']}})
    save(out/'EFFECTS.json',effects);save(out/'LOGICAL_KV_COMPARISONS.json',kv)
    with (out/'DECISIONS.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    validation={'status':'PASS','engineering_complete_trajectories':12,'formal_complete_trajectories':24,
                'formal_historical_matches':sum(r['historical_equal'] for _,r in formal),
                'same_path_natural_decision_matches':sum(r['same_path_natural_decision_equal'] for _,r in formal),
                'aligned_donor_pairs':len(effects),'fork_units':48,
                'fork_auxiliary_forward_calls':sum(len(f['auxiliary_ids']) for _,r in formal for f in r['checkpoint']['forks']),
                'current_effect_units':sum(any(e['current_call_decision_effect_by_donor']) for e in effects),
                'donor_effect_units':sum(any(e['donor_decision_effect_by_current_ub']) for e in effects),
                'raw_files_hash_checked':sum(len(r['files']) for _,r in formal)}
    save(out/'VALIDATION.json',validation)
    print(json.dumps(validation),flush=True)
    for e in effects:
        if e['repetition']==1:print(json.dumps(e),flush=True)
if __name__=='__main__':main()
