"""Same finite qualification, with three geometry cases per candidate worker.

The first retained whole-matrix worker observed ~95s per case on this deployment,
so12 cases exceed the unchanged900s worker ceiling. This changes orchestration
only. All12 cases, four M paths, full vectors/states, and natural controls remain.
No numerical rebuild, changed oracle, tolerance, or formal-panel retry is involved.
"""
from pathlib import Path
import argparse, copy, sys
import qualify_native as original
from common import need, read, save, sha
from native_checks import vector_pair, state_pair

REFERENCE_MATRIX_DIR=None

class PartitionedStudy(original.Study):
 def reference_matrix(self,family,cases):
  prior=REFERENCE_MATRIX_DIR/'runs'/(family+'-matrix-R') if REFERENCE_MATRIX_DIR else None
  if prior is None or not prior.exists():return self.execute(family+'-matrix-R',family,{'cases':cases})
  job=REFERENCE_MATRIX_DIR/'jobs'/(family+'-matrix-R.json');expected=copy.deepcopy(self.models[family])
  expected.update(cases=cases,residency='target_only',draft=False);expected.pop('draft_model',None);expected.pop('draft_sha256',None)
  launch=read(prior/'launch.json')
  need(read(job)==expected and launch['job_sha256']==sha(job) and launch['build_sha256']==sha(self.ref_build),'Different retained independent matrix identity')
  need(read(prior/'HOST.json')['status']=='COMPLETE','Never reuse a failed reference worker')
  modules=read(prior/'LOADED_MODULES.json')
  for name,row in modules.items():
   if row['kind']=='ELF_file':need(sha(name)==row['sha256'],'Retained independent matrix module changed')
  self.modules[('reference',family)]=prior/'LOADED_MODULES.json'
  save(self.out/(family+'-REFERENCE_MATRIX_REUSE.json'),{'job_sha256':sha(job),'launch_sha256':sha(prior/'launch.json'),
       'result_sha256':sha(prior/'native/result.json'),'module_map_sha256':sha(prior/'LOADED_MODULES.json'),
       'original_complete_run':str(prior),'logical_requests_replayed':0,'candidate_values_used_as_reference':False})
  return prior

 def matrix(self,family):
  cases=read(self.w/'inputs-01'/(family+'-GEOMETRY.json'))['cases'];ref=self.reference_matrix(family,cases)
  need(len(cases)==12,'Preserve the complete predeclared geometry matrix')
  for arm,(core,cut,draft) in original.ARMS.items():
   if draft:continue
   rows=[];groups=[]
   for start in range(0,len(cases),3):
    group=cases[start:start+3];label=family+'-matrix-'+arm+f'-group{start//3}'
    actual=self.execute(label,family,{'cases':group,'lowering':cut,'residency':'target_only','draft':False,'draft_width':1},core)
    native=read(actual/'native/result.json')
    need(native['model_structure']=={k:self.structures[family][k] for k in native['model_structure']},'Actual model topology differs from independent GGUF header')
    need(len(native['cases'])==len(group),'Missing native grouped geometry case')
    for i,c in enumerate(group):
     executed=native['cases'][i]['executions']
     need(executed and sum(x['width'] for x in executed)==sum(len(x['ids']) for x in c['forced']),'Missing actual occupied physical rows')
     need(all(0<x['width']<=32 and x['active_cells']==x['position']+x['width'] for x in executed),'Actual dense append mapping/physical widths')
     for n in c['observe_positions']:
      aa=actual/'native'/c['name']/'captures'/str(n);bb=ref/'native'/c['name']/'captures'/str(n)
      row={'case':c['name'],'position':n,'vector':vector_pair(aa/'frontier.f32',bb/'frontier.f32',native['vocab'])}
      if n in c['state_positions']:row['active_KV']=state_pair(aa/'sequence.bin',bb/'sequence.bin',n,self.parse,self.profiles[family])
      rows.append(row)
    groups.append({'cases':[c['name'] for c in group],'actual_native_result_sha256':sha(actual/'native/result.json'),'launch_sha256':sha(actual/'launch.json')})
    print('COMPLETE_MATRIX_GROUP',family,arm,start//3,flush=True)
   self.report(family+'-matrix-'+arm+'-CHECKED',{'passed':all(r['vector']['equal'] and r.get('active_KV',{'equal':True})['equal'] for r in rows),
      'family':family,'arm':arm,'rows':rows,'groups':groups,'separate_R_launch_sha256':sha(ref/'launch.json'),
      'scope':'Identical fixed12 geometry cases and exact comparison rules; four sequential candidate workers of3 cases retain the900s ceiling; no formal panel repartition'})

if __name__=='__main__':
 parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--reuse-reference-matrices',type=Path)
 extra,rest=parser.parse_known_args();REFERENCE_MATRIX_DIR=extra.reuse_reference_matrices.resolve() if extra.reuse_reference_matrices else None
 # Reuse the original natural/trace/vector/state checks and final proof registry.
 # Only this explicitly recorded matrix orchestration method is overridden.
 original.Study=PartitionedStudy;sys.argv=[sys.argv[0],*rest];original.main()
