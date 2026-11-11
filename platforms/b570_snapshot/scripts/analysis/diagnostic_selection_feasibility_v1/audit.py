"""CPU-only recomputation from pinned Git exports or a bound small input snapshot."""
import argparse, csv, hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / 'benchmarks/diagnostic_selection_feasibility_v1'
PIN = 'a3bf06ccaba6e4d7563b5bf5cb318b246727281c'
EOG = {128247,151643,151645,151662,151663,151664}

def load(path):
    def pairs(items):
        d = {}
        for k,v in items:
            if k in d: raise ValueError('duplicate JSON field: '+k)
            d[k]=v
        return d
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs)

def save(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')

def sha(b): return hashlib.sha256(b).hexdigest()

def save_outcomes(contexts):
    # Keep one complete array record per line for a compact, reviewable snapshot.
    chunks=[]
    for ctx in contexts:
        metadata={k:v for k,v in ctx.items() if k!='records'}
        prefix=json.dumps(metadata,separators=(',',':'))[:-1]
        chunks.append(prefix+',"records":[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in ctx['records'])+'\n]}')
    (DOC/'inputs').mkdir(exist_ok=True)
    (DOC/'inputs/OUTCOMES.json').write_text('[\n'+',\n'.join(chunks)+'\n]\n',encoding='utf-8',newline='\n')

class Sources:
    def __init__(self):
        m=load(DOC/'SOURCE_BINDINGS.json'); assert m['commit']==PIN
        self.bindings={x['path']:x for x in m['files']}
        self.used=[]
    def get(self,path):
        b=subprocess.check_output(['git','show',PIN+':'+path],cwd=ROOT)
        e=self.bindings[path]
        assert len(b)==e['bytes'] and sha(b)==e['sha256'],path
        self.used.append(path)
        return json.loads(b)

def normalize(row):
    ids=row['ids'];ep=row['endpoint']
    assert ids and len(ids)<=128 and all(type(i)==int and 0<=i<151936 for i in ids)
    assert not any(i in EOG for i in ids[:-1]),'early EOS'
    ep='limit' if ep=='CAP128' else ep
    assert ep in ('EOS','limit')
    assert (ep=='EOS')==(ids[-1] in EOG),'endpoint/token disagreement'
    assert ep=='EOS' or len(ids)==128,'truncated cap'
    return {'task':row['task'],'condition':row['condition'],'rep':row.get('rep',row.get('repetition')),'ids':ids,'endpoint':ep}

def index(rows,tasks,conditions):
    d={}
    for x in rows:
        k=(x['task'],x['condition'],x['rep'])
        if k in d: raise ValueError('duplicate task/condition/repetition')
        d[k]=x
    expected={(t,c,r) for t in tasks for c in conditions for r in (1,2,3)}
    if set(d)!=expected: raise ValueError('matrix denominator changed')
    return d

def boundary(x): return (len(x['ids']),x['endpoint'],x['ids'][-1])

def compare(a,b):
    first=next((i for i,(x,y) in enumerate(zip(a['ids'],b['ids'])) if x!=y),None)
    if first is None and len(a['ids'])!=len(b['ids']):first=min(len(a['ids']),len(b['ids']))
    ae=a['ids']==b['ids'];be=boundary(a)==boundary(b)
    return {'array':ae,'boundary':be,'reason':a['endpoint']==b['endpoint'],'joint':ae and be,
            'first_index_0':first,'position_difference_count':sum(x!=y for x,y in zip(a['ids'],b['ids']))+abs(len(a['ids'])-len(b['ids']))}

def stable(d,t,c):
    return all(compare(d[t,c,1],d[t,c,r])['joint'] for r in (2,3))

def action_metrics(ctx,action):
    n=len(ctx['tasks']);d=index(ctx['records'],ctx['tasks'],ctx['known_conditions'])
    if action not in ctx['known_conditions']:
        return {'status':'UNKNOWN','tasks':n,'observations':n*3,'missing_observations':n*3,
                'repairs':None,'regressions':None,'persistent':None,'reference_matches':None}
    transitions={'retained':0,'repairs':0,'regressions':0,'persistent':0}
    matches=0;obs=0;st=0
    for t in ctx['tasks']:
        b=all(compare(d[t,'N0',r],d[t,'R',r])['joint'] for r in (1,2,3))
        a=all(compare(d[t,action,r],d[t,'R',r])['joint'] for r in (1,2,3))
        transitions['retained' if b and a else 'repairs' if a else 'regressions' if b else 'persistent']+=1
        matches+=a;st+=stable(d,t,action)
        obs+=sum(compare(d[t,action,r],d[t,'R',r])['joint'] for r in (1,2,3))
    return {'status':'PASS' if matches==n and st==n else 'FAIL','tasks':n,'observations':n*3,
            'missing_observations':0,**transitions,'reference_matches':matches,'reference_observation_matches':obs,'stable_tasks':st}

def main():
    p=argparse.ArgumentParser();p.add_argument('--from-inputs',action='store_true');args=p.parse_args()
    if args.from_inputs:
        binding=load(DOC/'INPUT_SNAPSHOT_BINDING.json');b=(DOC/'inputs/OUTCOMES.json').read_bytes();assert sha(b)==binding['sha256']
        contexts=json.loads(b);used=binding['sources']
    else:
        s=Sources()
        bridge=s.get('benchmarks/rtx_target_only_bridge_v1/FORMAL_ARRAYS.json')['records']
        old=s.get('paper/mlsys2027/reviews/reconstruction_v010/rtx/FORMAL_ARRAYS_NEUTRAL.json')['records']
        b570=s.get('paper/mlsys2027/reviews/reconstruction_v010/b570/RAW_OUTPUT_ARRAYS.json')['units']
        rtasks=s.get('benchmarks/rtx_target_only_bridge_v1/PROTOCOL.json')['tasks']
        btasks=s.get('benchmarks/b570_prefill_diagnostic_v1/PROTOCOL.json')['tasks']
        rtasks=['HumanEval/'+str(t) if type(t)==int else t for t in rtasks]
        old_native={(x['task'],x['condition'],x['rep']):normalize(x) for x in old if x['task'] in rtasks and x['condition'] in ('N0','N1')}
        fresh=[normalize(x) for x in bridge if x['condition'] in ('N0','N1')]
        history={c:sum(compare(x,old_native[x['task'],c,x['rep']])['joint'] for x in fresh if x['condition']==c) for c in ('N0','N1')}
        assert history=={'N0':57,'N1':57}
        save(DOC/'HISTORICAL_NATIVE_CHECK.json',{'fresh_to_pinned_old':history,'denominator_each':57,'scope':'Direct pinned compact-array comparison; no old full archive re-audit. Historical U2/12-thread bridge remains inherited.'})
        mtasks=sorted({x['task'] for x in old if x['task'].startswith('MBPP/')})
        contexts=[{'name':'RTX_19','tasks':rtasks,'known_conditions':['R','N0','N1','U2','H1'],
                   'records':[normalize(x) for x in bridge]+[normalize(x) for x in old if x['task'] in rtasks and x['condition'] in ('R','H1')]},
                  {'name':'B570_24','tasks':btasks,'known_conditions':['R','N0','N1','T0','T1'],'records':[normalize(x) for x in b570]},
                  {'name':'RTX_MBPP_24_supplement','tasks':mtasks,'known_conditions':['R','N0','N1','H0','H1'],
                   'records':[normalize(x) for x in old if x['task'] in mtasks]}]
        raw=s.get('paper/mlsys2027/reviews/reconstruction_v010/b570/NATIVE_UNTRUNCATED_ARRAYS.json')['units']
        bd=index(contexts[1]['records'],btasks,contexts[1]['known_conditions']);overshoot={c:0 for c in ('N0','N1')}
        assert len(raw)==144
        for x in raw:
            ids=x['ids'];flags=x['eog'];assert len(ids)==len(flags)
            end=min(next((i+1 for i,e in enumerate(flags) if e),len(ids)),128)
            assert ids[:end]==bd[x['task'],x['condition'],x['repetition']]['ids']
            overshoot[x['condition']]+=len(ids)-end
        assert overshoot=={'N0':60,'N1':63}
        save(DOC/'B570_RAW_CONTRACT_CHECK.json',{'native_arrays':144,'raw_extra_ids':overshoot,'scope':'Recomputed from pinned untruncated export, not a new original capture audit.'})
        used=s.used
        save_outcomes(contexts)
        b=(DOC/'inputs/OUTCOMES.json').read_bytes()
        save(DOC/'INPUT_SNAPSHOT_BINDING.json',{'source_commit':PIN,'sha256':sha(b),'bytes':len(b),'sources':used,'normalization':'Only field naming and CAP128 -> limit; arrays retained without further truncation.'})
    results=[];rows=[]
    for ctx in contexts:
        d=index(ctx['records'],ctx['tasks'],ctx['known_conditions']);n=len(ctx['tasks'])
        comparisons={}
        pairs=[('N0','N1'),('N0','R'),('N1','R')]
        if 'U2' in ctx['known_conditions']:pairs += [('U2','N1'),('U2','N0'),('U2','R')]
        proxy='T1' if 'T1' in ctx['known_conditions'] else 'H1';pairs.append((proxy,'N1'))
        for a,b in pairs:
            metrics=[compare(d[t,a,r],d[t,b,r]) for t in ctx['tasks'] for r in (1,2,3)]
            comparisons[a+'/'+b]={k:sum(x[k] for x in metrics) for k in ('array','boundary','reason','joint')}
            comparisons[a+'/'+b].update(observations=n*3,task_units=n,all3_equal_tasks=sum(all(compare(d[t,a,r],d[t,b,r])['joint'] for r in (1,2,3)) for t in ctx['tasks']))
        actions=['R','N0','N1','U2']
        res={'context':ctx['name'],'tasks':n,'records':len(ctx['records']),'comparisons':comparisons,
             'stability':{c:sum(stable(d,t,c) for t in ctx['tasks']) for c in ctx['known_conditions']},
             'actions':{a:action_metrics(ctx,a) for a in actions}}
        results.append(res)
        for t in ctx['tasks']:
            for a in actions:
                if a not in ctx['known_conditions']:
                    rows.append({'context':ctx['name'],'task':t,'action':a,'status':'UNKNOWN','repairs':None,'regressions':None,'persistent':None,'reference_matches_3':None})
                    continue
                base=all(compare(d[t,'N0',r],d[t,'R',r])['joint'] for r in (1,2,3));good=all(compare(d[t,a,r],d[t,'R',r])['joint'] for r in (1,2,3))
                rows.append({'context':ctx['name'],'task':t,'action':a,'status':'KNOWN','repairs':int(not base and good),'regressions':int(base and not good),'persistent':int(not base and not good),'reference_matches_3':sum(compare(d[t,a,r],d[t,'R',r])['joint'] for r in (1,2,3))})
    # Exact headline assertions are integrity gates, never outcome-conditioned reruns.
    rr=results[0];assert rr['comparisons']['U2/N1']['joint']==57
    assert rr['comparisons']['U2/N0']['joint']==rr['comparisons']['N0/N1']['joint']==51
    assert results[1]['actions']['N1']['repairs']==4 and results[1]['actions']['N1']['regressions']==0
    save(DOC/'RECOMPUTED.json',{'source_commit':PIN,'sources_recomputed':used,'contexts':results,'exposed_development_only':True,'new_inference_runs':0})
    with (DOC/'TASK_ACTIONS.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    save(DOC/'ACTION_CATALOG.json',[
        {'context':'RTX_19','actions':[{'handle':'N1','proxy':'H1','kind':'native_continuation_UB1'},{'handle':'U2','proxy':None,'kind':'ordinary_target_only_UB2'}]},
        {'context':'B570_24','actions':[{'handle':'N1','proxy':'T1','kind':'native_prefill_UB128'}]},
        {'context':'RTX_MBPP_24_supplement','actions':[{'handle':'N1','proxy':'H1','kind':'native_continuation_UB1'},{'handle':'U2','proxy':None,'kind':'ordinary_target_only_UB2_UNKNOWN'}]}])
    print('PASS CPU recomputation:',[(r['context'],r['records']) for r in results])

if __name__=='__main__':main()
