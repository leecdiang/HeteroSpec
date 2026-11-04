"""Independent CPU recomputation of pinned, repository-visible native records.
No GPU calls. Compact timing/endpoint records are not raw f32 payload audit.
Run: python recompute.py (stdlib only).
"""
import json,math,random,statistics,collections,pathlib,hashlib
P=pathlib.Path(__file__).parent
read=lambda n:json.loads((P/'sources'/n).read_text())
gm=lambda a:math.exp(statistics.mean(math.log(x) for x in a))
def boot(a):
 r=random.Random(20261104);v=sorted(math.exp(statistics.mean(r.choices(a,k=len(a)))) for _ in range(10000));return [v[249],v[9749]]
# Compare independently stored actual output IDs, not MATRIX booleans.
e=read('152_execution_COUNTEREXAMPLE_ENDPOINTS.json');E={r['slot_id']:r['endpoint'] for r in e};ends=[]
for i in [2,4,6]:
 prefix=f'b570_producer_consumer_boundary_v1/B1/input{i}/';r=E[prefix+'R/off']
 for prod in ['P1','P4T']:
  for c in ['C1','PQ','QB']:
   ep=E[prefix+prod+'/'+c+('/natural/off' if c=='C1' else '/resumed/off')]
   dif=[j+1 for j,(x,y) in enumerate(zip(r['ids'],ep['ids'])) if x!=y]
   ends.append(dict(i=i,producer=prod,consumer=c,endpoint_equal=ep==r,first_difference=dif[0] if dif else None,aligned_token_differences=len(dif),length=ep['length']))
m=read('152_execution_MATRIX.json');state=read('152_execution_STATE_EFFECTS.json')
summary={'evidence_level':'CPU recomputation of compact native endpoint/timing records; not a fresh raw-vector audit','PR152':{'endpoint_match_count':sum(x['strict_reference_equal'] for x in m),'cells':len(m),'independently_recomputed_counterexample_endpoints':ends,'boundary_changes':sum(not x['kv_bytes_equal'] and not x['initial_logits_bytes_equal'] for x in state),'local_PQ_QB_full_vector_equal':sum(x[p+'_PQ_QB_vectors_equal'] for x in state for p in ['P1','P4T'])}}
# True paired timing records, nested sessions retained and root-level resampling.
a=read('165_COST.json')['rows'];pairs=collections.defaultdict(dict)
for r in a:pairs[r['input'],r['session']][r['arm']]=r['measured_seconds']
res=[]
for l,r in [('M_QB','M_PQ'),('C_QB','C_PQ'),('M_QB','C_QB'),('M_QB','R'),('C_QB','R')]:
 roots=collections.defaultdict(list)
 for (i,s),p in pairs.items():roots[i].append(math.log(p[l]/p[r]))
 vals=[statistics.mean(v) for v in roots.values()]
 res.append(dict(contrast=l+'/'+r,ratio=math.exp(statistics.mean(vals)),root_cluster_exploratory95=boot(vals),root_count=len(vals),all_blocks=len(pairs),leave_one_root_out_range=[min(math.exp(statistics.mean(vals[:i]+vals[i+1:])) for i in range(len(vals))),max(math.exp(statistics.mean(vals[:i]+vals[i+1:])) for i in range(len(vals)))]))
summary['PR165']=res
# All fixed observations, independently identify crossing via head and q.
f=read('169_fixed-work.json');pairs=collections.defaultdict(dict)
for r in f:pairs[tuple(r[k] for k in ['family','C','B','head','q','rep'])][r['arm']]=r
strata=collections.defaultdict(list);count_counterexamples=collections.Counter()
for (family,C,B,h,q,rep),p in pairs.items():
 if not all(a in p and p[a]['qualified'] for a in ['WB','QB']):continue
 crossing=(h//256!=(h+q-1)//256)
 ratio=p['WB']['seconds']/p['QB']['seconds'];strata[family,q,crossing].append(ratio)
 if crossing and p['WB']['calls']>p['QB']['calls'] and ratio<1:count_counterexamples[family]+=1
fixed=[dict(family=k[0],q=k[1],crossing=k[2],n=len(v),WB_over_QB=gm(v),WB_faster=sum(x<1 for x in v),min=min(v),max=max(v)) for k,v in sorted(strata.items())]
summary['PR169_fixed']={'observations':len(f),'strata':fixed,'fewer_calls_but_QB_slower':dict(count_counterexamples),'crossing_pairs':sum(len(v) for k,v in strata.items() if k[2])}
# Natural timing, not pooled independent 72 samples.
n=read('169_NATURAL_COST.json');pairs=collections.defaultdict(dict)
for r in n:pairs[r['id'],r['session'],r['block']][r['arm']]=r['seconds']
res=[]
for l,r in [('WB','QB'),('PQ','QB'),('S1','QB')]:
 roots=collections.defaultdict(list)
 for (i,s,b),p in pairs.items():roots[i].append(math.log(p[l]/p[r]))
 vals=[statistics.mean(v) for v in roots.values()]
 res.append(dict(contrast=l+'/'+r,ratio=math.exp(statistics.mean(vals)),exploratory_root95=boot(vals),root_count=len(vals),blocks=len(pairs),root_ratios={k:math.exp(statistics.mean(v)) for k,v in roots.items()},leave_one_out_range=[min(math.exp(statistics.mean(vals[:i]+vals[i+1:])) for i in range(len(vals))),max(math.exp(statistics.mean(vals[:i]+vals[i+1:])) for i in range(len(vals)))]))
summary['PR169_natural']=res
# Prefix reuse only root-aggregated times exposed here; no claim of new native timing audit.
panel=read('175_evidence_panel.json');rr=read('175_evidence_analysis.json')['root_results'];rr={x['root_id']:x for x in rr};res={}
for cross in [False,True]:
 roots=[x for x in panel['test'] if bool(x['crossed_qb_calls'])==cross]
 contrasts={a:gm([rr[x['root_id']]['baseline_over_AUTO'][a] for x in roots]) for a in ['QB','WB-cut','WB-rechunk']}
 # baseline1/baseline2 cancels AUTO within a root: avoids treating independent measurements as independent samples.
 res[str(cross)]={'roots':len(roots),'root_ids':[x['root_id'] for x in roots],'baseline_over_AUTO':contrasts,'WBcut_over_QB':contrasts['WB-cut']/contrasts['QB'],'WBcut_over_rechunk':contrasts['WB-cut']/contrasts['WB-rechunk'],'extra_cut_vs_rechunk_calls':sum(x['calls']['WB-cut']-x['calls']['WB-rechunk'] for x in roots)}
summary['PR175']={'calibration_crossings':sum(x['crossed_qb_calls']>0 for x in panel['calibration']),'test_strata':res,'warning':'Post-hoc subgroup with n=4 crossing roots; root aggregates only, no per-session effect or causal interpretation.'}
# Independent exact-cell causal comparison. Repeated cells remain same finite tasks.
causal=[]
for x in read('101_KV_LOGITS_CROSS.json')['rows']:
 c=x['full_cells']; aa,ab,ba,bb=[c[k] for k in ['AA','AB','BA','BB']]
 dif=[i for i,(a,b) in enumerate(zip(aa['ids'],ba['ids'])) if a!=b]
 causal.append({'task':x['task'],'AA_equals_AB':aa==ab,'BA_equals_BB':ba==bb,'first_KV_source_difference_zero_based':dif[0] if dif else None,'all_initial_top1_same':len(set(x['initial_top1'].values()))==1,'repetitions':x['repetitions']})
summary['PR101_causal']=causal
summary['PR152']['initial_logit_magnitude_counterexample']={'minimum_maxabs_divergent_input':min(x['initial_logits_max_absolute_difference'] for x in state if not x['all_six_endpoints_match_R']),'maximum_maxabs_all_endpoints_equal':max(x['initial_logits_max_absolute_difference'] for x in state if x['all_six_endpoints_match_R'])}
cp=[x for x in panel['test'] if x['crossed_qb_calls']]
v=[math.log(rr[x['root_id']]['baseline_over_AUTO']['WB-cut']/rr[x['root_id']]['baseline_over_AUTO']['QB']) for x in cp]
summary['PR175']['crossing_WBcut_QB_leave_one_root_out']=[math.exp(statistics.mean(v[:i]+v[i+1:])) for i in range(len(v))]
assert len(f)==1395 and len(n)==288 and len(m)==48
assert summary['PR169_fixed']['crossing_pairs']==129
assert sum(count_counterexamples.values())==48
assert summary['PR152']['endpoint_match_count']==39
summary['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((P/'sources').glob('*')) if p.suffix!='.b64'}
(P/'RECOMPUTED.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},indent=2))
