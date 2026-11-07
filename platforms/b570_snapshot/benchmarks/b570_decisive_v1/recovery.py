"""Append-only engineering continuation of the retained PR187 result."""
from host import *
def dxgi_stage(epoch):
 role='C1U1-budget'+epoch;dest=ROOT/role
 shutil.copytree(ROOT/'C1U1-budget01/kit',dest/'kit')
 native=dest/'kit/b570_producer_consumer_boundary_v1/native'
 shutil.copyfile(HERE/'dxgi_budget.hpp',native/'dxgi_budget.hpp')
 p=native/'resource_budget.hpp';s=p.read_text();s=s.replace('#include <vulkan/vulkan.h>','#include <vulkan/vulkan.h>\n#include "dxgi_budget.hpp"');s=s.replace(' static Query q;',' static Query q;\n hs_dxgi_budget(q.device);');p.write_text(s)
 cm=dest/'kit/b570_producer_consumer_boundary_v1/CMakeLists.txt';cm.write_text(cm.read_text()+'\ntarget_link_libraries(boundary PRIVATE dxgi)\n')
 write(dest/'SOURCE.json',dict(previous_epoch='C1U1-budget01',worker_sha256=sha(native/'boundary.cpp'),resource_sha256=sha(p),dxgi_sha256=sha(native/'dxgi_budget.hpp'),numeric_dll_changes=False,reserve_relaxed=False))
 unit=dest/'kit/b570_producer_consumer_boundary_v1'
 command(['cmake','-S',unit,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64','-DLLAMA_SOURCE='+str(OLD/'source-01'),'-DQUALIFIED_BUILD='+str(OLD/'build-01')],dest/'configure.log')
 command(['cmake','--build',dest/'build','--config','Release','--parallel','4'],dest/'compile.log')
 bins=dest/'build/bin/Release'
 for p in (ROOT/'C1U1-budget01/build/bin/Release').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(dest/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.dll','.exe')]))
def dxgi_admit(epoch):
 assert len(list((ROOT/'units').glob('admit-*')))<10
 s=read(HISTORY/'run-primary/B1-2.job.json')['slots'][2]
 s.update(study_id='tpds_decisive_b570_draft_v1',draft_caller=1,draft_ubatch=1,target_ub=4)
 role='C1U1-budget'+epoch
 n=run('admit-'+role,role,[s],admit=True);print(n['status'],n.get('error'))
if __name__=='__main__':
 if sys.argv[1]=='stage':dxgi_stage(sys.argv[2])
 else:dxgi_admit(sys.argv[2])
