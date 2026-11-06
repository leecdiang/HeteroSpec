"""Port #64's synchronize/bind/reserve sequence into a private source overlay.
The original R library is never edited; native build and qualification are pending.
"""
from pathlib import Path
import argparse, difflib, hashlib, json
from stage_costs import once

def stage(source,pins,out,widths=(1,128)):
    source=Path(source).resolve();out=Path(out).resolve()
    widths=tuple(sorted(set(widths)))
    if not widths or any(type(x)!=int or x<1 or x>128 for x in widths):raise ValueError('Widths must be explicit integers in1..128')
    if out.exists() or source in out.parents or out in source.parents:raise ValueError('Fresh independent overlay required')
    manifest=json.loads(Path(pins).read_text());raw={}
    for name in ('llama-context.h','llama-context.cpp'):
        p=source/'src'/name
        if p.is_symlink():raise ValueError('Source symlink')
        raw[name]=p.read_bytes()
        if hashlib.sha256(raw[name]).hexdigest()!=manifest['files']['src/'+name]:raise ValueError('Source binding mismatch: '+name)
    old={k:v.decode().replace('\r\n','\n') for k,v in raw.items()};new=dict(old)
    new['llama-context.h']=once(new['llama-context.h'],'    void sched_reserve();',
        '    void sched_reserve();\n    void b570_economics_bind_phase(uint32_t ub);')
    valid=' && '.join('ub != '+str(w) for w in widths)
    new['llama-context.cpp']+=f'''
// Reuses PR64's private phase mutation; not a new algorithm or a qualification.
void llama_context::b570_economics_bind_phase(uint32_t ub) {{
    if (({valid}) || cparams.n_ctx != 1024 || cparams.n_batch != 512 || cparams.n_seq_max != 1)
        throw std::runtime_error("B570 economics phase profile mismatch");
    synchronize();
    if (cparams.n_ubatch != ub) {{
        cparams.n_ubatch = ub;
        sched_need_reserve = true;
        sched_reserve();
    }}
}}
#ifdef _WIN32
#define B570_ECON_EXPORT __declspec(dllexport)
#else
#define B570_ECON_EXPORT __attribute__((visibility("default")))
#endif
extern "C" B570_ECON_EXPORT int b570_economics_bind_phase(llama_context *ctx,uint32_t ub) noexcept {{
    if (!ctx) return 1;
    try {{ctx->b570_economics_bind_phase(ub);return 0;}} catch (...) {{return 2;}}
}}
// Any nonzero result invalidates this request/context. Do not continue or retry
// against a partially changed allocation. Original R remains a separate binary.
'''
    (out/'src').mkdir(parents=True)
    patches=[]
    for name,text in new.items():
        (out/'src'/name).write_text(text,encoding='utf-8',newline='\n')
        patches.extend(difflib.unified_diff(old[name].splitlines(True),text.splitlines(True),fromfile='a/src/'+name,tofile='b/src/'+name))
    (out/'phase.patch').write_text(''.join(patches))
    report={'status':'PRIVATE_SOURCE_OVERLAY_ONLY','derived_from_PR64':True,'allowed_widths':widths,
       'profile':{'context':1024,'batch':512,'sequences':1},'original_reference_changed':False,
       'new_kernel':False,'output_reserve_modified':False,'native_build':'NOT_RUN','GPU_qualification':'NOT_RUN',
       'input_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},
       'output_sha256':{k:hashlib.sha256((out/'src'/k).read_bytes()).hexdigest() for k in new}}
    (out/'STAGE.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('source','pins','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--widths',type=int,nargs='+',default=[1,128]);a=p.parse_args()
    print(json.dumps(stage(a.source,a.pins,a.out,a.widths),indent=2))
