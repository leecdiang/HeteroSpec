"""Standard-library-only public byte and descriptive-statistic replay. Zero GPU.

Reassemble ordered XZ parts, verify every public record, then independently
recompute complete-panel totals from native receipts. Private binary commitments
do not constitute access to or independent numerical replay of their payloads.
"""
from pathlib import Path
from collections import defaultdict
import argparse,hashlib,json,lzma,tempfile
def read(p):return json.loads(Path(p).read_text())
def digest(b):return hashlib.sha256(b).hexdigest()
def replay(folder):
 bundle=read(folder/'BUNDLE.json');index=read(folder/'TEXT_INDEX.json')['files'];records={};count=0;total=hashlib.sha256();size=0
 with tempfile.TemporaryFile()as f:
  for item in bundle['ordered_parts']:
   b=(folder/item['file']).read_bytes();assert len(b)==item['bytes']and digest(b)==item['sha256'];f.write(b);total.update(b);size+=len(b)
  assert size==bundle['bytes']and total.hexdigest()==bundle['sha256'];f.seek(0)
  with lzma.open(f,'rt')as decoded:
   for line in decoded:
    row=json.loads(line);item=index[count];b=row['text'].encode();assert row['path']==item['path']and len(b)==item['public_bytes']and digest(b)==item['public_sha256'];count+=1
    path=row['path']
    if path.startswith('work/')and path.endswith('.json')and('/panel-01/'in path or path.endswith(('reference/COMPLETE.json','qualification-03/CORE_GATES_COMPLETE.json','closure-03/QUALIFICATION_COMPLETE.json','INHERITED_ACCOUNTING.json'))):records[path]=json.loads(row['text'])
 assert count==bundle['records']==len(index);costs=read(folder/'COSTS.json');assert costs['cumulative_Q32_requests']<=512 and costs['cumulative_Q32_reserved_rows']<=2000000
 result=dict(passed=True,records=count,bundle_sha256=bundle['sha256'],cumulative_requests=costs['cumulative_Q32_requests'],reserved_rows=costs['cumulative_Q32_reserved_rows'],reference_frozen=records.get('work/reference/COMPLETE.json',{}).get('own_R_frozen',False),eligibility_complete=records.get('work/closure-03/QUALIFICATION_COMPLETE.json',{}).get('passed',False),complete_performance_panel=False,native_requests=0,limitations='Sanitized public text/manifest byte replay and native receipt arithmetic; private vectors/KV/operand payloads are not independently rechecked here')
 if 'work/panel-01/COMPLETE.json'not in records:return result
 plan=records['work/panel-01/PLAN.json'];assert plan['measured']==96 and plan['primers']==48 and len(plan['workers'])==24;totals=defaultdict(float);rounds=defaultdict(lambda:defaultdict(float));rows=[]
 for worker in plan['workers']:
  prefix='work/panel-01/runs/'+worker['id']+'/';assert records[prefix+'HOST.json']['status']=='COMPLETE';meta=records[prefix+'native/result.json'];assert meta['status']=='COMPLETE';draft=worker['arm'].endswith('_D4');assert meta['total_observed_API_calls']['context_creates']==(2 if draft else 1)
  cap=records[prefix+'native/CAPABILITY.json'];assert cap['target_context']['outputs_max']==32 and cap['cuda_graphs']is False
  assert cap['residency']==('matched'if draft else'target_only')and cap['atomic_columns']==1
  job=records['work/panel-01/'+worker['job']]
  for entry in job['inputs'][2:]:
   root=entry['input']['id'];r=records[prefix+'native/'+entry['name']+'/receipt.json'];wanted=plan['expected_endpoints'][root];assert {k:r[k]for k in('ids','eog','stop_reason')}==wanted
   assert not r['capture']and all(v==0 for v in r['observed_API_calls_within_service'].values());assert r['target_output_reserve']==32 and r['k']==3
   width=sum(int(k)*v for k,v in r['target_physical_width_hist'].items());assert width==r['prompt_tokens']+(4*len(r['cycles'])if draft else len(r['ids'])-1)
   if not draft:assert r['draft_calls']==0 and not r['draft_physical_width_hist']
   value=float(r['service_seconds']);assert value>0;totals[worker['arm']]+=value;rounds[worker['round']][worker['arm']]+=value;rows.append(dict(round=worker['round'],position=worker['position'],arm=worker['arm'],root=root,service_s=value))
 assert len(rows)==96 and len(totals)==6;result.update(complete_performance_panel=True,descriptive_only=True,measured=96,primers=48,total_service_s=dict(totals),round_total_service_s={str(k):dict(v)for k,v in rounds.items()},rows=rows)
 if(folder/'ANALYSIS.json').exists():
  saved=read(folder/'ANALYSIS.json');assert saved['complete']and saved['total_service_s']==result['total_service_s'];result['saved_statistics_recomputed']=True
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();result=replay(a.folder)
 with a.out.open('x')as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({k:v for k,v in result.items()if k not in('rows','round_total_service_s')}))
if __name__=='__main__':main()
