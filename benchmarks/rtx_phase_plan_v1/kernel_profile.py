"""Separate CUPTI execution; these clocks are never clean timing samples."""
from develop import *

def build(lowering):
    base=ROOT/VERSIONS[lowering];dest=ROOT/'profiles-final'/lowering;dest.mkdir(parents=True)
    for n in ('worker.cpp','target_capture.hpp','resident_context.hpp','phase_plan.hpp'):shutil.copy2(base/n,dest/n)
    profiler=Path('D:/rtx184-operator/backend_loop4-driver-v5/profiler.inc').read_text().replace('check(','need(').replace('save(p,events)','dump(p,events)')
    profiler=profiler.replace('static uint64_t begin_time;','static uint64_t begin_time;\nstatic uint64_t dropped=0;\nstatic decltype(&cuptiActivityGetNumDroppedRecords) get_dropped;')
    profiler=profiler.replace('consume(CUcontext,uint32_t,','consume(CUcontext context,uint32_t stream,')
    profiler=profiler.replace('    _aligned_free(buf);','    size_t lost=0;need(get_dropped(context,stream,&lost)==CUPTI_SUCCESS,"CUPTI dropped count");dropped+=lost;\n    _aligned_free(buf);')
    profiler=profiler.replace('    timestamp=(decltype(timestamp))GetProcAddress(lib,"cuptiGetTimestamp");','    timestamp=(decltype(timestamp))GetProcAddress(lib,"cuptiGetTimestamp");\n    get_dropped=(decltype(get_dropped))GetProcAddress(lib,"cuptiActivityGetNumDroppedRecords");need(get_dropped,"CUPTI drop function");')
    profiler=profiler.replace('dump(p,events);','dump(p,events);dump(p.parent_path()/"CUPTI-RECEIPT.json",json{{"dropped_records",dropped},{"activity_API","actual CUDA kernels and memcpy"}});')
    (dest/'profiler.inc').write_text(profiler)
    entry=(base/'entry.cpp').read_text().replace('#undef main','#undef main\n#define FRONTIER_PROFILE\n#include "profiler.inc"')
    entry=replace(entry,'        if(job.contains("forced")||job.contains("cases")){','        profile::init();profile::begin();\n        if(job.contains("forced")||job.contains("cases")){')
    entry=replace(entry,'        result["total_observed_API_calls"]=', '        profile::end(root/"cuda-events.json");\n        result["total_observed_API_calls"]=')
    (dest/'entry.cpp').write_text(entry);binary=dest/'bin';binary.mkdir()
    binding=json.loads((base/'BUILD.json').read_bytes())
    for p in (base/'bin').glob('*.dll'):os.link(p,binary/p.name)
    for label in ('worker','link'):
        original=json.loads((base/(label+'.json')).read_bytes())['argv'];argv=[x.replace(str(base/'entry.cpp'),str(dest/'entry.cpp')).replace(str(base/'worker.obj'),str(dest/'worker.obj')).replace(str(base/'bin/worker.exe'),str(binary/'worker.exe')) for x in original]
        if label=='worker':
            argv.insert(2,'-fms-extensions')
            for path in ['cuda_nvcc','cuda_runtime','cuda_cupti']:argv.insert(2,'-IE:/rtx170/profiler/sdk/nvidia/'+path+'/include')
        command(dest,label,argv)
    put(dest/'BUILD.json',dict(binding,exe=sha(binary/'worker.exe'),source_files={p.name:sha(p) for p in dest.iterdir() if p.suffix in ('.cpp','.hpp','.inc')},profiling_only=True,clean_source_executable_sha256=binding['exe'],CUPTI_sha256=sha('E:/rtx170/profiler/sdk/nvidia/cuda_cupti/bin/cupti64_2025.2.1.dll')))

def run(family,lowering):
    row=dict(roots(family)[0]);row['cap']=16
    payload=dict(lowering=lowering,draft=True,draft_width=4,inputs=[dict(name='trace',capture=False,input=row)])
    out=finished(family+'-'+lowering+'-kernel-trace','profiles-final/'+lowering,family,payload,dict(requests=1,token_rows=2*len(row['prompt_ids'])+8*15,operators=0))
    r=json.loads((out/'native/trace/receipt.json').read_bytes());events=json.loads((out/'native/cuda-events.json').read_bytes());api=r['observed_API_calls_within_service'];assert all(v==0 for v in api.values())
    cupti=json.loads((out/'native/CUPTI-RECEIPT.json').read_bytes());assert cupti['dropped_records']==0
    free=json.loads((ROOT/'runs'/(family+'-old-free')/'native/r0-heavy/receipt.json').read_bytes());assert r['ids']==free['ids'][:16]
    kernels=[x for x in events if x['kind']=='kernel'];copies=[x for x in events if x['kind']=='copy'];hist={}
    for x in kernels:hist[x['name']]=hist.get(x['name'],0)+1
    put(ROOT/(family+'-'+lowering+'-CUDA-TRACE.json'),dict(separate_from_clean_timing=True,dropped_records=cupti['dropped_records'],endpoint_prefix_matches_independent_original_R=True,kernels=len(kernels),kernel_histogram=hist,copies=copies,online_API_calls=api,native_result=str(out/'native/result.json'),endpoint=r['endpoint'],phase_executions=r['executions'],GPU_event_durations_not_additive_service_time=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('lowering');p.add_argument('--family',default='Qwen');a=p.parse_args()
    if a.action=='build':build(a.lowering)
    else:run(a.family,a.lowering)
