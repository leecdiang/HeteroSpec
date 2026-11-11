"""Batch independently reset qualification cases, never formal measurements.

Same exact ELF/R/cases/outputs/checks. Retain all prior jobs and revalidate every
complete identical prior job before reuse. At most three new cases per worker;
the observed p764 worker completed in49.298s under the unchanged900s bound.
"""
from pathlib import Path
import argparse,shutil
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();w=a.root/'q32-q4-full-20261109-01'
 for name in ['build.py','resource_guard.py','geometry_journal.py']:shutil.copy2(a.source/name,a.out/name)
 s=(a.source/'qualification.py').read_text().replace('qualification-07','qualification-08')
 # Exact prior complete jobs, same payload/build/executable/modules and all
 # output file commitments; comparisons still run again in the new controller.
 anchor="  if core=='reference' and 'cases' in m:";assert s.count(anchor)==1
 reuse='''  if 'cases' in m:
   prior=self.w/'qualification-07/runs'/label;prior_job=self.w/'qualification-07/jobs'/(label+'.json')
   if (prior/'HOST.json').exists()and read(prior/'HOST.json')['status']=='COMPLETE'and prior_job.exists()and read(prior_job)==m:
    launch=read(prior/'launch.json');assert launch['job_sha256']==sha(prior_job)and launch['build_sha256']==sha(b)
    modules=read(prior/'LOADED_MODULES.json')
    for p,x in modules.items():
     if x['kind']=='ELF_file':assert sha(p)==x['sha256']
    if core!='reference':assert read(prior/'native/CAPABILITY.json')==m['capability_request']
    files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))for p in sorted((prior/'native').rglob('*'))if p.is_file()]
    save(self.out/'reuse'/(label+'.json'),dict(prior=str(prior),job_sha256=sha(prior_job),build_sha256=sha(b),files=files,scope='Exact complete same-ELF/job reuse, every output committed; all numerical and physical comparisons rerun; prior reservations remain charged',new_native_requests=0))
    self.modules.setdefault(core,modules);assert self.modules[core]==modules;print('Q32_EXACT_COMPLETE_JOB_REUSED',label,flush=True);return prior
'''
 s=s.replace(anchor,reuse+anchor,1)
 anchor="  for start in range(0,len(cases),1):\n   group=cases[start:start+1];ref=self.execute('geometry-R-'+str(start),'Qwen32B',dict(cases=group))";assert s.count(anchor)==1
 replacement="  groups=[(i,i+1)for i in range(min(4,len(cases)))]+[(i,min(i+3,len(cases)))for i in range(4,len(cases),3)]\n  save(self.out/'GEOMETRY_BATCH_PLAN.json',dict(groups=groups,max_cases_per_worker=3,logical_cases_unchanged=True,independent_reset_each_case=True,actual_observed_long_worker_s=49.297996898996644,worker_timeout_s=900,scope='Qualification only; no timing or numerical contract change'))\n  for start,end in groups:\n   group=cases[start:end];refs=[self.execute('geometry-R-'+str(start+j),'Qwen32B',dict(cases=[c]))for j,c in enumerate(group)]"
 s=s.replace(anchor,replacement,1)
 anchor="    for i,c in enumerate(group):\n     record=";assert s.count(anchor)==1;s=s.replace(anchor,"    for i,c in enumerate(group):\n     ref=refs[i]\n     record=",1)
 (a.out/'qualification.py').write_text(s)
 for name in ['finish.py','archive.py']:
  s=(a.source/name).read_text().replace('qualification-07','qualification-08').replace('closure-07','closure-08').replace('FINISH_NOT_ADMITTED-07','FINISH_NOT_ADMITTED-08').replace('LAUNCH_07','LAUNCH_08').replace('CLOSED07','CLOSED08').replace('export-09','export-10');(a.out/name).write_text(s)
 shutil.copy2(Path(__file__).parent/'batched_geometry_coordinator.py',a.out/'coordinator.py')
 for p in a.out.glob('*.py'):compile(p.read_text(),str(p),'exec')
 save(a.out/'ADAPTER_BINDING.json',dict(original_sources={p.name:sha(p)for p in a.source.glob('*.py')},new_sources={p.name:sha(p)for p in a.out.glob('*.py')},native_ELF_changed=False,numerical_archives_changed=False,reference_changed=False,all_original_geometry_cases_and_checks_retained=True,only_qualification_worker_grouping_changed=True,formal_panel_unchanged=True,prior_complete_jobs_rechecked_and_charged_once=True))
if __name__=='__main__':main()
