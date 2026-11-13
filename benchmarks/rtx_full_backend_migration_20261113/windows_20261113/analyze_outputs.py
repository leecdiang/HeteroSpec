"""Post-run only: all P/G records, trajectory differences and cross-contract Q errors."""
from pathlib import Path
import json,csv,math,statistics,datetime,subprocess
p=Path(__file__).resolve().parent;e=p/'evidence'
def put(name,x):
 with (e/name).open('x',encoding='utf8') as f:json.dump(x,f,indent=2)
records=json.loads((e/'ALL_RECORDS.json').read_bytes());panel=json.loads((e/'prepared/panel.json').read_bytes());indexed={(x['mode'],x['root'],x['block'],x['arm']):x for x in records if not x['warmup']}
table=[];gdiff=[]
for mode,blocks in [('P',4),('G',2)]:
 for root in [x['root'] for x in panel]:
  for b in range(blocks):
   r=indexed[mode,root,b,'R'];m=indexed[mode,root,b,'M']
   table.append(dict(mode=mode,root=root,block=b,length_bin=r['length_bin'],prompt_tokens=len(r['prompt_ids']),R_s=r['seconds'],M_s=m['seconds'],M_over_R=m['seconds']/r['seconds'],R_rows=r['rows'],M_rows=m['rows'],R_emitted=len(r['tokens']),M_emitted=len(m['tokens']),R_stop=r['stop'],M_stop=m['stop'],R_ttft_s=r['ttft_s'],M_ttft_s=m['ttft_s'],R_decode_per_emitted_s=r['continuation_s']/len(r['tokens']) if r['tokens'] else None,M_decode_per_emitted_s=m['continuation_s']/len(m['tokens']) if m['tokens'] else None))
   if mode=='G':
    a,c=r['tokens'],m['tokens'];first=next((i for i,(u,v) in enumerate(zip(a,c)) if u!=v),min(len(a),len(c)) if len(a)!=len(c) else None)
    gdiff.append(dict(root=root,block=b,R_length=len(a),M_length=len(c),exact_tokens_equal=a==c,first_divergent_zero_based_index=first,common_prefix_tokens=min(len(a),len(c)) if first is None else first,positional_equal_tokens=sum(u==v for u,v in zip(a,c)),R_stop=r['stop'],M_stop=m['stop'],R_text=r['text'],M_text=m['text'],R_tokens=a,M_tokens=c))
with (e/'ALL_PAIRED_SAMPLES.csv').open('x',encoding='utf8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
put('G_TRAJECTORY_DIFFERENCES.json',gdiff)
summary={}
for mode in ['P','G']:
 rows=[x for x in table if x['mode']==mode]
 summary[mode]=dict(pairs=len(rows),R_total_s=sum(x['R_s'] for x in rows),M_total_s=sum(x['M_s'] for x in rows),pooled_M_over_R=sum(x['M_s'] for x in rows)/sum(x['R_s'] for x in rows),paired_ratios_range=[min(x['M_over_R'] for x in rows),max(x['M_over_R'] for x in rows)],by_length_bin={str(b):dict(roots=4,geomean_M_over_R=math.exp(statistics.mean(math.log(x['M_over_R']) for x in rows if x['length_bin']==b))) for b in range(4)})
 if mode=='G':summary[mode].update(exact_trajectory_pairs=sum(x['exact_tokens_equal'] for x in gdiff),R_total_emitted=sum(x['R_emitted'] for x in rows),M_total_emitted=sum(x['M_emitted'] for x in rows),R_stops={stop:sum(x['R_stop']==stop for x in rows) for stop in ['cap','eog']},M_stops={stop:sum(x['M_stop']==stop for x in rows) for stop in ['cap','eog']},quality_equivalence='NOT_ESTABLISHED',task_scoring='NOT_EVALUATED')
put('P_G_SUMMARY.json',summary)
# Independent CPU array operations after GPU completion; never use cross-arm errors as admission.
import numpy as np
r=np.fromfile(e/'R-reference/capture-9002.f32',dtype='<f4').reshape(-1,151936);m=np.fromfile(e/'M-reference/capture-9102.f32',dtype='<f4').reshape(-1,151936);assert r.shape==m.shape
errors=[]
for i,(a,b) in enumerate(zip(r,m)):
 delta=b.astype('float64')-a.astype('float64');bits=int(np.count_nonzero(a.view('uint32')!=b.view('uint32')));den=float(np.linalg.norm(a.astype('float64')))
 errors.append(dict(requested_row_index=i,position=min((i+1)*32,764)-1 if i<24 else 764+i-24,bitwise_different_values=bits,max_abs=float(np.max(np.abs(delta))),relative_L2=float(np.linalg.norm(delta))/den if den else None,R_argmax=int(np.argmax(a)),M_argmax=int(np.argmax(b))))
put('CROSS_ARM_FIXED_DIAGNOSTIC_ERRORS.json',dict(scope='same historical764 prefix+same128 forced tokens;all requested full vocab vectors;different numerical contracts;no admission tolerance',vocab=151936,requested_rows=len(errors),total_float_values=int(r.size),total_different_float_bitpatterns=sum(x['bitwise_different_values'] for x in errors),rows=errors))
rows=[json.loads(x) for x in (e/'ledger.jsonl').read_bytes().splitlines()];passes=[x for x in rows if x['kind']=='PHASE_PASS'];debits=[x for x in rows if x['kind']=='RESERVED_BEFORE_CREATE']
put('RESOURCE_CONSUMPTION.json',dict(requests_reserved=sum(x['requests'] for x in debits),rows_reserved=sum(x['rows'] for x in debits),deployments=len(debits),actual_completed_requests=sum(x['actual_requests'] for x in passes),actual_completed_rows=sum(x['actual_rows'] for x in passes),formal_requests=192,qualification=16,warmups=12,failed_inference_requests=0,pre_model_preflight_stop=1,model_loads=len(debits),contexts=len(debits),wall_s=datetime.datetime.fromisoformat(rows[-1]['utc']).timestamp()-debits[0]['first_wall'],phase_times=passes,temperature_range_C=[min(x['temperature'] for x in rows if x['kind']=='RESOURCE_SAMPLE'),max(x['temperature'] for x in rows if x['kind']=='RESOURCE_SAMPLE')],max_observed_GPU_used_bytes=max(x['used_bytes'] for x in rows if x['kind']=='RESOURCE_SAMPLE'),physical_launch_count='UNKNOWN',implicit_contexts='UNKNOWN',bounds='request/row/deployment/window/evidence controls;not physical GPU launch contract'))
print(json.dumps(dict(P=summary['P'],G={k:v for k,v in summary['G'].items() if k!='by_length_bin'})))
