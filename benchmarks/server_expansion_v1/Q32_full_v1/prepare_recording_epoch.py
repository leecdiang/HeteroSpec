"""Restore all six arms for the recording/SHA successor, retain every old epoch.

Reconstruct every original PREFILL descriptor offline; never drop tensor values,
physical work or all-row ownership checks. No old numerical output is a new R.
"""
from pathlib import Path
import argparse,shutil
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--helpers',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir()
 for name in('build.py','resource_guard.py'):shutil.copy2(a.source/name,a.out/name)
 shutil.copy2(a.helpers/'geometry_journal.py',a.out/'geometry_journal.py')
 s=(a.source/'qualification.py').read_text().replace("self.w/'qualification-03'","self.w/'qualification-06'")
 s=s.replace('greedy=True,cuda_graphs=False,','greedy=True,cuda_graphs=False,geometry_policy="PREFILL:complete binary descriptors;VERIFY/ORDINARY:JSON",native_hash_file="Full SHA256, read-only mmap, pinned system libcrypto",native_crypto_sha256=sha(Path("/usr/lib/x86_64-linux-gnu/libcrypto.so.3")),',1)
 # Every full tensor descriptor is read, checked and bound; JSON allocation is
 # deferred outside native timing, not silently omitted from qualification.
 s=s.replace('from build import read,sha,save','from build import read,sha,save\nimport geometry_journal',1)
 anchor="  for c in cases:\n   n=sum(len(z['ids'])for z in c['forced']);";assert s.count(anchor)==1;s=s.replace(anchor,"  for c in cases:\n   c['forced'][1]['all']=True\n   n=sum(len(z['ids'])for z in c['forced']);",1)
 anchor='cases=[small]+cases';assert s.count(anchor)==1;s=s.replace(anchor,"cases=[small]+[dict(name=f'own-p{p}-q4',forced=[dict(ids=owned[:p],phase='PREFILL',all=False),dict(ids=owned[p:p+4],phase='VERIFY',all=True)],observe_positions=list(range(p,p+5)),state_positions=[p,p+4])for p in(32,33)]+cases",1)
 s=s.replace('range(0,len(cases),2):','range(0,len(cases),1):',1).replace('group=cases[start:start+2]','group=cases[start:start+1]',1)
 start=s.index("  if core=='reference':\n   prior=");end=s.index("  save(self.out/'admissions'",start)
 s=s[:start]+'''  if core=='reference' and 'cases' in m:
   for epoch in('qualification-05','qualification-04','qualification-01'):
    for prior_job in sorted((self.w/epoch/'jobs').glob('geometry-R-*.json')):
     prior=self.w/epoch/'runs'/prior_job.stem
     if not(prior/'HOST.json').exists()or read(prior/'HOST.json')['status']!='COMPLETE':continue
     original=read(prior_job)
     if {k:v for k,v in original.items()if k!='cases'}!={k:v for k,v in m.items()if k!='cases'} or not all(c in original['cases']for c in m['cases']):continue
     launch=read(prior/'launch.json');assert launch['job_sha256']==sha(prior_job)and launch['build_sha256']==sha(b)
     modules=read(prior/'LOADED_MODULES.json')
     for p,x in modules.items():
      if x['kind']=='ELF_file':assert sha(p)==x['sha256']
     files=[]
     for case in m['cases']:
      for p in sorted((prior/'native'/case['name']).rglob('*')):
       if p.is_file():files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
     save(self.out/'reuse'/(label+'.json'),dict(prior=str(prior),original_complete_superset_job_sha256=sha(prior_job),selected_cases=m['cases'],files=files,scope='Exact independently reset R cases from complete original scalar job; other original cases remain charged; no candidate reuse',new_native_requests=0))
     self.modules.setdefault(core,modules);assert self.modules[core]==modules;print('Q32_EXACT_R_CASES_REUSED',label,flush=True);return prior
''' +s[end:]
 anchor="record=meta['cases'][i];es=record['executions'];";assert s.count(anchor)==1;s=s.replace(anchor,"record=copy.deepcopy(meta['cases'][i]);expanded,journal_proof=geometry_journal.decode(record.get('prefill_descriptor_journal'));record['geometry']+=expanded;save(self.out/'recording-readback'/(arm+'-'+c['name']+'.json'),journal_proof);es=record['executions'];",1)
 anchor="  graph=[z for z in r['geometry']if z['op']=='MUL_MAT'];assert graph";assert s.count(anchor)==1;s=s.replace(anchor,"  expanded,journal_proof=geometry_journal.decode(r.get('prefill_descriptor_journal'));graph=[z for z in r['geometry']+expanded if z['op']=='MUL_MAT'];assert graph",1)
 s=s.replace('return dict(mixed_nodes=len(mixed),','return dict(prefill_operator_readback=journal_proof,mixed_nodes=len(mixed),',1);s=s.replace('self.admission(m);path=', 'path=',1);s=s.replace("  save(self.out/'admissions'","  self.admission(m)\n  save(self.out/'admissions'",1);(a.out/'qualification.py').write_text(s)
 # Original all-six boundary/primer/panel logic, plus strict metadata codec.
 s=(a.source/'finish.py').read_text().replace('qualification-03','qualification-06').replace('closure-03','closure-06').replace('FINISH_NOT_ADMITTED-03','FINISH_NOT_ADMITTED-06');(a.out/'finish.py').write_text(s)
 shutil.copy2(Path(__file__).parent/'recording_coordinator.py',a.out/'coordinator.py')
 save(a.out/'ADAPTER_BINDING.json',dict(original_sources={n:sha(a.source/n)for n in('qualification.py','finish.py')},new_sources={p.name:sha(p)for p in a.out.iterdir()if p.is_file()},scope='All six arms, same numerical archives/R/512 ceiling; new observer/SHA ABI must independently qualify; complete original descriptors decoded and retained; explicit p32/p33 mask diagnostics; no tolerance or state/value omission'))
if __name__=='__main__':main()
