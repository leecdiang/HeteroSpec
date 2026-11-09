"""Whitelisted metadata repair, never a native retry or qualification bypass.

Wait for the frozen driver to finish its current worker. Only its known
duplicate-key table-construction TypeError admits this adapter. Reuse every
completed worker exactly once and run only still-unreserved frozen slots.
"""
from pathlib import Path
import argparse,fcntl,hashlib,importlib.util,inspect,json,sys,textwrap,time,traceback
sys.dont_write_bytecode=True
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--builds',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);a=p.parse_args()
 w=a.work;spec=importlib.util.spec_from_file_location('frozen_stage_B',a.source/'run.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 while not(w/'COMPLETE.json').exists()and not list(w.glob('STOPPED-*')):
  if time.time()>1794226500:raise RuntimeError('Adapter wait cutoff; no native start')
  time.sleep(5)
 if(w/'COMPLETE.json').exists():return
 stopped=[h.read(f)for f in w.glob('STOPPED-*')]
 if not any(any("multiple values for keyword argument '"+field+"'" in x['error'] for field in ('position','execution')) for x in stopped):
  h.save(w/'RECORD_ADAPTER_NOT_ADMITTED.json',dict(reason='Parent stopped for another reason',native_requests=0));return
 assert h.read(w/'QUALIFIED.json')['passed']and len(h.read(w/'QUALIFIED.json')['cells'])==32
 plan_path=w/'TIMING_PLAN.json';plan=h.read(plan_path);plan_hash=h.sha(plan_path);assert len(plan['workers'])==8
 parent_hash=h.sha(a.source/'run.py');assert parent_hash==h.read(w/'SOURCE_AT_PREPARE.json')['run.py']
 source=inspect.getsource(h.Runner.timing)
 old="position=worker['position'],execution=item['execution'],**r,";assert source.count(old)==1
 source=source.replace(old,'**r,',1)
 old="save(self.w/'TIMING_PLAN.json',dict(frozen_before_timing_utc=stamp(),workers=frozen,measurement_requests=16,primer_requests=8))";assert source.count(old)==1
 source=source.replace(old,"assert read(self.w/'TIMING_PLAN.json')['workers']==frozen",1)
 ns=dict(h.__dict__);exec(compile(textwrap.dedent(source),'<record-only duplicate-key adapter>','exec'),ns)
 h.save(w/'RECORD_ADAPTER_DECLARATION.json',dict(parent_source_sha256=parent_hash,adapter_source_sha256=h.sha(Path(__file__)),patched_function_sha256=hashlib.sha256(source.encode()).hexdigest(),frozen_timing_plan_sha256=plan_hash,
  changes=['Remove duplicate position/execution table kwargs; values already guarded in native receipt','Retain exact original frozen TIMING_PLAN','Reuse complete original slots without rerun; execute only never-reserved slots'],numerical_code_or_thresholds_changed=False,original_failures_retained=True))
 runner=h.Runner(a);freeze=h.read(w/'REFERENCE_DERIVED_FREEZE.json');runner.streams={int(i):v for i,v in freeze['streams'].items()};runner.oracles={i:w/'runs'/f'R-trunk-{i}'/'native/trunk/captures'for i in range(4)}
 original=runner.run
 def run(name,job,core='reference'):
  runner.gate();slot=next(x for x in plan['workers']if x['name']==name);assert slot['core']==core and slot['job']==job
  out=w/'runs'/name
  ledger=[json.loads(x)for x in (w/'ledger.jsonl').read_text().splitlines()];reserved=[x for x in ledger if x['event']=='RESERVE'and Path(x['out'])==out]
  if out.exists():
   assert len(reserved)==1 and h.read(out/'HOST.json')['status']=='COMPLETE','Never reuse failed/incomplete worker'
   launch=h.read(out/'launch.json');assert launch['job_sha256']==h.sha(w/'jobs'/(name+'.json'))and h.read(w/'jobs'/(name+'.json'))==job
   assert launch['build_sha256']==h.sha(a.builds/core/'BUILD.json')
   for path,m in h.read(out/'LOADED_MODULES.json').items():
    if m['kind']=='ELF_file':assert h.sha(path)==m['sha256']
   h.save(w/'record-adapter-reuse'/(name+'.json'),dict(passed=True,native_repeated=False,launch_sha256=h.sha(out/'launch.json'),files=[dict(path=str(f.relative_to(out)),bytes=f.stat().st_size,sha256=h.sha(f))for f in out.rglob('*')if f.is_file()]));return out/'native'
  assert not reserved,'Never repeat a previously reserved slot'
  return original(name,job,core)
 runner.run=run
 with(a.root/'STUDY_SCHEDULING.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);ns['timing'](runner)
 assert h.sha(plan_path)==plan_hash and h.sha(a.source/'run.py')==parent_hash
 ledger=[json.loads(x)for x in (w/'ledger.jsonl').read_text().splitlines()];reserved=[x for x in ledger if x['event']=='RESERVE'];assert sum(x['requests']for x in reserved)==66
 h.save(w/'COMPLETE.json',dict(passed=True,utc=h.stamp(),stage='B_ONLY',new_requests=66,total_Stage_B_requests=67,conservative_rows_reserved=sum(x['rows']for x in reserved),record_adapter=True,numerical_binaries_unchanged=True,frozen_timing_plan_unchanged=True,original_failure_retained=True,candidate_optimization=False,next='No automatic C/D/E or 32B'))
if __name__=='__main__':main()
