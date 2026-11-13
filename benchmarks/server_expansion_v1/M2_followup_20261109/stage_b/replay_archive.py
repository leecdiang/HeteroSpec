"""Model-free public archive byte check and exact diagnostic statistic replay."""
from pathlib import Path
import argparse,gzip,hashlib,json
def read(p):return json.loads(p.read_text())
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir()
 manifest=read(a.bundle/'BUNDLE.json');b=(a.bundle/manifest['file']).read_bytes();assert len(b)==manifest['bytes']and hashlib.sha256(b).hexdigest()==manifest['sha256']
 index={x['path']:x for x in read(a.bundle/'TEXT_INDEX.json')['files']};records={}
 with gzip.open(a.bundle/manifest['file'],'rt')as z:
  for line in z:
   row=json.loads(line);name=row['path'];raw=row['text'].encode();item=index[name];assert name not in records
   assert len(raw)==item['public_bytes']and hashlib.sha256(raw).hexdigest()==item['public_sha256'];records[name]=row['text']
 assert set(records)==set(index)and len(records)==manifest['records']
 results=[n for n in records if n.endswith('/RESULTS.json')and n.startswith('pr210-stage-b-20261109-')]
 outputs=[]
 for name in results:
  prior=json.loads(records[name]);contrast=[];rows=prior['rows'];prefix=name.rsplit('/',1)[0]
  assert sum(x['kind']=='measurement'for x in rows)==16 and sum(x['kind']=='primer'for x in rows)==8
  plan=json.loads(records[prefix+'/TIMING_PLAN.json']);workers={x['name']:x for x in plan['workers']}
  for row in rows:
   raw=json.loads(records[prefix+'/runs/'+row['worker']+'/native/'+row['name']+'/receipt.json'])
   assert all(row[k]==v for k,v in raw.items()),'Derived table differs from original native receipt'
   worker=workers[row['worker']];item=next(x for x in worker['job']['diagnostics']if x['name']==row['name'])
   assert item['ids']==row['ids']and item['position']==row['position']and item['execution']==row['execution']
   assert worker['core']==row['core']and worker['round']==row['round']
   width=8 if row['execution']=='q8'else 4;assert row['physical_width_histogram']=={str(width):8//width}
   assert row['online_state_imports']==row['online_state_exports']==row['online_heavy_captures']==0
  qual=json.loads(records[prefix+'/QUALIFIED.json']);assert qual['passed']and len(qual['cells'])==32
  binary={x['path']:x for x in read(a.bundle/'BINARY_CAPTURE_INDEX.json')['files']}
  freeze=json.loads(records[prefix+'/REFERENCE_DERIVED_FREEZE.json'])
  for f in freeze['files']:
   path=f['path'].removeprefix('$HS_ROOT/');assert binary[path]['sha256']==f['sha256']and binary[path]['bytes']==f['bytes'],'Frozen oracle payload commitment changed'
  for cell in qual['cells']:
   assert cell['passed']and cell['initial_frontier']['equal']and cell['initial_KV']['equal']and cell['final_KV']['equal']
   actual=prefix+'/runs/qualification-'+cell['core']+'-'+str(cell['origin'])+'/native/'+cell['name']
   oracle=prefix+'/runs/R-trunk-'+str(cell['origin'])+'/native/trunk/captures/'
   for j,vector in enumerate(cell['vectors']):
    assert vector['equal']and vector['actual_sha256']==binary[actual+'/row-'+str(j)+'.f32']['sha256']and vector['reference_sha256']==binary[oracle+str(cell['position']+j+1)+'/frontier.f32']['sha256']
   assert cell['final_KV']['actual_raw_sha256']==binary[actual+'/final-sequence.bin']['sha256']
   assert cell['final_KV']['reference_raw_sha256']==binary[oracle+str(cell['position']+8)+'/sequence.bin']['sha256']
  for core in ('loop4','packed'):
   for pos in (248,252):
    cells=[x for x in rows if x['kind']=='measurement'and x['core']==core and x['position']==pos];assert len(cells)==4
    total={e:sum(x['operation_s']for x in cells if x['execution']==e)for e in ('q4pair','q8')};contrast.append(dict(core=core,position=pos,total_s=total,q8_over_q4pair=total['q8']/total['q4pair']))
  assert contrast==prior['contrasts'];outputs.append(dict(path=name,contrasts=contrast))
 save(a.out/'CHECKED.json',dict(passed=True,records=len(records),replayed_results=outputs,native_requests=0,scope='Exact exported-text byte and scalar-statistic consistency; not numerical requalification or kernel profiling'))
 print(json.dumps(dict(passed=True,records=len(records),results=len(outputs))),flush=True)
if __name__=='__main__':main()
