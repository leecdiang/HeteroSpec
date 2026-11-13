"""Public text/accounting replay; never revalidates private tensor bytes or GPU."""
import argparse,hashlib,io,json,tarfile
from pathlib import Path

def main(evidence,out):
 evidence=Path(evidence);out=Path(out);assert not out.exists();index=json.loads((evidence/'PUBLIC_TEXT_INDEX.json').read_text());expected={x['file']:x for x in index};texts={}
 with tarfile.open(evidence/'PUBLIC_TEXT_PACKET.tar.gz','r:gz') as tar:
  for m in tar:
   assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and m.name in expected and m.name not in texts
   data=tar.extractfile(m).read();assert len(data)==expected[m.name]['bytes'] and hashlib.sha256(data).hexdigest()==expected[m.name]['sha256'];texts[m.name]=data
 assert set(texts)==set(expected)
 def load(n):return json.loads(texts[n])
 parent=load('original/STATE.json');state=load('successor/STATE.json');m=load('successor/MANIFEST.json');assert m['approved']==dict(requests=43,rows=40000,deployments=4,GPU_seconds=14400)
 assert all(state['requests'][k]==v for k,v in parent['requests'].items());assert len(state['requests'])==state['consumed']['requests']<=43;assert sum(x['rows'] for x in state['requests'].values())==state['consumed']['rows']<=40000;assert state['consumed']['deployments']<=4;assert load('original/WINDOW.json')==load('successor/WINDOW.json')
 episodes=[];plans={};cases={c['id']:c for c in m['cases']}
 for n,data in texts.items():
  if not n.endswith('/EPISODE.json'):continue
  e=json.loads(data);cert=n.split('/')[0]+'/certificates/'+e['episode']+'.json'
  if cert not in texts:continue
  assert load(cert)['status']=='PASS';assert e['free_generation'] and e['n_ctx']==4096;cs=cases[e['case']]
  for r in e['requests']:
   q=r['prompt']['canonical_ids'];c=r['consumer'];y=c['sampled_ids'];k=r['retained'];assert r['native_head_after']==len(q)+len(y)-1 and r['logical_ids']==q+y and r['pending']==y[-1]
   assert state['requests'][r['id']]['status']=='COMPLETED';assert r['rows']==state['requests'][r['id']]['rows'];assert ''.join(p['piece_hex'] for p in c['pieces'])==c['parser_input_hex'];wire=json.loads(c['wire_response_json']);assert wire['choices'][0]['message']==c['client_message'];assert wire['usage']['completion_tokens']==len(y)
   if r['turn']==0:assert q==cs['initial_ids'] and r['prompt']['history']==[cs['users'][0]] and k==0
   elif e['stage']!='COLD':
    old=e['requests'][0];logical=old['logical_ids'];lcp=next((i for i,(a,b) in enumerate(zip(logical,q)) if a!=b),min(len(logical),len(q)));keep=min(lcp,old['native_head_after']);keep-=keep==len(q);assert k==keep and r['prompt']['history']==old['consumer']['history_after']+[cs['users'][1]]
   calls=[x for x in e['calls'] if x['request']==r['id']];assert sum((x['input_ids'] for x in calls),[])==(q if e['stage']=='COLD' else q[k:])+y[:-1];assert sum(x['rows'] for x in calls)==r['rows']
  if e['dispatch'] is not None:
   d=e['dispatch'];assert d['physical_calls']==len(d['physical']);assert d['physical_rows']==sum(r['rows'] for r in e['requests']);assert all(x['API_width']==x['physical_rows'] and x['physical_calls']==1 and x['returncode']==0 for x in d['physical'])
   if e['stage']=='HEAVY':assert d['loop4_marked_nodes']>0 and d['GPU_nodes']>0;plans[(e['case'],e['arm'])]=[(x['position'],x['width'],x['expected_extents']) for x in d['plan']]
  episodes.append(dict(episode=e['episode'],stage=e['stage'],case=e['case'],arm=e['arm']))
 geometry={c:plans.get((c,'W'))!=plans.get((c,'L')) for c in ['C0','C1'] if (c,'W') in plans and (c,'L') in plans}
 if 'successor/ACTUAL_GEOMETRY_GATE.json' in texts:
  g=load('successor/ACTUAL_GEOMETRY_GATE.json');assert all(g['cases'][c]['actual_partition_distinct']==v for c,v in geometry.items())
 raw=[x for x in load('closeout/ARCHIVE_INDEX.json') if '/episodes/' in x['name'] and x['name'].endswith(('.f32','.kv'))];assert sum(x['bytes'] for x in raw)==state['raw_bytes']
 result=dict(status='PASS_PUBLIC_TEXT_INPUT_CHAIN_ACCOUNTING_AND_RECORDED_DISPATCH',members=len(texts),consumed=state['consumed'],passed_episodes=episodes,actual_recorded_partition_difference=geometry,raw_index_bytes=sum(x['bytes'] for x in raw),raw_tensor_bytes_read=0,model_or_GPU_calls=0,limitation='Recorded certificates/indices are not independent revalidation of original tensor bytes; private archive/original-byte audit was performed separately. No free-EOG, performance or complete261-suite claim follows.')
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','members','consumed','actual_recorded_partition_difference']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);p.add_argument('--out',required=True);a=p.parse_args();main(a.evidence,a.out)
