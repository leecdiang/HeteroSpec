"""Original RTX host build/run bindings. A build is never a qualification."""
from pathlib import Path
import argparse,ctypes,hashlib,json,os,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'tpds_decisive_v1'
sys.path.insert(0,str(PREVIOUS))
from runner import Ledger,kill_owned
ROOT=Path('D:/rtx188')
OLD=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-original-v4')
META=OLD.parent/'native-metadata4-v4'
LIMITS=dict(requests=4096,token_rows=12000000,operators=1536)
MODELS={
 'Qwen':dict(target_model='D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf',draft_model='D:/HeteroSpec-PC/models/gguf/Qwen3-0.6B-Q8_0.gguf',target_sha256='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6',draft_sha256='9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'),
 'Smol':dict(target_model='C:/Users/ASUS/Documents/Codex/2026-10-10/kan/work/jsa/models/SmolLM2-1.7B-Instruct-Q8_0.gguf',draft_model='C:/Users/ASUS/Documents/Codex/2026-10-10/kan/work/jsa/models/SmolLM2-135M-Instruct-Q8_0.gguf',target_sha256='0c6e8955788b1253f418c354a4bdc4cf507b8cfe49c48bb10c7c58ae713cfa2a',draft_sha256='40f7094960b6ede829145d102ca79451b364b27d9d8694d4406e002024cff357')}

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(x,f,indent=2)
def command(out,label,argv):
    began=time.monotonic()
    env=os.environ.copy();env['ZIG_GLOBAL_CACHE_DIR']=str(ROOT/'compiler-cache');env['TEMP']=str(ROOT/'temp');env['TMP']=env['TEMP'];Path(env['TEMP']).mkdir(exist_ok=True)
    with (out/(label+'.log')).open('xb') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=1800,env=env)
    put(out/(label+'.json'),dict(argv=argv,code=r.returncode,seconds=time.monotonic()-began));r.check_returncode()
def replace(s,a,b):
    if s.count(a)!=1:raise RuntimeError('source anchor: '+a[:90])
    return s.replace(a,b,1)

def stage():
    ROOT.mkdir(exist_ok=False)
    put(ROOT/'PROVENANCE.json',dict(design_head='de96c18ced307b480f360d4d88a85792fc71fd6c',historical_results_unchanged=True,limits=LIMITS,output_disk_reserve=20*1024**3,system_disk_reserve=10*1024**3,note='Only D is a write destination; C has pre-existing lower free space. Preserve a10GiB system-volume reserve while retaining20GiB on output D. No reduced RAM/GPU reserve.'))
    for lowering,arm in [('SIMPLE','backend_loop4'),('LOCAL','packed')]:
        dest=ROOT/lowering;dest.mkdir();src=dest/'source'
        shutil.copytree(Path('F:/rtx184/loop/native-arms')/arm,src,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc'))
        h=src/'src/llama-kv-cache.h';s=h.read_text();s=replace(s,'    uint32_t get_n_kv(const slot_info & sinfo) const;','    std::vector<uint32_t> phase_append_requirements(uint32_t position,uint32_t width) const;\n    uint32_t phase_current_extent() const;\n    uint32_t get_n_kv(const slot_info & sinfo) const;');h.write_text(s)
        p=src/'src/llama-kv-cache.cpp';s=p.read_text();anchor='uint32_t llama_kv_cache::get_n_kv(const slot_info & sinfo) const {'
        extra='''std::vector<uint32_t> llama_kv_cache::phase_append_requirements(uint32_t position,uint32_t width) const {
    if(n_stream!=1 || n_swa || !width) return {};
    const auto& cells=v_cells[0];
    if(cells.get_has_shift() || cells.get_used()!=position || cells.used_max_p1()!=position || v_heads[0]!=position || uint64_t(position)+width>cells.size()) return {};
    for(uint32_t i=0;i<position;++i) if(cells.is_empty(i) || cells.pos_get(i)!=int32_t(i) || !cells.seq_has(i,0)) return {};
    hs_reference_batching::DenseAppendState state{position,width,position+width,position+width,cells.size(),std::max(n_pad,256u),1,true,false};
    return hs_reference_batching::scalar_prefix_requirements(state).extents;
}
uint32_t llama_kv_cache::phase_current_extent() const {slot_info s;s.strm={0};s.idxs={{0}};return get_n_kv(s);}

'''
        p.write_text(replace(s,anchor,extra+anchor))
        for name in ('phase_plan.hpp','resident_context.hpp'):shutil.copy2(HERE/'native'/name,dest/name)
    put(ROOT/'STAGED.json',dict(shared_rule_sha256=sha(HERE/'native/resident_context.hpp'),native_helpers_sha256=sha(HERE/'native/phase_plan.hpp'),source_family='PR171/186 candidate, direct PR151 old-R bridge required',qualified=False))

def build_core(lowering):
    dest=ROOT/lowering;src=dest/'source';core=dest/'core';core.mkdir()
    binding=json.loads((OLD/'BUILD.json').read_bytes())
    for n in ('ar.cmd','ranlib.cmd'):shutil.copy2(OLD/'core'/n,core/n)
    cmd=next(x['argv'] for x in binding['commands'] if x['label']=='configure')
    cmd=[x.replace(str(OLD/'source'),str(src)).replace(str(OLD/'core'),str(core)) for x in cmd]
    command(dest,'configure',cmd)
    command(dest,'core',[cmd[0],'--build',str(core),'--target','llama','vendor-hash','-j','4'])
    put(dest/'CORE_BUILD.json',dict(core_sha256=sha(core/'src/libllama.a'),source=str(src),qualified=False))

def worker(name):
    candidate=name in ('SIMPLE','LOCAL');old=OLD if name!='R-Smol' else META
    base=ROOT/name;dest=base
    if (base/'BUILD.json').exists():
        revision=2
        while (base/('runtime-v'+str(revision))).exists():revision+=1
        dest=base/('runtime-v'+str(revision));dest.mkdir()
    if not candidate:dest.mkdir(exist_ok=True)
    source=base/'source' if candidate else old/'source';core=base/'core' if candidate else old/'core'
    s=Path('F:/rtx184/draft-v3/D1/worker.cpp').read_text()
    s=s.replace('    if(!capture){auto diagnostic=Clock::now();target->capture=true;target->snapshot("final-clean",final_frontier);target->capture=false;r["post_service_state_seconds"]=since(diagnostic);}', '')
    s=replace(s,'if (!capture || !target) return;','if (!capture || !target || (key!="initial" && key!="commit-0")) return;')
    if candidate:
        for n in ('phase_plan.hpp','resident_context.hpp'):shutil.copy2(HERE/'native'/n,dest/n)
        s=replace(s,'struct Context {','#include "resident_context.hpp"\nstruct Context {\n    PhaseContext plan;')
        s=replace(s,'static constexpr int draft_ubatch=1;','')
        s=replace(s,'#include "resident_context.hpp"','#include "resident_context.hpp"\n#define draft_ubatch phase_draft_width')
        s=replace(s,'auto&o=*static_cast<Observer*>(opaque);','auto&o=*static_cast<Observer*>(opaque);if(!phase_observe)return false;')
        # The observer definition precedes resident_context.hpp.
        s=replace(s,'struct Observer {','inline bool phase_observe=false;\nstruct Observer {')
        h=dest/'resident_context.hpp';h.write_text(h.read_text().replace('inline bool phase_observe=false;',''))
        s=replace(s,'p.n_ubatch=istarget?ub:draft_physical;','p.n_ubatch=istarget?ub:phase_draft_width;')
        s=replace(s,'p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;','p.n_outputs_max=istarget?4:1;p.n_outputs_max_per_seq=istarget?4:1;')
        s=replace(s,'c=llama_init_from_model(m,p);need(c,"context initialization");','hs_scope::active=false;c=llama_init_from_model(m,p);need(c,"context initialization");hs_scope::active=scoped;')
        s=replace(s,'capture=cap;path=dir;calls=0;','plan.clear();capture=cap;path=dir;calls=0;')
        anchor='    void decode(const std::vector<int>&ids,int pos,bool all,const char*phase){'
        s=replace(s,anchor,anchor+'\n        if(target){if(capture)caller_trace.push_back({{"phase",phase},{"position",pos},{"rows",ids.size()},{"all_outputs",all}});plan.decode(*this,ids,pos,all,phase);return;}')
        s=replace(s,'auto*p=llama_get_logits_ith(c,row);','auto*p=target?plan.logits(row):llama_get_logits_ith(c,row);')
        s=replace(s,'tpds_decisive::capture_existing(c,model,path/"state"/key,row);','tpds_decisive::capture_existing(c,model,path/"state"/key,row,plan.logits(row));')
        s=replace(s,'r["target_calls"]=target->calls;','r["phase_executions"]=target->plan.executions;r["target_calls"]=target->calls;')
    (dest/'worker.cpp').write_text(s,encoding='utf8');shutil.copy2(HERE/'native/phase_entry.cpp',dest/'entry.cpp')
    cap=(PREVIOUS/'native/target_capture.hpp').read_text()
    if candidate:
        cap=cap.replace('const std::filesystem::path& dir,int frontier_row)', 'const std::filesystem::path& dir,int frontier_row,const float* supplied=nullptr)')
        cap=cap.replace('const float* p=llama_get_logits_ith(ctx,frontier_row);','const float* p=supplied?supplied:llama_get_logits_ith(ctx,frontier_row);')
    (dest/'target_capture.hpp').write_text(cap)
    binding=json.loads((old/'BUILD.json').read_bytes());binary=dest/'bin';binary.mkdir()
    runtime=Path('D:/rtx184-operator/backend_loop4-service-v4/bin') if candidate else old/'bin'
    for p in runtime.glob('*.dll'):
        target=binary/p.name
        if p.stat().st_dev==binary.stat().st_dev:os.link(p,target)
        else:shutil.copy2(p,target)
    for record in binding['commands']:
        if record['label'] not in ('worker','link'):continue
        argv=[x.replace(str(old/'source'),str(source)).replace(str(old/'core'),str(core)).replace(str(old/'worker.cpp'),str(dest/'entry.cpp')).replace(str(old/'worker.obj'),str(dest/'worker.obj')).replace(str(old/'bin/rtx-scope-transfer.exe'),str(binary/'worker.exe')) for x in record['argv']]
        if record['label']=='worker':argv.insert(2,'-DPHASE_CANDIDATE='+str(int(candidate)))
        command(dest,record['label'],argv)
    put(dest/'BUILD.json',dict(exe=sha(binary/'worker.exe'),core=sha(core/'src/libllama.a'),modules={p.name:sha(p) for p in binary.glob('*.dll')},source_files={p.name:sha(p) for p in dest.iterdir() if p.suffix in ('.cpp','.hpp')},reference_family=old.name if not candidate else None,qualified=False))

class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]

def execute(label,name,family,payload,reservation,output=None):
    out=Path(output) if output else ROOT/'runs'/label;out.mkdir(parents=True,exist_ok=False)
    ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.reserve(label,reservation)
    historical='historical' in payload
    if historical:
        origin=OLD if family=='Qwen' else META;original=json.loads((origin/'BUILD.json').read_bytes());exe=origin/'bin/rtx-scope-transfer.exe';build=dict(exe=original['executable_sha256'],modules=original['numerical_modules'],core=original['core_sha256'])
    else:exe=ROOT/name/'bin/worker.exe';build=json.loads((exe.parent.parent/'BUILD.json').read_bytes())
    job=dict(MODELS[family],**payload)
    put(out/'job.json',job);put(out/'binding.json',build);p=None;owned=False;status='FAILED';code=None;began=time.monotonic()
    lock=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock')
    try:
        assert sha(exe)==build['exe']
        for n,h in build['modules'].items():assert sha(exe.parent/n)==h
        for role in ('target','draft'):assert sha(job[role+'_model'])==job[role+'_sha256']
        with lock.open('x') as f:json.dump(dict(pid=os.getpid(),job=label),f)
        owned=True
        if historical:
            for key in ('panel','slots','binding','plan'):put(out/('original-'+key+'.json'),payload['historical'][key])
            cmd=[str(exe),str(out/'native'),job['target_model'],job['draft_model'],str(out/'original-panel.json'),str(out/'original-slots.json'),payload['historical']['family'],str(out/'original-binding.json'),str(out/'original-plan.json')]
        else:cmd=[str(exe),str(out/'job.json'),str(out/'native')]
        put(out/'launch.json',dict(argv=cmd,reservation=reservation,limits=LIMITS,wall_limit_s=1800,output_disk_free_min=20*1024**3,system_disk_free_min=10*1024**3,ram_free_min=4*1024**3,gpu_free_min=128*1024**2))
        env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))}
        with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr,(out/'resources.jsonl').open('x') as telemetry:
            p=subprocess.Popen(cmd,stdin=subprocess.PIPE if historical else None,stdout=stdout,stderr=stderr,env=env,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            if historical:p.stdin.write(b'RUN\n'+b'CONTINUE\n'*len(payload['historical']['slots']));p.stdin.close()
            while p.poll() is None:
                m=Memory();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
                measured=subprocess.check_output(['nvidia-smi','--query-gpu=memory.free,temperature.gpu,clocks.current.graphics,power.draw','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
                gpu=int(measured[0])*1024**2
                row=dict(seconds=time.monotonic()-began,disk_free=shutil.disk_usage(out).free,ledger_disk_free=shutil.disk_usage(ROOT).free,system_free=shutil.disk_usage('C:/').free,ram_free=m.available,gpu_free=gpu,gpu_temperature_C=measured[1].strip(),gpu_graphics_clock_MHz=measured[2].strip(),gpu_power_W=measured[3].strip())
                telemetry.write(json.dumps(row)+'\n');telemetry.flush()
                assert row['seconds']<1800 and row['disk_free']>=20*1024**3 and row['ledger_disk_free']>=20*1024**3 and row['system_free']>=10*1024**3 and row['ram_free']>=4*1024**3 and gpu>=128*1024**2,'live resource limit'
                time.sleep(2)
            code=p.returncode;assert code==0,('native exit',code)
        result=json.loads((out/'native/result.json').read_bytes());assert result['status']=='COMPLETE'
        if historical:
            records=[json.loads((out/'native'/r['record']).read_bytes()) for r in result['requests']]
            actual=dict(requests=len(records),token_rows=sum(len(r['prompt_ids'])+len(r['ids'])-1 for r in records),operators=0)
        else:actual=dict(requests=result['trajectories'],token_rows=result['token_rows'],operators=0)
        for k,v in actual.items():assert v<=reservation[k],(k,v,reservation[k])
        inventory={}
        for key in ('modules_before','modules_after'):
            inventory[key]=[]
            for value in result.get(key,result.get('modules',[])):
                if isinstance(value,dict):value=value['path']
                pth=Path(value);h=sha(pth);inventory[key].append(dict(path=value,sha256=h))
                if pth.name in build['modules']:assert h==build['modules'][pth.name]
                elif pth.name.lower().startswith(('ggml','cublas','cudart')):raise RuntimeError('unbound numerical module '+value)
        put(out/'ACTUAL_MODULES.json',inventory);put(out/'COMPLETE.json',dict(actual_work=actual,qualified=False));status='COMPLETE';print(label,'complete',actual,flush=True)
    except BaseException as e:put(out/'failure.json',dict(error=repr(e)));raise
    finally:
        if p is not None:kill_owned(p)
        if owned:lock.unlink()
        put(out/'exit.json',dict(status=status,code=code,seconds=time.monotonic()-began));ledger.finish(label,status,code);ledger.close()
    return out

def witness(name):
    prior=json.loads(Path('D:/rtx184-runs/D-main-forced-10/job.json').read_bytes())['forced'];suffix=prior['paths'][0]['suffix'][:67]
    assert len(prior['prompt_ids'])==704 and suffix[63:67]==[220,16,198,286]
    calls=[dict(ids=prior['prompt_ids'],phase='PREFILL',all=False)]+[dict(ids=[x],phase='ORDINARY') for x in suffix[:63]]+[dict(ids=suffix[63:67],phase='VERIFY')]
    lowering='SIMPLE' if name.startswith('SIMPLE') else 'LOCAL'
    return execute('retained-witness-'+name.replace('/','-'),name,'Qwen',dict(lowering=lowering,forced=calls,observe_positions=[704,767,768,769,770,771],state_positions=[704,767,771]),dict(requests=1,token_rows=771,operators=0))

def dedup():
    # Same storage operation used by PR186. Every logical capture path remains.
    pool=ROOT/'evidence-cas';pool.mkdir(exist_ok=True);rows=[]
    paths=[p for base in [ROOT/'runs',Path('E:/rtx188/runs')] for p in base.rglob('*') if p.is_file() and p.suffix in ('.bin','.f32')]
    paths+=list(ROOT.glob('*/bin/*.dll'))+list(ROOT.glob('*/runtime-*/bin/*.dll'))
    for p in sorted(paths):
        h=sha(p);volume_pool=pool if p.drive.casefold()==ROOT.drive.casefold() else Path('E:/rtx188/evidence-cas');volume_pool.mkdir(parents=True,exist_ok=True);dest=volume_pool/h[:2]/h;dest.parent.mkdir(exist_ok=True)
        if dest.exists():
            assert sha(dest)==h
            if os.path.samefile(p,dest):continue
            temporary=p.with_name(p.name+'.dedup');assert not temporary.exists();os.link(dest,temporary);os.replace(temporary,p)
        else:os.link(p,dest)
        rows.append(dict(path=str(p),sha256=h,bytes=p.stat().st_size))
    put(ROOT/('STORAGE-'+str(time.time_ns())+'.json'),dict(method='verified same-volume hardlinks; every logical file retained',files=rows));print('deduplicated',len(rows),'capture paths',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name',nargs='?');a=p.parse_args()
    if a.action=='stage':stage()
    elif a.action=='core':build_core(a.name)
    elif a.action=='worker':worker(a.name)
    elif a.action=='witness':witness(a.name)
    elif a.action=='dedup':dedup()
