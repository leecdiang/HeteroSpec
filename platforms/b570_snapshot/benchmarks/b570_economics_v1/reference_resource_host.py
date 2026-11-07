"""Capacity-only observer bridge; the original R binary/data remain unchanged."""
from campaign_host import *
from stage_costs import once
import re

def build():
 d=ROOT/'forced-resource02'
 if (d/'FILES.json').exists():return d
 original=OSMOL/'forced-reference02';freeze=read(OLD_CAMPAIGN/'FREEZE.json')
 assert sha(original/'FILES.json')==freeze['forced_reference_manifest_sha256']
 d.mkdir()
 for p in original.iterdir():
  if p.is_file() and p.suffix.lower() in ('.cpp','.h','.hpp','.txt'):shutil.copyfile(p,d/p.name)
 old=(original/'target.cpp').read_text(encoding='utf-8');s=old
 s=once(s,'#include "smol_capture.hpp"','#include "smol_capture.hpp"\n#include "smol_capacity.hpp"')
 anchor='    std::cout<<"HS_READY\\n"<<std::flush;';s=once(s,anchor,'    smol_capacity();\n'+anchor)
 anchor='        std::cout<<"HS_RESULT "<<pj({{"request_id",req.at("request_id")},{"forced_tokens",suffix.size()}}).dump()<<"\\n"<<std::flush;';s=once(s,anchor,'        smol_capacity();\n'+anchor)
 # Remove the include using exact lines and both guard-only insertions.
 restored=s.replace('#include "smol_capture.hpp"\n#include "smol_capacity.hpp"','#include "smol_capture.hpp"').replace('    smol_capacity();\n'+ '    std::cout<<"HS_READY\\n"<<std::flush;', '    std::cout<<"HS_READY\\n"<<std::flush;').replace('        smol_capacity();\n'+anchor,anchor)
 assert restored==old
 (d/'target.cpp').write_text(s,encoding='utf-8',newline='\n')
 for name in ('smol_capacity.hpp','resource_budget.hpp'):shutil.copyfile(ROOT/'resident04/M-mode0'/name,d/name)
 with (d/'CMakeLists.txt').open('a',encoding='utf-8') as f:f.write('\ntarget_compile_definitions(b570-closeout-target PRIVATE NOMINMAX)\nfind_package(Vulkan REQUIRED)\ntarget_link_libraries(b570-closeout-target PRIVATE Vulkan::Vulkan)\n')
 write(d/'RESOURCE_ONLY_SOURCE_BINDING.json',dict(original_producer_unchanged=True,original_frontend_sha256=sha(original/'target.cpp'),observer_frontend_sha256=sha(d/'target.cpp'),only_additions=['include existing signed resource guard','check after original model/context init','check after each complete original forced request'],reference_manifest_sha256=sha(original/'FILES.json'),numerical_DLLs_changed=False,old_original_R_binary_not_modified=True,source_files={p.name:sha(p) for p in d.iterdir() if p.suffix in ('.cpp','.h','.hpp','.txt')}))
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 command(['cmake','--build',d/'build','--config','Release','--target','b570-closeout-target','--parallel','4'],d/'compile.log')
 bins=d/'build/Release'
 for f in read(ROOT/'bindings/forced-FILES.json')['files']:
  p=Path(f['path'])
  if p.suffix.lower()=='.dll':assert sha(p)==f['sha256'];shutil.copyfile(p,bins/p.name)
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in bins.iterdir() if p.suffix.lower() in ('.dll','.exe')]))
 return d

@meter('reference-resource-qualification')
def main():
 assert not LOCK.exists();d=build();units=sorted(p for p in (ROOT/'units').iterdir() if p.name.startswith('forced-'))
 captured={Path(p).parent.name for receipt in (ROOT/'reference').glob('*/COMPLETE-*.json') for p in read(receipt)['captures']}
 assert units and {p.name for p in units}==captured
 plan=ROOT/'REFERENCE_RESOURCE_PLAN.json'
 if not plan.exists():write(plan,dict(reason='Original forced R has no signed GPU budget observations; do not invent them or change its producer',units=[p.name for p in units],same_token_tapes_only=True,no_new_root_or_performance_sample=True,binding_sha256=sha(d/'RESOURCE_ONLY_SOURCE_BINDING.json'),initial_timing_closeout_sha256=sha(ROOT/'EXPERIMENT_CLOSED.json')))
 assert read(plan)['units']==[p.name for p in units];results=[]
 for unit in units:
  source=ROOT/'runs'/unit.name;jobs=read(source/'JOBS.json');assert len(jobs)==1
  name='resource-ref01-'+unit.name;dest=ROOT/'runs'/name
  if not (dest/'MODULE_AUDIT.json').exists():execute(name,'M',jobs,heavy=True,forced=True,build=d)
  a=read(source/'0.json');b=read(dest/'0.json');assert not a['candidate_values_received'] and not b['candidate_values_received'] and a['prompt_ids']==b['prompt_ids']
  assert [x['prefix'] for x in a['prefixes']]==[x['prefix'] for x in b['prefixes']]
  states=0
  for x,y in zip(a['prefixes'],b['prefixes']):
   assert native_path(x['frontier']).read_bytes()==native_path(y['frontier']).read_bytes()
   if 'sequence' in x:assert state_equal(x,y);states+=1
  text=(ROOT/'units'/name/'SUPERVISOR.stderr.log').read_text(errors='replace');budgets=[]
  for m in re.finditer(r'HS_BUDGET heap=(\d+) physical=(\d+) budget=(\d+) usage=(\d+) signed_remaining=(-?\d+)',text):
   _,physical,budget,usage,remaining=map(int,m.groups());assert remaining==budget-usage and 0<budget<=physical and remaining>=128*1024**2;budgets.append(remaining)
  assert len(budgets)>=2
  results.append(dict(original_unit=unit.name,resource_observer_unit=name,requests=1,full_vectors=len(a['prefixes']),states=states,all_equal=True,minimum_signed_GPU_reserve_bytes=min(budgets),original_request_budget_observation=None,original_R_unchanged=True))
  print('REFERENCE_RESOURCE_BRIDGE_PASS',unit.name,len(a['prefixes']),min(budgets),flush=True)
 write(ROOT/'REFERENCE_RESOURCE_BRIDGE.json',dict(status='ORIGINAL_R_RESOURCE_OBSERVER_BYTE_EXACT_BRIDGE_PASS',results=results,requests=len(results),full_vectors=sum(x['full_vectors'] for x in results),states=sum(x['states'] for x in results),all_original_missing_observations_retained=True,original_producer_and_numerical_DLLs_unchanged=True,original_reference_data_not_replaced=True,natural_performance_samples=0))

if __name__=='__main__':main()
