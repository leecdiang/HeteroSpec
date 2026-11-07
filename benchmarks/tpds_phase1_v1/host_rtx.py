"""RTX review-v2 native adapter, reusing the PR190 supervisor and original R."""
from pathlib import Path
import argparse,datetime,difflib,hashlib,json,os,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'rtx_phase_plan_v1'
sys.path.insert(0,str(PARENT))
import host as prior
sys.path.insert(0,str(HERE))
import stage_native
ROOT=Path('D:/rtx192-review-v2')
P190=Path('D:/rtx188')
DESIGN='d730902c62042a8f5f2b93bb6941ca6678dc1a5a'
LIMITS=dict(requests=3072,token_rows=4000000,operators=0)
VERSION=2
prior.ROOT=ROOT;prior.LIMITS=LIMITS
sha=prior.sha
put=prior.put
MODEL=prior.MODELS

def read(p):return json.loads(Path(p).read_bytes())
def snapshot(p):
    return dict(root=str(p),files={x.relative_to(p).as_posix():sha(x) for x in sorted(p.rglob('*')) if x.is_file() and '.git' not in x.parts})
def command(out,label,argv,cwd=None):
    out.mkdir(parents=True,exist_ok=True);began=time.monotonic()
    env=os.environ.copy();env['ZIG_GLOBAL_CACHE_DIR']=str(ROOT/'compiler-cache');env['TEMP']=str(ROOT/'temp');env['TMP']=env['TEMP'];Path(env['TEMP']).mkdir(exist_ok=True)
    with (out/(label+'.log')).open('xb') as log:r=subprocess.run(argv,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,timeout=1800,env=env)
    put(out/(label+'.json'),dict(argv=list(map(str,argv)),working_directory=str(Path(cwd or os.getcwd()).resolve()),code=r.returncode,seconds=time.monotonic()-began));r.check_returncode()

def stage():
    ROOT.mkdir(exist_ok=False)
    put(ROOT/'HOST_VERSION.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),design=DESIGN,version='review-v2-native-v1',prior_phase1_freezes_or_timing_found=False,observation='No phase1 output/worktree or matching native process existed before this independent worktree was created; PR190 is complete/stopped and untouched.',limits=LIMITS,prior_design_v1='0fddf2255830a563433cb40ae8f6e09341bc702a',old_panels_unchanged=True))
    frozen=read(P190/'SHARED_RULE_FREEZE.json');front={};cores={}
    for recipe,method in [('loop4','SIMPLE'),('packed','LOCAL')]:
        p=Path(frozen['runtimes'][method]['path']);b=frozen['runtimes'][method]['build']
        assert sha(p/'bin/worker.exe')==b['exe']
        assert sha(P190/method/'core/src/libllama.a')==b['core']
        for n,h in b['source_files'].items():assert sha(p/n)==h
        for n,h in b['modules'].items():assert sha(p/'bin'/n)==h
        src=ROOT/'snapshots'/recipe/'source';shutil.copytree(P190/method/'source',src,ignore=shutil.ignore_patterns('.git','__pycache__'))
        dst=ROOT/'snapshots'/recipe/'frontend';dst.mkdir()
        for n in stage_native.FRONTEND:shutil.copy2(p/n,dst/n)
        shutil.copy2(prior.OLD/'arm_spec.h',dst/'arm_spec.h')
        front[recipe]=snapshot(dst);cores[recipe]=snapshot(src)
    a=Path(cores['loop4']['root']);b=Path(cores['packed']['root']);ma=cores['loop4']['files'];mb=cores['packed']['files'];diff=[];patch=[]
    for n in sorted(set(ma)|set(mb)):
        if ma.get(n)==mb.get(n):continue
        diff.append(n)
        aa=(a/n).read_text(encoding='utf8',errors='replace').splitlines(True) if n in ma else []
        bb=(b/n).read_text(encoding='utf8',errors='replace').splitlines(True) if n in mb else []
        patch+=list(difflib.unified_diff(aa,bb,fromfile='loop4/'+n,tofile='packed/'+n))
    (ROOT/'PARENT_CORE_DIFF.patch').write_text(''.join(patch),encoding='utf8')
    # Both cores use the same admitted backend implementation/placement guards.
    # The parent already loaded the loop4-capable DLL for BOTH numerical recipes.
    for n in diff:
        if n.startswith('ggml/'):
            dst=b/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a/n,dst)
    cores['packed']=snapshot(b)
    assert [n for n in sorted(set(ma)|set(cores['packed']['files'])) if ma.get(n)!=cores['packed']['files'].get(n)]==['src/llama-graph.cpp']
    binding=dict(base_commit='a28f3474acac793d07b6e6f462cb70bbccfa6ceb',cores=cores,frontends=front)
    put(ROOT/'PARENT_SOURCE_BINDING.json',binding)
    stage_native.stage(binding,ROOT/'native-v1')
    f=ROOT/'native-v1/frontend';w=f/'worker.cpp';text=w.read_text(encoding='utf8')
    text=stage_native.once(text,'if(spec.scoped)pair.draft=','if(spec.scoped && d)pair.draft=')
    text=stage_native.once(text,'if(capture){std::ofstream f','if(capture){++phase_heavy_captures;std::ofstream f')
    text=stage_native.once(text,'        tpds_decisive::capture_existing(c,model,path/"state"/key,row,plan.logits(row));','        ++phase_heavy_captures;tpds_decisive::capture_existing(c,model,path/"state"/key,row,plan.logits(row));')
    w.write_text(text,encoding='utf8')
    p=f/'entry.cpp';text=p.read_text(encoding='utf8')
    text=stage_native.once(text,'static uint64_t phase_exports=0,phase_imports=0,phase_contexts=0;','static uint64_t phase_exports=0,phase_imports=0,phase_contexts=0,phase_heavy_captures=0;')
    text=stage_native.once(text,'static void observe_state(Context& c,const fs::path& dir,int row,bool state=true){','static void observe_state(Context& c,const fs::path& dir,int row,bool state=true){\n    ++phase_heavy_captures;')
    text=stage_native.once(text,'int main(int argc,char**argv){','#include "rtx_append.inc"\nint main(int argc,char**argv){')
    text=stage_native.once(text,'if(job.contains("forced")||job.contains("cases")){','if(job.contains("append_probes")){phase1_append(job,result,root,pool);}\n        else if(job.contains("forced")||job.contains("cases")){')
    text=stage_native.once(text,'if(capture){const int row=r["cycles"].empty()?', 'r["observed_API_calls_within_service"]["heavy_captures"]=phase_heavy_captures-heavy_before;\n                if(capture){const int row=r["cycles"].empty()?')
    text=stage_native.once(text,'const auto exports=phase_exports,imports=phase_imports,contexts=phase_contexts;','const auto exports=phase_exports,imports=phase_imports,contexts=phase_contexts,heavy_before=phase_heavy_captures;')
    p.write_text(text,encoding='utf8');shutil.copy2(HERE/'native/rtx_append.inc',f/'rtx_append.inc')
    put(ROOT/'SOURCE_ADAPTATION.json',dict(parent_core_differences=diff,normalized_common_backend=True,only_core_factor_difference='src/llama-graph.cpp projection lowering',common_frontend_repairs=['Null draft accepted by provision only for target-only ordinary M','Observed heavy-capture counter','Separate native append window on newly prepared valid state'],numerical_R_unchanged=True,source_snapshot=snapshot(ROOT/'native-v1'),qualified=False))
    for fam in ('Qwen','Smol'):
        src=P190/('R-'+fam)/'runtime-v2';dst=ROOT/('R-'+fam);(dst/'bin').mkdir(parents=True)
        for x in (src/'bin').iterdir():
            if x.is_file():os.link(x,dst/'bin'/x.name)
        shutil.copy2(src/'BUILD.json',dst/'BUILD.json')
    put(ROOT/'R0_SAVED_COSTS.json',__import__('receipts').saved_costs(P190/'confirmation/RESULTS.json',6))
    print('Actual final sources staged; native qualification pending',flush=True)

def revise():
    dest=ROOT/'native-v2';shutil.copytree(ROOT/'native-v1',dest)
    for recipe in ('loop4','packed'):
        src=dest/'cores'/recipe
        p=src/'src/hsc_counter.h';s=p.read_text(encoding='utf8')
        s=stage_native.once(s,'int64_t graphs_reused=0,','int64_t graphs_built=0,graphs_reused=0,')
        s=stage_native.once(s,'inline void reused(void * ctx){','inline void built(void * ctx){if(counted()&&w.context==ctx)w.graphs_built++;}\ninline void reused(void * ctx){');p.write_text(s,encoding='utf8')
        p=src/'src/llama-context.cpp';s=p.read_text(encoding='utf8');s=stage_native.once(s,'        gf = model.build_graph(gparams);','        gf = model.build_graph(gparams);\n        if(gf)hsc::built(this);');p.write_text(s,encoding='utf8')
    f=dest/'frontend';p=f/'worker.cpp';s=p.read_text(encoding='utf8')
    s=stage_native.once(s,'hsc::begin(capture?"heavy":"baseline",','hsc::begin(capture?"heavy":"counts",')
    s=stage_native.once(s,'r["graphs_reused"]=capture?json(hsc::w.graphs_reused):json(nullptr);','r["graphs_reused"]=hsc::w.graphs_reused;r["graphs_built"]=hsc::w.graphs_built;r["observer_mode"]=capture?"heavy":"counts";');p.write_text(s,encoding='utf8')
    profiler=P190/'profiles-final/SIMPLE/profiler.inc';s=profiler.read_text(encoding='utf8')
    s=stage_native.once(s,'auto lib=LoadLibraryW(L"E:/rtx170/profiler/sdk/nvidia/cuda_cupti/bin/cupti64_2025.2.1.dll");','auto lib=LoadLibraryW(fs::path(std::getenv("PHASE1_CUPTI_LIBRARY")?std::getenv("PHASE1_CUPTI_LIBRARY"):"E:/rtx170/profiler/sdk/nvidia/cuda_cupti/bin/cupti64_2025.2.1.dll").c_str());')
    (f/'profiler.inc').write_text(s,encoding='utf8')
    p=f/'entry.cpp';s=p.read_text(encoding='utf8');s=stage_native.once(s,'#undef main','#undef main\n#define FRONTIER_PROFILE\n#include "profiler.inc"\nstatic bool phase1_profiling=false;')
    s=stage_native.once(s,'        if(job.contains("append_probes")){','        phase1_profiling=job.value("profile",false);if(phase1_profiling){profile::init();if(!job.contains("append_probes"))profile::begin();}\n        if(job.contains("append_probes")){')
    s=stage_native.once(s,'        result["total_observed_API_calls"]=', '        if(phase1_profiling && !job.contains("append_probes"))profile::end(root/"cuda-events.json");\n        result["total_observed_API_calls"]=');p.write_text(s,encoding='utf8')
    shutil.copy2(HERE/'native/rtx_append.inc',f/'rtx_append.inc')
    put(ROOT/'NATIVE_REVISION_2.json',dict(reason='Observe real graph build/reuse/physical work in common non-heavy counts mode; optional separately labelled CUPTI profiling. No R change and no formal panel started.',prior_loop4_build_retained=True,native_GPU_requests_before_revision=0,source_snapshot=snapshot(dest)))
    print('Revision2 source prepared; exact version still needs native qualification',flush=True)

def build(recipe):
    base=ROOT/f'native-v{VERSION}';src=base/'cores'/recipe;core=ROOT/f'build-v{VERSION}'/recipe;core.mkdir(parents=True,exist_ok=False)
    for n in ('ar.cmd','ranlib.cmd'):shutil.copy2(P190/'SIMPLE/core'/n,core/n)
    old=read(P190/'SIMPLE/configure.json')['argv']
    argv=[x.replace(str(P190/'SIMPLE/source'),str(src)).replace(str(P190/'SIMPLE/core'),str(core)) for x in old]
    command(core,'configure',argv)
    command(core,'core',[argv[0],'--build',str(core),'--target','llama','vendor-hash','-j','4'])
    f=base/'frontend';dest=ROOT/(f'runtime-v{VERSION}-'+recipe);dest.mkdir();(dest/'bin').mkdir()
    old=read(P190/'SIMPLE/runtime-v5/worker.json')['argv']
    argv=[x.replace(str(P190/'SIMPLE/source'),str(src)).replace(str(P190/'SIMPLE/core'),str(core)).replace(str(P190/'SIMPLE/runtime-v5'),str(f)).replace(str(prior.OLD),str(f)) for x in old]
    argv=[str(dest/'worker.obj') if x==str(f/'worker.obj') else x for x in argv]
    argv[2:2]=['-MD','-MF',str(dest/'worker.d')]
    argv[2:2]=['-fms-extensions']+['-IE:/rtx170/profiler/sdk/nvidia/'+x+'/include' for x in ('cuda_nvcc','cuda_runtime','cuda_cupti')]
    command(dest,'worker',argv)
    old=read(P190/'SIMPLE/runtime-v5/link.json')['argv']
    argv=[x.replace(str(P190/'SIMPLE/core'),str(core)).replace(str(P190/'SIMPLE/runtime-v5'),str(dest)) for x in old];argv.insert(2,'-v')
    command(dest,'link',argv)
    for p in (P190/'SIMPLE/runtime-v5/bin').glob('*.dll'):os.link(p,dest/'bin'/p.name)
    put(dest/'BUILD.json',dict(exe=sha(dest/'bin/worker.exe'),core=sha(core/'src/libllama.a'),modules={p.name:sha(p) for p in (dest/'bin').glob('*.dll')},source_files=snapshot(f)['files'],qualified=False))
    print('Built actual native recipe',recipe,flush=True)

def execute(label,recipe,family,payload,reservation):
    return prior.execute(label,recipe if recipe.startswith('R-') else f'runtime-v{VERSION}-'+recipe,family,payload,reservation)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','revise','build']);p.add_argument('recipe',nargs='?');a=p.parse_args()
    if a.action=='stage':stage()
    elif a.action=='revise':revise()
    else:build(a.recipe)
