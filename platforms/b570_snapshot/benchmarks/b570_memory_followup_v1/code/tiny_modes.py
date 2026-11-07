"""Required bounded tiny validation for all declared modes; selection is already frozen."""
from common import *
from runner import Worker,signature
from probe import budget
import traceback
s=load(R/'STANDARD_Q6_ENGINEERING.json');assert s['status']!='ENGINEERING_IN_PROGRESS' and s.get('diagnostic_ranked_first')
cases=[];synthetic=load(R/'SYNTHETIC_INPUTS.json');profile='STANDARD_Q6';ub=s['R_prod_ub'];reference={}
for p in (R/'raw').glob('STANDARD_Q6_BOUNDARY_R_stock_0*/RESULT.json'):
 x=load(p)
 if not x['warm']:reference[x['task'],x['native']['cap']]=x
assert len(reference)==15
for q in ['Q8_0','Q4_K_M']:
 for mode in ['native_greedy','vulkan_batched_repair']:
  name=f'{profile}_TINY_{q}_{mode}_k3';worker=None;entry=dict(draft=q,mode=mode,k_max=3,selection_effect='NONE',requests=[],status='IN_PROGRESS')
  try:
   worker=Worker(profile,q,ub,mode,3,name);worker.request(synthetic[0],name+'_warm',0,'TINY',warm=True,capture=True)
   for inp in synthetic[1:3]:
    for cap in [1,2,3,4]:
     x=worker.request(inp,name+'_'+inp['id'].rsplit('/',1)[1]+'_'+str(cap),0,'TINY',cap=cap,capture=True);same=signature(x['native'])==signature(reference[inp['id'],cap]['native']);entry['requests'].append(dict(unit=x['unit'],task=inp['id'],cap=cap,whole_native_reference_equal=same))
   entry['status']='COMPLETE_RAW_EQUIVALENT' if all(x['whole_native_reference_equal'] for x in entry['requests']) else 'COMPLETE_RAW_DIVERGENCE'
  except BaseException as e:entry.update(status='BLOCKED',error=repr(e),traceback=traceback.format_exc())
  finally:
   if worker:worker.close()
   cases.append(entry);save(R/'TINY_MODE_VERIFICATION.json',dict(status='COMPLETE' if len(cases)==4 else 'IN_PROGRESS',cases=cases,budget=budget(profile),candidate_selection_unchanged=True,formal_requests=0))
print('All-mode tiny validation closed',budget(profile),flush=True)
