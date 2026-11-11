"""Rebuild manuscript numerical tables from fixed, supplied evidence projections.
No model, network or GPU calls. Source intervals are retained with their scope.
"""
from pathlib import Path
import csv,json,math,hashlib
from collections import defaultdict
import numpy as np
P=Path(__file__).resolve().parents[1]
def load(n):return json.loads((P/'data'/n).read_text())
def need(ok,msg):
 if not ok:raise ValueError(msg)
def dump(n,x):(P/'generated'/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
apps=load('applications.json');arms=['W_L4_M','W_P_M','L_L4_M','L_P_M','W_L4_D4','L_P_D4'];out={'applications':[]}
for a in apps:
 denoms=arms[:5];rr=[a['totals']['L_P_D4']/a['totals'][b] for b in denoms]
 need(np.allclose(rr,a['reported_ratios'],atol=1e-12,rtol=0),'Application totals/ratio mismatch')
 b=min(arms[:4],key=lambda k:a['totals'][k]);x=dict(a,means={k:v/a['formal_per_arm'] for k,v in a['totals'].items()},best_fixed_M=b,best_M_reduction=1-a['totals']['L_P_D4']/a['totals'][b])
 out['applications'].append(x)
qrows=list(csv.DictReader((P/'data/q32_measurements.csv').open()));tot=defaultdict(float);root=defaultdict(lambda:defaultdict(float));seen=set()
for r in qrows:
 key=(r['root'],r['arm'],int(r['round']));need(key not in seen,'Duplicate32Bslot');seen.add(key);t=float(r['service_s']);need(t>0 and math.isfinite(t),'32Btime');tot[r['arm']]+=t;root[r['root']][r['arm']]+=t
q=load('q32_recomputed.json');need(len(qrows)==96 and len(root)==4,'32B dimensions')
for k,v in tot.items():need(abs(v-q['totals'][k])<1e-9,'32B totals')
out['q32']=dict(totals=dict(tot),means={a:t/16 for a,t in tot.items()},root_sums=dict(root),worker=q['native_worker_by_arm'],caller=q['caller_by_arm'],whole_group_over_loop=tot['W_REF1G_M']/tot['W_REF1L_M'],local_group_over_loop=tot['L_REF1G_M']/tot['L_REF1L_M'],draft_over_best_M=tot['L_REF1G_D4']/tot['L_REF1G_M'])
qr=load('q8_root_sums.json');x=np.asarray(qr['sums'],float);need(x.shape==(8,16),'q8 root shape');qt=x.sum(axis=1)
qc=load('q8_recomputed.json');idx=np.random.Generator(np.random.PCG64(20261109)).integers(0,16,(10000,16));boot=x[:,idx].sum(axis=2)
# Use stored estimands and family memberships, not post-hoc selected winners.
for c in qc['contrasts']:
 i=qr['arms'].index(c['numerator']);j=qr['arms'].index(c['denominator']);ratio=qt[i]/qt[j];ci=np.quantile(boot[i]/boot[j],[.05/4/2,1-.05/4/2])
 need(abs(ratio-c['ratio'])<2e-12,'q8 ratio mismatch');need(np.max(np.abs(ci-c['adjusted_interval']))<2e-12,'q8 CI mismatch')
out['q8']=dict(totals=dict(zip(qr['arms'],qt.tolist())),contrasts=qc['contrasts'],root_sums=qr['sums'],roots=qr['roots'],interval_provenance='Independently recomputed from supplied complete arm/root sums; not raw receipt reread',primary_units=16,requests_represented=1024)
eq=load('q8_equal_work.json');out['equal_work']=[]
for c in eq['cells']:
 a=sum(c['q8']);b=sum(c['q4pair']);out['equal_work'].append(dict(c,ratio=a/b,root_ratios=[x/y for x,y in zip(c['q8'],c['q4pair'])],reduction=1-a/b))
out['factors']={}
for size,name in [('8B','factor8.json'),('14B','factor14.json')]:
 f=load(name)
 for c in f['all_fixed_controls']:need(abs(f['totals'][c['numerator']]/f['totals'][c['denominator']]-c['total_ratio'])<1e-12,'factor ratio')
 out['factors'][size]=f
bv=load('b570_inputs.json');out['vulkan_geometry']=[]
for name,v in bv['cells'].items():
 arr=np.asarray(v);need(arr.shape==(3,3),'Vulkan geometry shape');means=arr.mean(axis=1);out['vulkan_geometry'].append(dict(cell=name,means_ms=means.tolist(),ratio=float(means[2]/means[1]),paired_ratios=(arr[2]/arr[1]).tolist()))
w=load('q8_phase_work.json');out['q8_work']=w['work_by_k'];out['q8_phases']=w['arms'];out['historical']=load('historical_evidence.json')
out['vulkan_economics']=load('vulkan_economics.json');out['windows_r2']=load('windows_r2.json')
dump('analysis.json',out)
# Complete arms and fixed contrasts are also emitted as readable supplementary tables.
tex=[]
for a in out['applications']:
 label={'Qwen3-8B Linux/A5000':'Qwen3-8B','Qwen3-14B Linux/A5000':'Qwen3-14B'}.get(a['study'],a['study'].replace(' Linux/A5000',''))
 vals=' & '.join(f"{a['means'][k]:.4f}" for k in arms);tex.append(label+' & '+vals+r' \\')
(P/'generated/application_rows.tex').write_text('\n'.join(tex)+'\n')
qtex=[]
for a in ['W_REF1L_M','W_REF1G_M','L_REF1L_M','L_REF1G_M','W_REF1L_D4','L_REF1G_D4']:
 label=a.replace('_',r'\_');qtex.append(r'\texttt{'+label+'} & '+f"{tot[a]:.6f} & {tot[a]/16:.4f} & {q['native_worker_by_arm'][a]:.3f} & {q['caller_by_arm'][a]:.3f}"+r' \\')
(P/'generated/q32_rows.tex').write_text('\n'.join(qtex)+'\n')
# Sanity checks needed by manuscript values.
need(all(.1<a['best_M_reduction']<.3 for a in out['applications']),'application effects')
need(abs(out['q32']['whole_group_over_loop']-.9438357094)<1e-7,'Q32 headline')
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((P/'data').iterdir()) if f.is_file()}
dump('DATA_CHECKS.json',{'status':'PASS','application_ratios':15,'q32_raw_measurement_rows':96,'q8_root_aggregate_cells':128,'q8_interval_endpoints_recomputed':16,'vulkan_raw_timing_values':108,'method':'Local arithmetic/reanalysis of fixed supplied evidence; no GPU or private raw state replay','input_sha256':manifest})
print('Data reconciliation PASS: 15 application ratios; 96 Q32 rows; 16 q8 CI endpoints; 108 Vulkan times.')
