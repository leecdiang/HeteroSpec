"""Finish round-1 bounded diagnostic evidence. CPU-only source transformation."""
from pathlib import Path
import difflib
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'_host/source'
def patch(p,old,new):
 t=p.read_text(encoding='utf-8');
 if new in t:return
 assert t.count(old)==1,(p,old[:80],t.count(old));p.write_text(t.replace(old,new),encoding='utf-8',newline='\n')
patch(SRC/'llama-context.h','std::string b570_geometry_key;','''std::string b570_geometry_key;
    bool b570_order_enabled=false;
    std::vector<uint32_t> b570_order;''')
p=SRC/'llama-context.cpp';t=p.read_text(encoding='utf-8');assert t.count('++b570_micrograph_widths[ubatch.n_tokens];')==1;t=t.replace('++b570_micrograph_widths[ubatch.n_tokens];','''++b570_micrograph_widths[ubatch.n_tokens];
            if(b570_order_enabled)b570_order.push_back(ubatch.n_tokens);''');t+='''
extern "C" __declspec(dllexport) void llama_b570_order_enable(llama_context *ctx,bool enabled){ctx->b570_order_enabled=enabled;ctx->b570_order.clear();}
extern "C" __declspec(dllexport) uint64_t llama_b570_order_count(llama_context *ctx){return ctx->b570_order.size();}
extern "C" __declspec(dllexport) uint32_t llama_b570_order_item(llama_context *ctx,uint64_t i){return ctx->b570_order.at(i);}
''';p.write_text(t,encoding='utf-8',newline='\n')
p=ROOT/'native/worker.cpp'
patch(p,'int consumer108=0,capacity108=4;', '''extern "C" __declspec(dllimport) void llama_b570_order_enable(llama_context *,bool);
extern "C" __declspec(dllimport) uint64_t llama_b570_order_count(llama_context *);
extern "C" __declspec(dllimport) uint32_t llama_b570_order_item(llama_context *,uint64_t);
int consumer108=0,capacity108=4;''')
patch(p,'llama_b570_work_enable(ctx,counted());','llama_b570_work_enable(ctx,counted());llama_b570_order_enable(ctx,capture);')
patch(p,'int rc=llama_decode(ctx,b);','''emit({{"event","FORWARD_START"},{"role",role},{"phase",phase},{"caller_rows",ids.size()},{"pos",pos},{"pid",GetCurrentProcessId()}});
  int rc=llama_decode(ctx,b);
  emit({{"event","FORWARD_RETURN"},{"role",role},{"phase",phase},{"returncode",rc},{"pid",GetCurrentProcessId()}});''')
patch(p,'{"successful_micrographs",llama_b570_work_graphs(ctx)-g0}', '''{"ordered_micrograph_widths",[&](){std::vector<int>v;auto count=llama_b570_order_count(ctx);for(uint64_t i=g0;i<count;++i)v.push_back(llama_b570_order_item(ctx,i));return v;}()},{"successful_micrographs",llama_b570_work_graphs(ctx)-g0}''')
patch(p,'heavy()?json(5):json(nullptr)','json(nullptr)')
for name in ['llama-context.cpp','llama-context.h','llama-graph.cpp']:
 before=(ROOT/'_host/pr97/baseline/native/candidate-src'/name).read_text(encoding='utf-8');after=(SRC/name).read_text(encoding='utf-8');(ROOT/'p0'/('source-'+name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='PR97/'+name,tofile='PR108/'+name)),encoding='utf-8')
before=(ROOT/'_host/pr97/native/worker.cpp').read_text(encoding='utf-8');after=p.read_text(encoding='utf-8');(ROOT/'p0/source-worker.cpp.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='PR97/native/worker.cpp',tofile='PR108/native/worker.cpp')),encoding='utf-8')
p=ROOT/'native/worker.cpp';t=p.read_text(encoding='utf-8').replace('if(false)timer=std::thread','timer=std::thread').replace('sample("HEAVY_PERIODIC")','sample("SAFETY_PERIODIC")').replace('std::chrono::milliseconds(5)','std::chrono::milliseconds(100)').replace('{"requested_period_ms",json(nullptr)}','{"requested_period_ms",100}');p.write_text(t,encoding='utf-8',newline='\n')
print('Bounded observations and source diffs complete; native starts 0')
