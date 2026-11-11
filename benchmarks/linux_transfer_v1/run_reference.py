"""Execute and freeze actual repeated independent Linux R before candidates."""
from pathlib import Path
import argparse, fcntl, hashlib
import numpy as np
from common import need, read, save, sha
from host import run
from compare import compare
from freeze import reference

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('work','config','build'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--family',choices=('Qwen','Smol'))
 a=p.parse_args();w=a.work.resolve();inputs=w/'inputs-01';out=w/'reference-01'
 coordinator_lock=(w/'REFERENCE_COORDINATOR.lock').open('a')
 fcntl.flock(coordinator_lock,fcntl.LOCK_EX)
 need(not (out/'REFERENCE_FREEZE.json').exists(),'Independent R is already frozen')
 out.mkdir(exist_ok=True)
 need(read(a.build)['role']=='reference','Independent source-built reference only')
 pairs=[];endpoints=[];runs=[]
 for family in ((a.family,) if a.family else ('Qwen','Smol')):
  for kind in ('R-repeat','R-free-repeat'):
   paths=[]
   for repeat in (1,2):
    job=inputs/f'{family}-{kind}-{repeat}.json';dest=out/f'{family}-{kind}-{repeat}'
    if dest.exists():
     need(read(dest/'HOST.json')['status']=='COMPLETE','Failed reference attempt retained; explicit new epoch required')
     launch=read(dest/'launch.json');need(launch['job_sha256']==sha(job) and launch['build_sha256']==sha(a.build),'Completed reference does not match fixed job/build')
     for name,row in read(dest/'LOADED_MODULES.json').items():
      if row['kind']=='ELF_file':need(sha(name)==row['sha256'],'Actual reference module changed during the input wait')
    else:run(a.config,a.build,job,dest,'reference')
    paths.append(dest)
    runs.append({'family':family,'job_sha256':sha(job),'launch_sha256':sha(dest/'launch.json'),'loaded_modules_sha256':sha(dest/'LOADED_MODULES.json')})
   first,second=paths;meta=read(first/'native/result.json');vocab=meta['vocab']
   need(meta['n_ubatch']==1 and meta['n_ctx']==1024 and meta['output_reserve']==1 and meta['threads']==2,'Actual reference allocation differs')
   captures=list((first/'native').rglob('*.f32'))+list((first/'native').rglob('sequence.bin'))
   need(captures,'No executed reference captures')
   for x in sorted(captures):
    y=second/'native'/x.relative_to(first/'native');need(y.is_file(),'R repeat capture missing')
    if x.suffix=='.f32':
     for f in (x,y):
      b=f.read_bytes();need(len(b)==4*vocab and bool(np.isfinite(np.frombuffer(b,dtype='<f4')).all()),'Nonfinite/truncated independent vector')
     pairs.append({'kind':'full_requested_logits','reference':str(x),'candidate':str(y)})
     if x.with_name('sequence.bin').exists():pairs.append({'kind':'frontier','reference':str(x),'candidate':str(y)})
    else:pairs.append({'kind':'active_sequence_serialized','reference':str(x),'candidate':str(y)})
   if kind=='R-free-repeat':
    job=read(inputs/f'{family}-{kind}-1.json')
    for entry in job['inputs']:
     x=read(first/'native'/entry['name']/'receipt.json');y=read(second/'native'/entry['name']/'receipt.json')
     fields=('ids','eog','cap','pending_id','pending_position','materialized_tokens','terminal_kind')
     equal=all(x[k]==y[k] for k in fields);need(equal,'Independent endpoint/termination unstable')
     need(x['pending_position']==len(entry['input']['prompt_ids'])+len(x['ids'])-1,'Reference pending frontier')
     need(x['pending_id']==x['ids'][-1] and not any(x['eog'][:-1]),'Reference committed/pending/EOG contract')
     need(x['terminal_kind']==('EOG' if x['eog'][-1] else 'CAP'),'Reference native termination')
     need(x['eog'][-1] or len(x['ids'])==x['cap'],'Reference cap')
     endpoints.append({'family':family,'name':entry['name'],'equal':equal,'reference_receipt_sha256':sha(first/'native'/entry['name']/'receipt.json'),'repeat_receipt_sha256':sha(second/'native'/entry['name']/'receipt.json'),'terminal_kind':x['terminal_kind']})
 executable=read(a.build)['executable_sha256']
 manifest={'mode':'reference_repeat','reference_executable_sha256':executable,'candidate_executable_sha256':executable,'reference_core':'pristine-upstream','pairs':pairs,
           'scope':'Both pinned model families; retained crossing witness, full q4 requested vectors, two exposed free roots/family; complete native serialized active seq0 and initial/terminal frontiers'}
 if a.family:
  manifest['scope']='Separate '+a.family+' reference executions while the other exact model downloads; no global reference freeze or candidate eligibility yet'
  checked=compare(manifest);save(out/(a.family+'-REPEAT_CHECKED.json'),checked);need(checked['passed'],'Unstable family R retained')
  save(out/(a.family+'-REFERENCE_FAMILY_COMPLETE.json'),{'family':a.family,'runs':runs,'endpoints':endpoints,'repeat_checked_sha256':sha(out/(a.family+'-REPEAT_CHECKED.json')),'global_reference_frozen':False})
  print('REFERENCE_FAMILY_COMPLETE',a.family,flush=True);return
 save(out/'REPEAT_MANIFEST.json',manifest);checked=compare(manifest);save(out/'REPEAT_CHECKED.json',checked)
 need(checked['passed'],'Unstable independent reference retained')
 ledger=(w/'ledger.jsonl').read_text();events=[__import__('json').loads(x) for x in ledger.splitlines()]
 need(all(x.get('phase')=='reference' for x in events if x.get('event')=='RESERVE'),'Candidate outputs preceded reference freeze')
 save(out/'ORDER_AND_ENDPOINTS.json',{'candidate_outputs_before_freeze':0,'ledger_sha256_before_freeze':hashlib.sha256(ledger.encode()).hexdigest(),
      'contract_sha256':sha(inputs/'CONTRACT_BEFORE_OUTPUTS.json'),'runs':runs,'endpoints':endpoints})
 reference(a.build,out/'REPEAT_CHECKED.json',out/'REFERENCE_FREEZE.json')
 cfg=read(a.config);cfg.update(reference_freeze=str(out/'REFERENCE_FREEZE.json'),reference_freeze_sha256=sha(out/'REFERENCE_FREEZE.json'))
 save(w/'config-reference-frozen-01.json',cfg)
 print('REFERENCE_FROZEN',sha(out/'REFERENCE_FREEZE.json'),flush=True)

if __name__=='__main__':main()
