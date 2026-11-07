"""Correct independent resource telemetry in a fresh non-numerical epoch."""
from host import *
def stage(role):
 previous=ROOT/role;dest=ROOT/(role+'-budget01');shutil.copytree(previous/'kit',dest/'kit')
 native=dest/'kit/b570_producer_consumer_boundary_v1/native'
 shutil.copyfile(HERE/'resource_budget.hpp',native/'resource_budget.hpp')
 header=native/'transfer_scope.hpp';s=header.read_text()
 s=s.replace('static void capacity_check() {','#include "resource_budget.hpp"\nstatic void capacity_check() {')
 s=s.replace('    need(available <= total, "device free exceeds total");','    std::fprintf(stderr,"HS_LEGACY_MEMORY free=%llu total=%llu\\n",(unsigned long long)available,(unsigned long long)total);\n    available=bounded_vulkan_free();')
 header.write_text(s,encoding='utf-8')
 cm=dest/'kit/b570_producer_consumer_boundary_v1/CMakeLists.txt';text=cm.read_text();text+='\nfind_package(Vulkan REQUIRED)\ntarget_link_libraries(boundary PRIVATE Vulkan::Vulkan)\n';cm.write_text(text)
 write(dest/'SOURCE.json',dict(previous_source=read(previous/'SOURCE.json'),previous_worker_sha256=sha(previous/'kit/b570_producer_consumer_boundary_v1/native/boundary.cpp'),worker_sha256=sha(native/'boundary.cpp'),resource_header_sha256=sha(header),metadata_query_sha256=sha(native/'resource_budget.hpp'),numerical_changes=False))
 # Build paths use the original numerical role while keeping the new epoch separate.
 original=role=='R';unit=dest/'kit/b570_producer_consumer_boundary_v1'
 command(['cmake','-S',unit,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64','-DLLAMA_SOURCE='+str(ORACLE/'clean-source2/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2' if original else OLD/'source-01'),'-DQUALIFIED_BUILD='+str(ORACLE/'build' if original else OLD/'build-01')],dest/'configure.log')
 command(['cmake','--build',dest/'build','--config','Release','--parallel','4'],dest/'compile.log')
 bins=dest/'build/bin/Release'
 for p in (previous/'build/bin/Release').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(dest/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.exe','.dll')]))
def admit(role):
 s=read(HISTORY/'run-primary/B1-2.job.json')['slots'][2]
 s.update(study_id='tpds_decisive_b570_draft_v1',draft_caller=1 if role=='R' else int(role[1]),draft_ubatch=1 if role=='R' else int(role[3]),target_ub=1 if role=='R' else 4)
 n=run('admit-'+role+'-budget01',role+'-budget01',[s],admit=True);print(role,n['status'],n.get('error'),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='stage':stage(sys.argv[2])
 else:admit(sys.argv[2])
