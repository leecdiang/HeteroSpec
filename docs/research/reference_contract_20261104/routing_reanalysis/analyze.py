"""Exploratory nested grouped validation; no online execution or causal claims."""
from pathlib import Path
import json,math,statistics as st,collections as co,random,hashlib
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
f=ROOT/'scalars.json'
if f.stat().st_size!=manifest['projection_bytes']:raise ValueError('Projection byte count mismatch')
if hashlib.sha256(f.read_bytes()).hexdigest()!=manifest['projection_sha256']:raise ValueError('Projection SHA mismatch')
r=json.loads(f.read_text())
if len(r)!=240:raise ValueError('Expected240QBrecords')
keys=[(x['model'],x['root'],x['date'],x['session'])for x in r]
if len(set(keys))!=240:raise ValueError('Duplicate measured key')
for x in r:
 if x['model']not in ['Qwen','SmolLM2','Llama'] or x['M']<=0 or x['C']<=0 or not math.isfinite(x['M']+x['C']) or not isinstance(x['prompt'],int) or x['prompt']<=0:raise ValueError('Invalid scalar')
g=co.defaultdict(list)
for x in r:g[x['model'],x['root']].append(x)
a=[]
for (model,root),v in sorted(g.items()):
 if len({x['prompt']for x in v})!=1:raise ValueError('prompt inconsistent')
 a.append(dict(model=model,root=root,prompt=v[0]['prompt'],M=st.mean(x['M']for x in v),C=st.mean(x['C']for x in v),records=len(v)))
# Deterministic training-only candidates; tie prefers M and then lower threshold.
def fit(train,kind):
 if kind=='fixed':candidates=[-1,math.inf]
 else:
  ps=sorted({x['prompt']for x in train});candidates=[-1]+[(x+y)/2 for x,y in zip(ps,ps[1:])]+[math.inf]
 return min(candidates,key=lambda t:(sum(x['C']if x['prompt']<=t else x['M']for x in train),t))
def chosen(x,t):return 'C' if x['prompt']<=t else 'M'
def nested(train):
 scores={}
 for kind in ['fixed','stump']:
  costs=[]
  for held in train:
   inner=[x for x in train if x['root']!=held['root']];t=fit(inner,kind);costs.append(held[chosen(held,t)])
  scores[kind]=sum(costs)
 kind=min(scores,key=lambda k:(scores[k],['fixed','stump'].index(k)))
 return fit(train,kind),kind,scores
out=[]
for held in a:
 # Model is deployment-known. All same-root rows (including the other151model) excluded before filtering model.
 train=[x for x in a if x['root']!=held['root'] and x['model']==held['model']]
 t,kind,inner=nested(train);fixed=fit(train,'fixed');stump=fit(train,'stump')
 row=dict(held,selected_class=kind,threshold=None if math.isinf(t)else t,threshold_always_C=math.isinf(t),inner_costs=inner,train_roots=len(train))
 policies={'nested':chosen(held,t),'stump_only':chosen(held,stump),'train_fixed':chosen(held,fixed),'exposed384_reference':'C'if held['prompt']<=384 else'M','alwaysM':'M','alwaysC':'C','root_oracle':'C'if held['C']<held['M']else'M'}
 row['actions']=policies;row['costs']={k:held[v]for k,v in policies.items()};out.append(row)

def quantile(a,p):
 a=sorted(a);z=p*(len(a)-1);i=int(z);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(z-i)
def summarize(v):
 fixed=min(['alwaysM','alwaysC'],key=lambda k:sum(x['costs'][k]for x in v));base=sum(x['costs'][fixed]for x in v);ans={'roots':len(v),'best_fixed_retrospective':fixed,'best_fixed_sum':base,'policies':{}}
 for p in v[0]['costs']:
  c=sum(x['costs'][p]for x in v);ex=[x['costs'][p]-min(x['M'],x['C'])for x in v];harm=[x['costs'][p]-x['M']for x in v]
  ans['policies'][p]={'sum':c,'over_best_fixed':c/base,'saving_vs_best_fixed':1-c/base,'regret_vs_root_oracle_s':sum(ex),'selected_C':sum(x['actions'][p]=='C'for x in v),'draft_selected_but_costlier':sum(x['actions'][p]=='C'and x['C']>x['M']for x in v),'max_excess_vs_M_s':max(harm),'max_relative_excess_vs_M':max(x['costs'][p]/x['M']-1 for x in v),'mean_overhead_budget_ms_vs_best_fixed':1000*(base-c)/len(v),'saving_with_uniform_overhead_ms':{str(h):1-(c+len(v)*h/1000)/base for h in [1,10,50,100]}}
 return ans
summaries={m:summarize([x for x in out if x['model']==m])for m in sorted({x['model']for x in out})}
# 384 is a historical panel-design boundary but route use is posthoc/exposed, not a preregistered policy.
# Conditional clustered bootstrap of fixed OOF predictions, with best fixed baseline specified by full panel model.
# Does not re-train thresholds or estimate training uncertainty. Same151root draw shared by both models.
rng=random.Random(817301);boots={m:[]for m in summaries};allroots=sorted({x['root']for x in out});strata=co.defaultdict(list)
for root in allroots:
 membership=tuple(sorted(x['model']for x in out if x['root']==root));strata[membership].append(root)
lookup={(x['model'],x['root']):x for x in out}
for _ in range(10000):
 sample=[root for ss in strata.values()for root in rng.choices(ss,k=len(ss))]
 for m in summaries:
  v=[lookup[m,root]for root in sample if(m,root)in lookup];p=sum(x['costs']['nested']for x in v);b=sum(x['costs'][summaries[m]['best_fixed_retrospective']]for x in v);boots[m].append(1-p/b)
for m in summaries:summaries[m]['nested_conditional_root_bootstrap_95pct']=[quantile(boots[m],.025),quantile(boots[m],.975)]
# Across-day holdout is temporal repeat on identical roots, not unseen-input generalization.
crossday=[]
for m in ['Qwen','SmolLM2']:
 days=sorted({x['date']for x in r if x['model']==m})
 for train_day,test_day in [days,days[::-1]]:
  z=[]
  for root in sorted({x['root']for x in r if x['model']==m}):
   q=[x for x in r if x['model']==m and x['root']==root and x['date']==train_day];z.append(dict(root=root,prompt=q[0]['prompt'],M=st.mean(x['M']for x in q),C=st.mean(x['C']for x in q)))
  t=fit(z,'stump');test=[x for x in r if x['model']==m and x['date']==test_day];C=sum(x[chosen(x,t)]for x in test);M=sum(x['M']for x in test);D=sum(x['C']for x in test)
  crossday.append(dict(model=m,train_day=train_day,test_day=test_day,threshold=None if math.isinf(t)else t,alwaysC=math.isinf(t),cost=C,over_test_best_fixed=C/min(M,D),warning='same roots repeated; temporal stability only'))
# Train threshold on all source-model roots, test different model. #151 same-root transfer is labeled explicitly.
transfer=[]
for src in summaries:
 t=fit([x for x in a if x['model']==src],'stump')
 for dst in summaries:
  if dst==src:continue
  v=[x for x in a if x['model']==dst];cost=sum(x[chosen(x,t)]for x in v);base=min(sum(x['M']for x in v),sum(x['C']for x in v))
  transfer.append(dict(source=src,target=dst,threshold=None if math.isinf(t)else t,alwaysC=math.isinf(t),over_best_fixed=cost/base,shared_roots=bool({x['root']for x in a if x['model']==src}&{x['root']for x in v})))
res={'sources':manifest['original_analysis_sources'],'unit':'same dataset input root, repeated sessions averaged; only four151roots overlap across models', 'records':len(r),'model_roots':len(a),'unique_roots':len(allroots),'features':['deployment model','prompt token count'],'constant_budget':'cap128 throughout, no budget policy identifiable','summaries':summaries,'outer_rows':out,'crossday_same_roots':crossday,'cross_model_transfer':transfer,'bootstrap':'10000 model-membership-stratified root cluster draws (8Qwen-only,8Smol-only,4shared,24Llama), seed817301, conditional fixed OOF predictions; not training uncertainty or population sampling proof'}
(ROOT/'results.json').write_text(json.dumps(res,indent=2,allow_nan=False)+'\n');print(json.dumps({'summaries':summaries,'crossday':crossday,'transfer':transfer},indent=2))
