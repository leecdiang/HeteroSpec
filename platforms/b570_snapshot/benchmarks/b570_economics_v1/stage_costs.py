"""Add mode0/host-clock/synchronized diagnostics to a frozen PR187 frontend.
No inference, no mutation of the source tree, no removal of original checks.
"""
from pathlib import Path
import argparse, hashlib, json, shutil
HERE = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Review source drift; expected one anchor: '+old[:100])
    return text.replace(old, new, 1)

def observer(text):
    text = '#include "cost_clock.hpp"\n'+text
    for anchor, extra in (
        ('void reset(const pj &req){', 'b570_cost::reset();'),
        ('void begin(llama_context * ctx,llama_batch b) {',
         '\n b570_cost::begin_decode(role,phase,b.n_tokens,[&]{llama_synchronize(ctx);});'),
        ('void end(llama_context * ctx,int code) {',
         '\n b570_cost::end_decode([&]{llama_synchronize(ctx);});'),
    ):
        text = once(text, anchor, anchor+extra)
    # Scope all migration work, including fields/comparisons left outside subspans.
    text = once(text, 'auto before=state(src);auto p=positions(src);',
        'b570_cost::Span transition_span(b570_cost::Phase::transition);\n'
        'auto before=b570_cost::measure(b570_cost::Phase::export_source,[&]{return state(src);});auto p=positions(src);')
    changes = {
        'auto * clone=common_sampler_clone(sampler);':
        'auto * clone=b570_cost::measure(b570_cost::Phase::sampler_clone,[&]{return common_sampler_clone(sampler);});',
        'auto * dst=llama_init_from_model(model,cp);':
        'auto * dst=b570_cost::measure(b570_cost::Phase::context_create,[&]{return llama_init_from_model(model,cp);});',
        'size_t consumed=llama_state_set_data(dst,before.data(),before.size());':
        'size_t consumed=b570_cost::measure(b570_cost::Phase::import_state,[&]{return llama_state_set_data(dst,before.data(),before.size());});',
        'auto restored=state(dst),after=state(src);':
        'auto restored=b570_cost::measure(b570_cost::Phase::export_destination,[&]{return state(dst);});\n'
        'auto after=b570_cost::measure(b570_cost::Phase::export_source_after,[&]{return state(src);});',
    }
    for old,new in changes.items():
        text=once(text,old,new)
    # Include BOTH equality checks in transfer JSON and the subsequent gate.
    start='        transfer={{"before",p}'
    stop='throw std::runtime_error("Transfer gate failed");'
    text=once(text,start,'        { b570_cost::Span checks_span(b570_cost::Phase::state_checks);\n'+start)
    text=once(text,stop,stop+'\n        }')
    return text

def frontend(text, target=False):
    if '"service_ms"' not in text:
        raise ValueError('Expected PR187 full-service clock; do not relabel legacy generation clock')
    if target:
        old='if(ctx!=source_target){common_sampler_free(sampler);llama_free(ctx);}'
        new='if(ctx!=source_target)b570_cost::measure(b570_cost::Phase::context_destroy,[&]{common_sampler_free(sampler);llama_free(ctx);});'
        close='metrics_file.close();'
    else:
        old='if(ctx_tgt!=source_target)llama_free(ctx_tgt);'
        new='if(ctx_tgt!=source_target)b570_cost::measure(b570_cost::Phase::context_destroy,[&]{llama_free(ctx_tgt);});'
        close='result_file.close();'
    text=once(text,old,new)
    return once(text,close,close+'\n    b570_cost::write(observer.path+".cost.json");')

def stage(source, pins, out, mode, active='both'):
    source=Path(source).resolve();out=Path(out).resolve()
    if mode not in (0,1,2) or active not in ('both','target','native') or out.exists() or source in out.parents or out in source.parents:
        raise ValueError('Use a fresh output outside the frozen source, mode0/1/2')
    manifest=json.loads(Path(pins).read_text())
    raw={}
    for name in ('observer.h','native.cpp','target.cpp','CMakeLists.txt'):
        p=source/name
        if p.is_symlink(): raise ValueError('Source symlink')
        raw[name]=p.read_bytes()
        if digest(raw[name]) != manifest['files'][name]:
            raise ValueError('Frozen source SHA256 differs: '+name)
    text={k:v.decode().replace('\r\n','\n') for k,v in raw.items()}
    text['observer.h']=observer(text['observer.h'])
    # PR187 froze each arm's measured frontend; its unused companion may retain
    # the earlier generation-only clock. Never relabel that inactive clock.
    if active in ('both','native'):text['native.cpp']=frontend(text['native.cpp'])
    if active in ('both','target'):text['target.cpp']=frontend(text['target.cpp'],True)
    text['CMakeLists.txt']+='\n# Diagnostic-only frontend build, never rebuild numerical DLLs here.\n'
    for target,spec in (('b570-closeout-native',1),('b570-closeout-target',0)):
        text['CMakeLists.txt']+=f'if(TARGET {target})\n target_compile_definitions({target} PRIVATE B570_COST_MODE={mode} B570_ECON_SPEC={spec})\nendif()\n'
    out.mkdir(parents=True)
    for p in source.iterdir():
        if p.is_symlink(): raise ValueError('Symlink in input directory')
        if p.is_file() and p.suffix.lower() in ('.h','.hpp','.inc','.cpp','.txt'):
            shutil.copyfile(p,out/p.name)
    for name,contents in text.items(): (out/name).write_text(contents,encoding='utf-8',newline='\n')
    shutil.copyfile(HERE/'native/cost_clock.hpp',out/'cost_clock.hpp')
    record={'status':'SOURCE_STAGED_NOT_NATIVE_COMPILED','mode':mode,
        'base_receipt':manifest.get('receipt'), 'input_sha256':{k:digest(v) for k,v in raw.items()},
        'output_sha256':{k:digest((out/k).read_bytes()) for k in text},
        'numerical_DLL_changes':False, 'removed_transfer_checks':False,
        'new_GPU_forwards':0,'native_bridge':'REQUIRED','extra_sync':mode==2,
        'active_frontend':active}
    (out/'STAGE.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','pins','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--mode',type=int,choices=(0,1,2),required=True)
    p.add_argument('--active',choices=('both','target','native'),default='both')
    a=p.parse_args();print(json.dumps(stage(a.source,a.pins,a.out,a.mode,a.active),indent=2))
