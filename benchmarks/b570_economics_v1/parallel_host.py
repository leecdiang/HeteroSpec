"""Reuse PR169's F32/p021 backend, scoped to the reference continuation phase."""
from resident_host import *
PAR=Path('I:/HeteroSpec/b570-parallel-20261103')

def core_parallel():
 bind();d=ROOT/'parallel-core02'
 if (d/'FILES.json').exists():return d
 d.mkdir();source=PAR/'source-00';proof=read(PAR/'SOURCE_BINDING-candidate-D.json')
 for rel,h in proof['compiled_source'].items():assert sha(source/rel)==h,rel
 approved={'companion_scope.hpp','hs_reference_batching.hpp','llama-context.cpp','llama-graph.cpp','llama-graph.h','llama-kv-cache.cpp','llama-kv-cache.h','query_head.h'}
 modified=set()
 for p in (source/'src').rglob('*'):
  if p.is_file():
   q=SOURCE/'src'/p.relative_to(source/'src')
   if not q.exists() or sha(p)!=sha(q):modified.add(str(p.relative_to(source/'src')).replace('\\','/'))
 assert modified==approved,modified
 src=d/'source';shutil.copytree(source/'src',src/'src')
 write(d/'INPUT_SOURCE.json',dict(pr169_receipt_sha256=sha(PAR/'SOURCE_BINDING-candidate-D.json'),files={str(p.relative_to(source/'src')).replace('\\','/'):sha(p) for p in (source/'src').rglob('*') if p.is_file()},modified_from_original=sorted(modified),phase_rule='Original mode0 UB128 producer; scalar-reference-compatible continuation only; no model/input identifiers'))
 pins=d/'CORE_PINS.json';write(pins,dict(files={'src/'+n:sha(source/'src'/n) for n in ('llama-context.h','llama-context.cpp')}))
 core_overlay(source,pins,d/'overlay',(1,2,4,32,128))
 for p in (d/'overlay/src').iterdir():shutil.copyfile(p,src/'src'/p.name)
 # Reuse the exact reviewed diagnostic insertion from the baseline private core.
 baseline=(ROOT/'core01/source/src/llama-context.cpp').read_text()
 start=baseline.index('    if(std::getenv("HS_ECON_MICROTRACE"))')
 trace=baseline[start:baseline.index('    ret = GGML_STATUS_SUCCESS;',start)]
 p=src/'src/llama-context.cpp';s=p.read_text();s='#include "llama-kv-cache.h"\n'+s
 s=once(s,'    if (!graph_reuse_disable && res->can_reuse(gparams)) {','    const bool economics_reused=!graph_reuse_disable && res->can_reuse(gparams);\n    if (economics_reused) {')
 key='    ret = GGML_STATUS_SUCCESS;\n\n    return res;';s=once(s,key,trace+key);p.write_text(s)
 p=src/'src/llama-kv-cache.h';s=p.read_text();s=once(s,'    uint32_t get_n_kv() const;','    uint32_t get_n_kv() const;\n    uint32_t economics_head() const {return sinfos.at(i_cur).head();}');p.write_text(s)
 # SIMPLE realigns the actual occupied whole micrographs inside ONE logical
 # decode. llama's output buffer retains all requested rows across micrographs.
 p=src/'src/llama-kv-cache.cpp';s=p.read_text();s='#include "companion_scope.hpp"\n'+s
 key='            auto ubatch = n_stream == 1 ? balloc.split_simple(n_ubatch) : balloc.split_equal(n_ubatch, true, 0);'
 s=once(s,key,r'''
            uint32_t economics_width=n_ubatch;
            if(hs_b570::mode && std::getenv("HS_ECON_WHOLE")) {
                if(n_stream!=1 || n_swa || balloc.get_n_tokens()>32)throw std::runtime_error("SIMPLE dense append profile");
                const auto &cells=v_cells[0];const auto end=cells.used_max_p1();
                if(cells.get_used()!=end || v_heads[0]>end)throw std::runtime_error("SIMPLE non-dense physical owner");
                const auto &batch=balloc.get_batch();
                for(int i=0;i<batch.n_tokens;++i)
                    if(batch.pos[i]!=llama_pos(end+i) || batch.n_seq_id[i]!=1 || batch.seq_id[i][0]!=0)
                        throw std::runtime_error("SIMPLE non-append logical batch");
                const uint32_t pad=std::max(n_pad,256u);
                economics_width=std::min(n_ubatch,pad-(end+balloc.get_n_used())%pad);
            }
            auto ubatch = n_stream == 1 ? balloc.split_simple(economics_width) : balloc.split_equal(economics_width, true, 0);''')
 p.write_text(s)
 extra=Path('C:/hs/b570-llama-results/scripts/experiments/b570_llama_companion_v1/companion_scope.cpp')
 shutil.copyfile(extra,src/'src/economics_scope.cpp')
 cm=(ROOT/'core01/CMakeLists.txt').read_text();(d/'CMakeLists.txt').write_text(cm)
 write(d/'OUTPUT_SOURCE.json',dict(files={str(p.relative_to(src)).replace('\\','/'):sha(p) for p in src.rglob('*') if p.is_file()},shared_repairs_for_M_SIMPLE_LOCAL=True,backend_reused_from_PR169=True,scope_definition_sha256=sha(extra),output_reserve_increased=False))
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 command(['cmake','--build',d/'build','--config','Release','--parallel','4'],d/'compile.log')
 backend=next(x for x in proof['runtime_files']['files'] if Path(x['path']).name=='ggml-vulkan.dll');assert sha(backend['path'])==backend['sha256']
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in (d/'build/Release').glob('*.dll')],backend=backend))
 return d

def parallel_frontend(arm,mode=0):
 c=core_parallel();d=ROOT/'parallel03'/f'{arm}-mode{mode}'
 if (d/'FILES.json').exists():return d
 base=ROOT/'resident04'/f'{arm}-mode{mode}'
 d.mkdir(parents=True)
 for p in base.iterdir():
  if p.is_file() and p.suffix.lower() in ('.cpp','.h','.hpp','.txt'):shutil.copyfile(p,d/p.name)
 p=d/'economics_phase.hpp';s=p.read_text();s+='''
extern "C" __declspec(dllimport) void hs_b570_set_layout(int);
extern "C" __declspec(dllimport) void hs_b570_set_reference_q8(bool);
extern "C" __declspec(dllimport) void hs_b570_set_prefix_extent(bool);
static void economics_policy(const std::string&role,const std::string&phase){
 const bool active=role=="target"&&phase=="continuation";
 hs_b570_set_layout(active?2:0);hs_b570_set_reference_q8(active);hs_b570_set_prefix_extent(active);
}
'''
 # observer.h needs these declarations before begin/end definitions.
 s=s[s.index('extern "C" __declspec(dllimport) void hs_b570_set_layout'):]
 (d/'economics_policy.hpp').write_text('#pragma once\n#include <string>\n'+s)
 p=d/'observer.h';s=p.read_text();s='#include "economics_policy.hpp"\n'+s
 key='void begin(llama_context * ctx,llama_batch b) {';s=once(s,key,key+'economics_policy(role,phase);')
 key='void end(llama_context * ctx,int code) {';s=once(s,key,key+'economics_policy("target","prefill");');p.write_text(s)
 if arm!='M':
  p=d/'native.cpp';s=p.read_text();s=once(s,'const auto continuation_phase=econ_phase(ctx_tgt,observer,1,pending);','const auto continuation_phase=econ_phase(ctx_tgt,observer,2,pending);');p.write_text(s)
 p=d/'CMakeLists.txt';s=p.read_text();s=once(s,(ROOT/'core01/build/Release/llama.lib').as_posix(),(c/'build/Release/llama.lib').as_posix());p.write_text(s)
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 command(['cmake','--build',d/'build','--config','Release','--target','b570-closeout-'+('target' if arm=='M' else 'native'),'--parallel','4'],d/'compile.log')
 bins=d/'build/Release'
 for x in read(base/'FILES.json')['files']:
  p=Path(x['path'])
  if p.suffix.lower()=='.dll' and p.name.lower() not in ('llama.dll','ggml-vulkan.dll'):shutil.copyfile(p,bins/p.name)
 shutil.copyfile(c/'build/Release/llama.dll',bins/'llama.dll')
 shutil.copyfile(read(c/'FILES.json')['backend']['path'],bins/'ggml-vulkan.dll')
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in bins.iterdir() if p.suffix.lower() in ('.exe','.dll')]))
 write(d/'SOURCE.json',dict(files={p.name:sha(p) for p in d.iterdir() if p.suffix in ('.cpp','.h','.hpp','.txt')},core=str(c),shared_binary_for_SIMPLE_LOCAL=True,target_capacity=128 if arm=='M' else 2,prefill_capacity=128,ordinary_M_actual_caller_rows=1,prefill_policy=0,continuation_policy='PR169 QB F32 activation, physical extent identity',simple='HS_ECON_WHOLE set: realign whole micrographs',local='same binary: local attention grouping, wide compatible projections/FFN'))
 return d

if __name__=='__main__':
 if sys.argv[1]=='core':print(core_parallel(),flush=True)
 else:
  for a in ('M','H1','C4U4'):
   for m in (0,1):print(parallel_frontend(a,m),flush=True)
