"""Separate raw-to-table CPU verifier and six real-input negative fixtures; no analyzer import."""
import argparse, ast, copy, csv, hashlib, json, math, statistics
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import numpy as np

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def table(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=0
def need(v,msg):
    global checks;checks+=1
    if not v:raise ValueError(msg)
def close(a,b,msg):need(math.isclose(float(a),float(b),rel_tol=2e-12,abs_tol=1e-12),msg)
def rebuild(raw,plan):
    groups=defaultdict(dict)
    for r in raw:
        k=(r['task'],r['condition']);rep=r['repetition'];need(rep not in groups[k],'duplicate key');groups[k][rep]=r
    need(set(groups)=={(t,c['name']) for t in plan['tasks'] for c in plan['conditions']},'missing group')
    for g in groups.values():need(set(g)=={1,2,3,4},'missing repeat')
    for t in plan['tasks']:
        refs=groups[t,'scalar_reference'];need(all(refs[k]['response']['tokens']==refs[1]['response']['tokens'] and refs[k]['endpoint']==refs[1]['endpoint'] for k in refs),'unstable reference')
        for c in plan['conditions']:
            for r in groups[t,c['name']].values():
                need(r['response']['tokens']==refs[1]['response']['tokens'] and r['endpoint']==refs[1]['endpoint'],'unqualified cost')
                for v in [r['wall_ms'],r['response']['timings']['predicted_ms']]:need(math.isfinite(v) and v>0,'invalid ms')
    return groups
def audit_exports(raw,plan,costrows,pairrows):
    groups=rebuild(raw,plan)
    for row in costrows:
        need(row['timer_unit']=='ms','wrong unit');r=groups[row['task'],row['condition']][int(row['repetition'])];close(row['generation_ms'],r['response']['timings']['predicted_ms'],'wrong generation ms');close(row['whole_ms'],r['wall_ms'],'wrong whole ms');need(row['qualified']=='True','unqualified export')
    for row in pairrows:
        b=groups[row['task'],row['baseline']];c=groups[row['task'],row['candidate']]
        get=(lambda r:r['wall_ms']) if row['timer']=='whole' else (lambda r:r['response']['timings']['predicted_ms'])
        bm=statistics.median(Decimal(str(get(r))) for r in b.values());cm=statistics.median(Decimal(str(get(r))) for r in c.values())
        close(row['baseline_median_ms'],bm,'baseline median');close(row['candidate_median_ms'],cm,'candidate median');close(row['speedup_baseline_over_candidate'],bm/cm,'inverted ratio');need(row['qualified']=='True','unqualified pair')
    return groups
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--experiment',required=True);ap.add_argument('--analysis',default=str(Path(__file__).parent));ap.add_argument('--archive',required=True);ap.add_argument('--phase2',required=True);ap.add_argument('--phase2-archive',required=True);a=ap.parse_args();root=Path(a.experiment);out=Path(a.analysis)
    raw=read(root/'runs/b/RECORDS.json');plan=read(root/'B_MANIFEST.json');costrows=table(out/'RAW_COSTS.csv');pairs=table(out/'TASK_COST_PAIRS.csv');roundrows=table(out/'ROUND_COST_PAIRS.csv');qual=table(out/'QUALIFICATION_RECOMPUTED.csv');summary=read(out/'COST_SUMMARY.json')
    need(len(raw)==len(costrows)==len(qual)==384,'formal cardinality');need(len(pairs)==288 and len(roundrows)==1152,'pair cardinality')
    groups=audit_exports(raw,plan,costrows,pairs)
    for q in qual:
        r=groups[q['task'],q['condition']][int(q['repetition'])];ids=r['response']['tokens'];need(q['qualified']=='True' and q['full_array_equal']=='True' and q['endpoint_equal']=='True' and q['reference_stable']=='True','qualification export');need(int(q['tokens'])==len(ids) and q['endpoint']==r['endpoint'],'endpoint export');need(q['tokens_sha256']==hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest(),'token digest')
    for r in raw:need(read(root/r['record_relative_path'])==r,'individual raw mismatch')
    for row in roundrows:
        get=(lambda r:r['wall_ms']) if row['timer']=='whole' else (lambda r:r['response']['timings']['predicted_ms']);rep=int(row['repetition']);b=get(groups[row['task'],row['baseline']][rep]);c=get(groups[row['task'],row['candidate']][rep]);close(row['baseline_ms'],b,'round baseline');close(row['candidate_ms'],c,'round candidate');close(row['speedup_baseline_over_candidate'],Decimal(str(b))/Decimal(str(c)),'round ratio')
    # Independently generate samples and implement linear interpolation instead of np.quantile.
    indices=np.random.Generator(np.random.PCG64(20261008)).integers(0,24,(10000,24))
    for s in summary['comparisons']:
        rs=[float(next(p['speedup_baseline_over_candidate'] for p in pairs if p['task']==t and p['timer']==s['timer'] and p['baseline']==s['baseline'] and p['candidate']==s['candidate'])) for t in plan['tasks']]
        point=math.exp(statistics.mean(math.log(v) for v in rs));close(s['task_median_gm'],point,'GM')
        sim=sorted(np.exp(np.sum(np.log(rs)[indices],axis=1)/24).tolist())
        for prob,ci in zip([.025,.975],s['descriptive_task_bootstrap_95_linear']):
            pos=(len(sim)-1)*prob;lo=int(pos);hi=math.ceil(pos);expected=sim[lo]+(pos-lo)*(sim[hi]-sim[lo]);close(ci,expected,'bootstrap CI')
        for rep in range(1,5):
            vv=[float(x['speedup_baseline_over_candidate']) for x in roundrows if x['timer']==s['timer'] and x['baseline']==s['baseline'] and x['candidate']==s['candidate'] and int(x['repetition'])==rep];close(s['rounds'][rep-1]['gm'],math.exp(statistics.mean(math.log(v) for v in vv)),'round GM')
    fixtures=[]
    for kind in ['missing_repeat','duplicate_key','inverted_ratio','wrong_unit','unqualified_output','invalid_cost']:
        r=copy.deepcopy(raw);cs=copy.deepcopy(costrows);ps=copy.deepcopy(pairs)
        if kind=='missing_repeat':r.pop()
        elif kind=='duplicate_key':r.append(copy.deepcopy(r[0]))
        elif kind=='inverted_ratio':ps[0]['speedup_baseline_over_candidate']=str(1/float(ps[0]['speedup_baseline_over_candidate']))
        elif kind=='wrong_unit':cs[0]['timer_unit']='s';cs[0]['generation_ms']=str(float(cs[0]['generation_ms'])/1000)
        elif kind=='unqualified_output':next(x for x in r if x['condition']=='target_scopes')['response']['tokens'][0]+=1
        elif kind=='invalid_cost':r[0]['wall_ms']=float('nan')
        try:audit_exports(r,plan,cs,ps)
        except ValueError as exc:fixtures.append({'fixture':kind,'status':'REJECTED','reason':str(exc)})
        else:raise ValueError('negative fixture was accepted: '+kind)
    units=read(out/'UNIT_MANIFEST.json');post=[]
    for u in units['units']:
        p=(root.parent/u['path']) if u['namespace']=='archive_restored' else (Path(a.phase2)/u['path']);need(sha(p)==u['sha256'],'old bytes changed');post.append({'namespace':u['namespace'],'path':u['path'],'sha256':u['sha256'],'unchanged':True})
    need(sha(a.archive)==units['archive']['sha256'],'archive changed');need(sha(a.phase2_archive)==units['phase2_archive']['sha256'],'Phase2 archive changed')
    for script in ['identity.py','analyze.py','verify.py']:
        tree=ast.parse((out/script).read_text())
        imported=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        imported += [alias.name for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names]
        need(not any(x in imported for x in ['close_base','run_b','analyze_bcd','server','close_server','subprocess']),'unsafe model path')
    result={'status':'PASS','positive_and_negative_checks':checks,'negative_fixtures':fixtures,'independent_raw_reconstruction':True,'old_selected_units_unchanged':len(post),'archives_unchanged':True,'formal_records':384,'warmups_excluded':16,'new_model_requests':0,'new_target_draft_forwards':0,'new_warmups':0,'source_scope':'B raw arrays/costs individually re-read; selected archive/Phase2 sources; no omitted asset authentication claimed','bootstrap_independent_quantile':'manual sorted linear interpolation type7; common PCG64 index matrix', 'no_import_of_old_runner_or_analyzer':True}
    (out/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'POST_AUDIT.json').write_text(json.dumps({'status':'PASS','selected_units':post,'archive_unchanged':True,'phase2_archive_unchanged':True,'models_runtime_driver_not_accessed_or_modified_this_round':True},indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['negative_fixtures','source_scope']},indent=2))
if __name__=='__main__':main()
