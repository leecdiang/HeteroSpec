"""Independent ZIP/fresh-path/native raw audit; summaries are not authorities."""
from __future__ import annotations
import argparse,collections,json,subprocess,zipfile,re
from pathlib import Path
import numpy as np
from contracts import *
from state_distance import layout,splice,selector_geometry
ZIP_SHA='2e6114e9a3019b71d7e7a1ac55dd483ee8191ce6fcb99310fcbeda588992b0b1'
B101='benchmarks/b570_final_causal_closeout_v1/'
B103='benchmarks/b570_kv_subset_followup_v1/'
def gitbytes(repo,commit,path):return subprocess.check_output(['git','show',commit+':'+path],cwd=repo)
def verify_commit_file(repo,commit,path,actual):
 b=gitbytes(repo,commit,path);require(Path(actual).read_bytes()==b,'commit body mismatch: '+path);return {'commit':commit,'repository_path':path,'actual_path':str(actual),'git_blob':gitblob(b),'sha256':digest(b)}
def restore_archive(archive,manifest,fresh):
 require(sha(archive)==ZIP_SHA,'PR103 final ZIP hash mismatch');require(not fresh.exists(),'fresh restore path already exists');rows=manifest['files'];names=[r['path'] for r in rows];require(len(names)==len(set(names)),'duplicate manifest path');fresh.mkdir(parents=True)
 with zipfile.ZipFile(archive) as z:
  require(len(z.infolist())==len(names) and set(z.namelist())==set(names),'ZIP/manifest members differ')
  for row in rows:
   q=(fresh/row['path']).resolve();require(q.is_relative_to(fresh.resolve()),'ZIP path escape');q.parent.mkdir(parents=True,exist_ok=True)
   with z.open(row['path']) as src,q.open('xb') as dst:
    while b:=src.read(1024*1024):dst.write(b)
   require(q.stat().st_size==row['bytes'] and sha(q)==row['sha256'],'fresh restored hash mismatch: '+row['path'])
 return {'scope':'LOCAL_FRESH_RESTORE','archive_sha256':sha(archive),'files_verified':len(rows),'actual_root':str(fresh.resolve()),'independent_machine':'NOT_PERFORMED','remote_raw_availability':'REMOTE_PENDING'}
def baseline_expected(base,repo):
 pins=[verify_commit_file(repo,BASE101,B101+name,base/name) for name in ('STUDY_RECORDS.json','DONORS.json','INPUTS.json','native/worker.cpp','code/controller100.py','code/common98.py','code/verify100.py','F0_BASE.json','ARCHIVE_MANIFEST.json')]
 source_freeze=read(base/'F0_BASE.json');source_pins=[]
 for name in ('baseline/source/llama-kv-cache.cpp','baseline/source/models/llama.cpp'):
  pin=next(x for x in source_freeze['runtime_files'] if x['path']==name);p=base/name;require(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'source body differs from commit-bound F0: '+name);source_pins.append(dict(pin,actual_path=str(p),binding='Git-pinned PR101 F0_BASE runtime_files'))
 pins+=source_pins
 archive_pins={p['path']:p for p in read(base/'ARCHIVE_MANIFEST.json')['files']}
 def bound_file(name):
  require(name in archive_pins,'baseline evidence absent from Git-pinned archive manifest');p=base/name;pin=archive_pins[name];require(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'baseline raw/identity/stderr pin mismatch: '+name);return p
 geometry_proofs=[];identities=set()
 ds=read(base/'DONORS.json');rr=read(base/'STUDY_RECORDS.json');res=Resolver(base,base);expected={};raw_refs={};checked=[]
 for rec in rr:
  if rec['phase']!='P2':continue
  for name in (rec['raw_path'],rec['raw_path'].replace('.RESULT.json','.REQUEST.json'),rec['evidence_path'],rec['identity_path']):bound_file(name)
  if rec['identity_path'] not in identities:
   identities.add(rec['identity_path']);ip=read(bound_file(rec['identity_path']));require(ip['owned_pid']==rec['owned_pid'] and ip['status']=='PASS' and not ip['api_layer_loaded'],'baseline process identity')
   for m in ip['modules']:
    rel=str(Path(m['path']).relative_to(base)).replace('\\','/');require(rel in archive_pins and archive_pins[rel]['sha256']==m['sha256'],'baseline runtime module not manifest-bound')
   stderr=str(Path(rec['identity_path']).parent/'stderr.log').replace('\\','/');sp=bound_file(stderr);txt=sp.read_text(encoding='utf8')
   for key,value in [('n_head_kv',8),('n_embd_head_k',128),('n_embd_head_v',128)]:require(re.search(r'print_info: '+key+r'\s*= '+str(value)+r'\b',txt),'native geometry differs: '+key)
   geometry_proofs.append({'path':str(sp),'sha256':sha(sp),'n_head_kv':8,'n_embd_head_k':128,'n_embd_head_v':128})
  x=res.record_file(rec['raw_path'],rec['raw_sha256']);kv,log=rec['slot_config']['restore_donors'];task=rec['task'];e=validate_endpoint(x,x['prompt_ids'],rec['owned_pid'],rec['observation_mode']);tr=res.record_file(rec['evidence_path'],rec['evidence_sha256']);validate_channel(tr,x,x['prompt_ids'],rec['owned_pid'],rec['observation_mode'])
  k=dict(ds[task+'|'+kv]['KV'],path='baseline/pr99/'+ds[task+'|'+kv]['KV']['path']);l=dict(ds[task+'|'+log]['logits'],path='baseline/pr99/'+ds[task+'|'+log]['logits']['path']);validate_restore(x,res,k,l);key=task+'|'+kv+log
  require(key not in expected or expected[key]==e,'baseline P2 repeats differ');expected[key]=e;raw_refs.setdefault(key,[]).append({'path':str(base/rec['raw_path']),'sha256':rec['raw_sha256'],'slot':rec['slot'],'pid':rec['owned_pid']});checked.append(rec['slot'])
 require(set(expected)=={task+'|'+k+l for task in CASES for k in ('A','B') for l in ('A','B')},'baseline raw full-cross coordinate missing')
 return expected,{'commit_pins':pins,'raw_references':raw_refs,'P2_raw_records_checked':len(checked),'native_geometry_proofs':geometry_proofs}
def coordinate_set(plan):
 requests=plan['requests'];ids=[s['id'] for s in requests];require(len(ids)==len(set(ids)),'duplicate slot')
 coords={(s['task'],s['recipient'],s['selector'],s['repeat']) for s in requests};selectors={s['selector'] for s in requests};repeats={s['repeat'] for s in requests};expected={(t,r,k,i) for t in CASES for r in ('A','B') for k in selectors for i in repeats}
 require(len(coords)==len(requests) and coords==expected and repeats=={0,1},'missing/duplicate Cartesian coordinate')
 require(selectors=={'EMPTY','ALL','K_all','V_all','K_layer0','V_layer0','KV_layer0','KV_early','KV_middle','KV_late','KV_prefix128','KV_tail128'},'historical selector inventory changed')
 for s in requests:
  require(s['donor']==('B' if s['recipient']=='A' else 'A'),'direction reversed')
  require(s['stage']==('control' if s['selector'] in ('EMPTY','ALL') else 'cross'),'stage mismatch')
  require(digest(encoded({k:v for k,v in s.items() if k not in ('id','order','audit')}))[:24]==s['id'],'slot hash mismatch')
 return requests
def audit(fresh,base,repo,output):
 plan=read(fresh/'PLAN.json');requests=coordinate_set(plan);freeze=read(fresh/'FREEZE.json');original=Path(next(p['path'] for p in freeze['inputs'] if Path(p['path']).name=='PLAN.json')).parent;res=Resolver(fresh,original)
 verify_commit_file(repo,REG103,B103+'registration/F0.json',fresh/'FREEZE.json')
 for pin in freeze['inputs']:require(digest(res.payload(pin))==pin['sha256'],'restored frozen input differs')
 external=[]
 for pin in freeze['runtime']:
  p=Path(pin['path']);require(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'external frozen actor/model mismatch: '+str(p));external.append(dict(pin,scope='READ_ONLY_EXTERNAL_RUNTIME_SOURCE_MODEL_NOT_RELOCATED'))
 expected,baseline_proof=baseline_expected(base,repo);ds=read(fresh/'DONORS.json');states={};mixproof={};rows=[]
 ledger=[json.loads(s) for s in (fresh/'LEDGER.jsonl').read_text().splitlines()];starts=[v for v in ledger if v['event']=='REQUEST_STARTED'];require(len(starts)==len(requests) and {v['slot'] for v in starts}=={s['id'] for s in requests},'ledger starts mismatch')
 for s in requests:
  receipt=read(fresh/'receipts'/(s['id']+'.json'));require(receipt['status']=='COMPLETED' and receipt['slot']==s,'failed/mismatched slot receipt');rec=receipt['record'];require(rec['slot']==s['id'] and rec['task']==s['task'] and rec['source_commit']==REG103,'record identity')
  x=res.record_file(rec['raw_path'],rec['raw_sha256']);request_path=rec['raw_path'].replace('.RESULT.json','.REQUEST.json');req=read(res.resolve(request_path));require(req['request_id']==x['request_id'] and req['prompt_ids']==plan['cases'][s['task']]['prompt_ids'],'native REQUEST/RESULT mismatch')
  require(req['prefill_schedule']==[] and req['restore100']['donor_labels']==[s['restore_label'],s['recipient']] and not req['operator_capture'],'wrong restore direction/conditions')
  e=validate_endpoint(x,req['prompt_ids'],rec['owned_pid'],'heavy');require(e==receipt['endpoint'],'receipt endpoint is not native output');trace=res.record_file(rec['evidence_path'],rec['evidence_sha256']);validate_channel(trace,x,req['prompt_ids'],rec['owned_pid'],'heavy')
  require(rec['evidence_path'].endswith('.trace.json'),'memory masquerading as heavy trace');identity=res.record_file(rec['identity_path'],rec['identity_sha256']);require(identity['owned_pid']==rec['owned_pid'] and identity['status']=='PASS' and not identity['api_layer_loaded'],'native identity')
  for m in identity['modules']:
   require(any(str(Path(p['path']).resolve()).lower()==str(Path(m['path']).resolve()).lower() and p['sha256']==m['sha256'] for p in freeze['runtime']),'incorrect loaded runtime')
  life=read(res.resolve(str(Path(rec['identity_path']).parent/'LIFECYCLE.json')));require(life['pid']==rec['owned_pid'] and life['returncode']==0 and not life['failed'],'worker lifecycle')
  block=s['id'];owned=[v for v in ledger if v.get('block')==block and v['event']=='OWNED_PID'];done=[v for v in ledger if v.get('slot')==block and v['event']=='REQUEST_COMPLETED'];closed=[v for v in ledger if v.get('block')==block and v['event']=='WORKER_CLOSED']
  require(len(owned)==len(done)==len(closed)==1 and owned[0]['pid']==done[0]['pid']==closed[0]['pid']==rec['owned_pid'],'ledger PID linkage')
  k=dict(ds[s['task']+'|'+s['restore_label']]['KV'],path='baseline/pr99/'+ds[s['task']+'|'+s['restore_label']]['KV']['path']);l=dict(ds[s['task']+'|'+s['recipient']]['logits'],path='baseline/pr99/'+ds[s['task']+'|'+s['recipient']]['logits']['path']);t0=validate_restore(x,res,k,l)
  mk=(s['task'],s['recipient'],s['selector']);n=len(req['prompt_ids'])
  if mk not in mixproof:
   for side in ('A','B'):
    sk=(s['task'],side)
    if sk not in states:states[sk]=res.payload(dict(ds[s['task']+'|'+side]['KV'],path='baseline/pr99/'+ds[s['task']+'|'+side]['KV']['path']))
   left,right=states[(s['task'],s['recipient'])],states[(s['task'],s['donor'])];rebuilt=splice(left,right,n,s['selector']);actual=res.payload(k);require(actual==rebuilt and digest(actual)==s['audit']['mixed_sha256'],'mixture differs from prescribed selection');roles,layers,positions=selector_geometry(s['selector'],n);selected=len(roles)*len(layers)*len(positions)*2048;changed=int(np.count_nonzero(np.frombuffer(actual,np.uint8)!=np.frombuffer(left,np.uint8)));require(selected==s['audit']['selected_bytes'] and changed==s['audit']['changed_bytes'],'changed-byte audit mismatch');mixproof[mk]={'selected_bytes':selected,'changed_bytes':changed,'mixed_sha256':digest(actual)}
  own=expected[s['task']+'|'+s['recipient']*2];full=expected[s['task']+'|'+s['donor']+s['recipient']];donor=expected[s['task']+'|'+s['donor']*2];changed=mixproof[mk]['changed_bytes'];cls='D' if e==own else 'B' if e==full else 'C';passed=e==(own if s['selector']=='EMPTY' else full) if s['stage']=='control' else None
  row={'slot':s['id'],'task':s['task'],'recipient':s['recipient'],'donor':s['donor'],'direction':s['donor']+'->'+s['recipient'],'selector':s['selector'],'stage':s['stage'],'repeat':s['repeat'],'owned_pid':rec['owned_pid'],'worker_epoch':closed[0]['utc'],'endpoint':e,'endpoint_class':cls,'control_pass':passed,'recipient_endpoint':own,'donor_endpoint':donor,'full_cross_endpoint':full,'donor_full_cross_equal':donor==full,'raw_path':rec['raw_path'],'raw_sha256':rec['raw_sha256'],'evidence_path':rec['evidence_path'],'initial_logits_spec':l,'mixture_spec':k,**mixproof[mk],**t0}
  available=[]
  for t in sorted(map(int,x['partition98']['full_payloads'])):
   z,meta=logits_at(x,t,res,l);require(z is not None,'missing advertised full logits');available.append({'t':t,**meta})
  row['full_logits_available']=available;rows.append(row)
 controls=[r for r in rows if r['stage']=='control'];pairs=collections.defaultdict(list)
 for r in rows:
  if r['stage']=='cross':pairs[(r['task'],r['recipient'],r['selector'])].append(r)
 for key,rr in pairs.items():require(len(rr)==2 and rr[0]['endpoint']==rr[1]['endpoint'] and rr[0]['owned_pid']!=rr[1]['owned_pid'],'repeat process/endpoint disagreement: '+str(key))
 require(all(r['control_pass'] for r in controls),'historical native control endpoint mismatch')
 quartet=[r for r in rows if r['task']=='GSM8K/test/1248' and r['direction']=='B->A' and r['selector'] in PANELS['L0']]
 result={'status':'PASS_INDEPENDENT_RAW_AUDIT','input_commit':RESULT103,'registration_commit':REG103,'baseline_commit':BASE101,'counts':{'native_requests':len(rows),'controls':len(controls),'subset_requests':sum(r['stage']=='cross' for r in rows),'subset_repeat_pairs':len(pairs)},'subset_classes':dict(collections.Counter(r['endpoint_class'] for r in rows if r['stage']=='cross')),'structural_null_subsets':sum(r['stage']=='cross' and r['changed_bytes']==0 for r in rows),'changed_byte_endpoint_null_subsets':sum(r['stage']=='cross' and r['changed_bytes']>0 and r['endpoint_class']=='D' for r in rows),'quartet_1248_B_to_A':[{k:r[k] for k in ('slot','selector','repeat','direction','endpoint_class','changed_bytes','raw_path','raw_sha256')} for r in quartet],'baseline_raw_proof':baseline_proof,'external_actor_model_runtime_pins':external,'resolver_original_prefix':str(original),'resolver_actual_root':str(fresh.resolve()),'logical_to_actual_paths':res.mapping,'rows':rows,'independent_machine':'NOT_PERFORMED','remote_raw_availability':'REMOTE_PENDING','new_GPU_requests':0}
 write(output,result);return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--fresh',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--restore',action='store_true');a=ap.parse_args();manifest=json.loads(gitbytes(a.repo,RESULT103,B103+'execution/final-seal/ARCHIVE_MANIFEST.json'))
 if a.restore:receipt=restore_archive(a.archive,manifest,a.fresh);write(a.output.parent/'RESTORE_RECEIPT.json',receipt)
 else:
  for pin in manifest['files']:p=a.fresh/pin['path'];require(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'fresh manifest mismatch')
 r=audit(a.fresh,a.baseline,a.repo,a.output);print(json.dumps({k:r[k] for k in ('status','counts','subset_classes','quartet_1248_B_to_A')}))
