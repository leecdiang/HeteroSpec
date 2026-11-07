"""Independent CPU prior-evidence restoration and cost/qualification audit."""
from pathlib import Path
import json,hashlib,zipfile,statistics,math,csv,time
R=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,x):(R/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
checks=0;errors=[]
def check(x,m):
 global checks;checks+=1
 if not x:errors.append(m)
restores=[]
prior_dirs=sorted((R/'archive').glob('prior-*'))
for label,receipt in [('core','C:/hs/b570-closeout-v1/ARCHIVE_RESTORE.json'),('supplement','C:/hs/b570-closeout-audit-v1/SUPPLEMENT_ARCHIVE_RESTORE.json')]:
 d=load(receipt);archive=Path(d['archive']);check(sha(archive)==d['archive_sha256'],label+' archive SHA')
 candidates=sorted((R/'archive').glob('prior-'+label+'-*'))
 dest=candidates[-1] if candidates else R/'archive'/('prior-'+label+'-'+str(time.time_ns()));dest.mkdir(exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  check(z.testzip() is None,label+' all CRC');index=json.loads(z.read('INDEX.json'))
  for h,m in index['objects'].items():check(hashlib.sha256(z.read('objects/'+h)).hexdigest()==h,label+' object '+h)
  for name,m in index['files'].items():
   target=dest/name;check(target.resolve().is_relative_to(dest.resolve()),'safe restore '+name)
   target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():target.write_bytes(z.read('objects/'+m['sha256']))
   check(sha(target)==m['sha256'],label+' restored '+name)
 restores.append(dict(label=label,path=str(dest),archive=str(archive),sha256=d['archive_sha256'],files=len(index['files']),objects=len(index['objects'])))
 print('RESTORED',label,len(index['files']),flush=True)
core=Path(restores[0]['path']);supp=Path(restores[1]['path'])
assets=load('C:/hs/b570-closeout-v1/ASSET_POST.json')['checked'];actual={}
for p,d in assets.items():
 h=sha(p);check(h==d['sha256'] and Path(p).stat().st_size==d['bytes'],'asset '+p);actual[p]=dict(sha256=h,bytes=Path(p).stat().st_size)
save('ASSET_MANIFEST.json',dict(status='PASS' if not errors else 'FAIL',checked=actual,prior_snapshots=restores,scope='full-byte reread; no model requests'))
eog=set(load(core/'TOKENIZATION_PROOF.json')['runtime_eog_ids'])
records=[]
for base in [core,supp]:
 for p in (base/'raw').glob('*/RESULT.json'):
  r=load(p);caps=[base/f for f in r['files'] if f.endswith('/capture.json')]
  check(len(caps)==1,'one raw '+r['unit_id']);x=load(caps[0]);ids=x['ids'];flags=x['eog'];cap=r['config'].get('cap',128)
  check(len(ids)==len(flags)>0 and all(type(i)==int and 0<=i<151936 for i in ids),'raw vocab '+r['unit_id'])
  check(flags==[i in eog for i in ids],'EOG '+r['unit_id'])
  n=min(cap,next((i+1 for i,t in enumerate(ids) if t in eog),len(ids)))
  ep=dict(ids=ids[:n],eog=flags[:n],reason='EOG' if ids[n-1] in eog else 'CAP',raw_suffix=len(ids)-n)
  check(ep==r['endpoint'],'endpoint '+r['unit_id'])
  for f,h in r['files'].items():check(sha(base/f)==h,'raw hash '+f)
  r['independent_endpoint']=ep;r['archive_root']=str(base);r['raw_ids']=ids;r['raw_eog']=flags;records.append(r)
rows=[]
for p in sorted((core/'derived').glob('*.csv')):
 for row in csv.DictReader(p.open(encoding='utf-8-sig',newline='')):
  rr=[r for r in records if not r['warm'] and r['unit_id'].split('/')[0]==row['stage'] and r['task']==row['task'] and r['config'].get('cap',128)==int(row['cap'])]
  def median(label):
   rs=[r for r in rr if r['config'].get('label')==label and (not int(row['k']) or r['config'].get('width_k',0)==int(row['k']))]
   return statistics.median(r['metrics'][row['timer']] for r in rs)
  a,b=median(row['baseline']),median(row['candidate'])
  for v,w in [(a,float(row['baseline_median_ms'])),(b,float(row['candidate_median_ms'])),(a/b,float(row['speed_ratio']))]:check(math.isclose(v,w,rel_tol=1e-12,abs_tol=1e-9),'CSV '+p.name+row['task']+row['timer'])
  rows.append(dict(csv=p.name,**row))
check(len(list((core/'derived').glob('*.csv')))==66 and len(rows)==744,'66 CSV 744 rows')
bf=[r for r in records if r['unit_id'].startswith('B/') and not r['warm']];neg=[]
for task in load(core/'INPUTS.json')['shared']+load(core/'INPUTS.json')['unused']:
 rr=[r for r in bf if r['task']==task['id'] and r['config']['label']=='R_reference'];check(len(rr)==4,'B four paid R '+task['id'])
 for r in rr:check(r['endpoint']==rr[0]['endpoint'],'stable B R '+task['id'])
 for r in [r for r in bf if r['task']==task['id'] and r['config']['label']!='R_reference']:
  if any(r['endpoint'][k]!=rr[0]['endpoint'][k] for k in ['ids','eog','reason']):neg.append(dict(task=r['task'],label=r['config']['label'],unit=r['unit_id']))
check(len(neg)==8 and {x['task'] for x in neg}=={'MBPP/72'} and {x['label'] for x in neg}=={'N1_repaired','T_matched'},'all four N1 and T MBPP72 failures retained')
# Bind available exact parent arrays, not just reference qualification labels.
dev=load(R/'DEV_INPUTS.json');hist=load(core/'dependencies/B570/HISTORICAL_EXPECTED.json');parents={}
for inp in dev:
 task=inp['id']
 for label in ['R_reference','N1_repaired','E_k1_ub2','M_ordinary_same_k1_ub2','N0_ordinary']:
  match=[]
  for r in records:
   c=r['config']
   if r['warm'] or r['task']!=task or c.get('cap',128)!=128:continue
   native=c.get('native',False)
   ok=(label=='R_reference' and not native and not c.get('matched') and c['prefill']==128 and c['ub']==128)
   ok|=(label=='N1_repaired' and native and c.get('k')==2 and c['prefill']==128 and c['ub']==1 and not c.get('plain'))
   ok|=(label=='E_k1_ub2' and native and c.get('k')==1 and c['prefill']==128 and c['ub']==2 and not c.get('plain'))
   ok|=(label=='M_ordinary_same_k1_ub2' and native and c.get('k')==1 and c['prefill']==2 and c['ub']==2 and c.get('plain',False))
   ok|=(label=='N0_ordinary' and native and c.get('k')==2 and c['prefill']==1 and c['ub']==1 and not c.get('plain'))
   if ok:
    log=Path(r['archive_root'])/'sessions'/r['session']/'stderr.log'
    if log.exists() and 'offloaded 37/37 layers to GPU' in log.read_text(encoding='utf8',errors='replace'):
     match.append(r)
  if match:
   x=match[0];check(all(q['raw_ids']==x['raw_ids'] and q['raw_eog']==x['raw_eog'] for q in match),'history stability '+task+'/'+label)
   parents[task+'/'+label]=dict(raw_ids=x['raw_ids'],raw_eog=x['raw_eog'],endpoint=x['endpoint'],source_units=[q['unit_id'] for q in match],source='PR63 restored core/supplement')
  elif label=='R_reference' and task+'/R/1' in hist:
   x=hist[task+'/R/1'];parents[task+'/'+label]=dict(raw_ids=x['ids'],raw_eog=x['eog'],endpoint=dict(ids=x['ids'],eog=x['eog'],reason=x['endpoint'],raw_suffix=0),source='retained scalar R export; complete scalar output')
  elif label=='N1_repaired' and task+'/R/1' in hist:
   x=hist[task+'/R/1'];parents[task+'/'+label]=dict(endpoint=dict(ids=x['ids'],eog=x['eog'],reason=x['endpoint']),source='prior N1 qualification against fixed scalar R; raw historical parent unavailable',raw_history_unavailable=True)
save('HISTORICAL_PARENTS.json',parents)
save('STAGE0.json',dict(status='PASS' if not errors else 'FAIL',checks=checks,errors=errors,restores=restores,records=len(records),csv_files=66,cost_rows=744,negatives=neg,assets_checked=len(actual),model_requests=0))
print('STAGE0',checks,len(errors),errors[:12],flush=True)
assert not errors
