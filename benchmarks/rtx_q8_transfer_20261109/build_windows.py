"""Build new M2 frontends against immutable, qualified Windows archives."""
from pathlib import Path
import difflib, importlib.util, json, os, shutil, subprocess, time
from admission import HERE, ROOT, sha, put

BASE=Path('D:/rtx192-review-v2')
WORK=Path('D:/rtx211-q8-20261109')

def main():
    WORK.mkdir(exist_ok=False);front=WORK/'frontend';shutil.copytree(BASE/'native-v2/frontend',front)
    old={p.name:p.read_bytes() for p in front.iterdir() if p.is_file()}
    m2=ROOT/'pinned_sources/benchmarks/server_expansion_v1/M2'
    spec=importlib.util.spec_from_file_location('m2_transform',m2/'transform.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.transform(front)
    # Heavy qualification must observe every committed state, as in PR203/209.
    p=front/'worker.cpp';s=p.read_text();s=module.once(s,'inline bool phase_observe=false;','inline bool phase_observe=false;\ninline int phase_threads=24;')
    s=module.once(s,'if (!capture || !target || (key!="initial" && key!="commit-0")) return;','if (!capture || !target) return;');p.write_text(s)
    for name,src in [('m2_tapes.hpp','tapes.hpp'),('m1_capability.hpp','capability.hpp')]:shutil.copy2(m2/'native'/src,front/name)
    p=front/'m1_capability.hpp';s=p.read_text();s=module.once(s,'"M1 dense cache required"','"RTX dense cache required"');s=module.once(s,'    need(job.at("n_ctx")==llama_n_ctx(pool.target->c),"Ignored context request");','    need(job.at("n_ctx")==llama_n_ctx(pool.target->c),"Ignored context request");\n    need(job.at("threads")==24,"Original Windows thread count required");');p.write_text(s)
    p=front/'entry.cpp';s=p.read_text();s=module.once(s,'static json module_inventory()','#include "m1_capability.hpp"\nstatic json module_inventory()')
    s=module.once(s,'        phase1_profiling=job.value("profile",false);','        m1_capability(job,pool,t,d,spec,root,result);\n        phase1_profiling=job.value("profile",false);');p.write_text(s)
    patches=[]
    for p in sorted(front.iterdir()):
        if p.is_file():patches.extend(difflib.unified_diff(old.get(p.name,b'').decode().splitlines(True),p.read_text().splitlines(True),fromfile='PR195/'+p.name,tofile='RTX211/'+p.name))
    (WORK/'WINDOWS_FRONTEND.patch').write_text(''.join(patches))
    shutil.copytree(front,ROOT/'candidate_frontend_v1')
    put(WORK/'SOURCE.json',dict(parent='873d16712fbf3bc04f54e9b3753515c5dbebb60f',m2_native_source='61bcce0552b1a80e9345fa199238ebb7bc63e6ff',
        frontend={p.name:sha(p) for p in front.iterdir() if p.is_file()},patch_sha256=sha(WORK/'WINDOWS_FRONTEND.patch'),
        numerical_core_edits=False,original_R_edits=False,threads=24,qualification='NOT_RUN',same_work_frontend='PENDING_SEPARATE_REVIEW_BEFORE_FINAL_EPOCH'))
    commands=[]
    for core in ('loop4','packed'):
        before=json.loads((BASE/f'runtime-v2-{core}/BUILD.json').read_bytes());assert sha(BASE/f'build-v2/{core}/src/libllama.a')==before['core']
        out=WORK/core;out.mkdir();(out/'bin').mkdir()
        for label in ('worker','link'):
            old_run=BASE/f'runtime-v2-{core}'
            args=json.loads((old_run/(label+'.json')).read_bytes())['argv']
            args=[x.replace(str(old_run),str(out)).replace(str(BASE/'native-v2/frontend'),str(front)) for x in args]
            if label=='worker':args.insert(2,'-DM1_PROJECTION="'+core+'"')
            env=os.environ.copy();env.update(ZIG_GLOBAL_CACHE_DIR=str(WORK/'compiler-cache'),TEMP=str(WORK/'temp'),TMP=str(WORK/'temp'));(WORK/'temp').mkdir(exist_ok=True)
            began=time.monotonic()
            with (out/(label+'.log')).open('xb') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=900)
            record=dict(argv=args,cwd=str(Path.cwd()),seconds=time.monotonic()-began,code=r.returncode);put(out/(label+'.json'),record);commands.append(record);r.check_returncode()
        for p in (BASE/f'runtime-v2-{core}/bin').glob('*.dll'):shutil.copy2(p,out/'bin'/p.name)
        put(out/'BUILD.json',dict(exe=sha(out/'bin/worker.exe'),core=before['core'],modules={p.name:sha(p) for p in (out/'bin').glob('*.dll')},
            original_build_sha256=sha(BASE/f'runtime-v2-{core}/BUILD.json'),frontend_sha256=sha(WORK/'SOURCE.json'),qualified=False))
    put(ROOT/'BUILD_PREPARATION.json',dict(status='BOTH_FRONTENDS_BUILT_NOT_QUALIFIED',work=str(WORK),commands=commands,model_forward_requests=0,
        original_archives_and_R_unchanged=True,source_sha256=sha(WORK/'SOURCE.json')))
    print('Both Windows reserve8 frontends built; no model forwards; qualification pending',flush=True)

if __name__=='__main__':main()
