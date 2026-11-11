"""Process-fixed role/phase scopes with a graph-reuse topology key."""
import shutil
from base import HERE,PHASE1,save,sha

HEADER='''#pragma once
#include <cstdlib>
#include <cstring>
#include <stdexcept>
namespace hs_scope {
inline thread_local bool active = false;
inline int mask() {
    static const int value = [] {
        const char * p = std::getenv("HS_SCOPE_MASK");
        if (!p) return -1;
        char * end = nullptr;
        long v = std::strtol(p, &end, 10);
        if (!*p || *end || v < 0 || v > 15) throw std::runtime_error("invalid scope mask");
        return int(v);
    }();
    return value;
}
struct guard {
    bool prior;
    guard(const char * role, bool prefill) : prior(active) {
        int m = mask();
        if (m < 0) { active = std::getenv("HS_ATTENTION_QUERY_BATCH") != nullptr; return; }
        int bit;
        if (std::strcmp(role, "target") == 0) bit = prefill ? 1 : 2;
        else if (std::strcmp(role, "draft") == 0) bit = prefill ? 4 : 8;
        else throw std::runtime_error("unsupported scope role");
        active = (m & bit) != 0;
    }
    ~guard() { active = prior; }
};
}
'''

def patch():
    src=HERE/'generated/source';assert not src.exists()
    shutil.copytree(PHASE1/'generated/source',src)
    before={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()}
    def replace(rel,a,b):
        p=src/rel;s=p.read_text(encoding='utf-8');assert s.count(a)==1,(rel,a,s.count(a))
        p.write_text(s.replace(a,b),encoding='utf-8',newline='\n')
    (src/'src/hs_scope.h').write_text(HEADER,encoding='utf-8',newline='\n')
    replace('common/hs_observer.h','#include "llama.h"','#include "llama.h"\n#include "../src/hs_scope.h"')
    replace('common/hs_observer.h','inline int decode(llama_context*c,llama_batch b,const char*role){',
            'inline int decode(llama_context*c,llama_batch b,const char*role){\n    hs_scope::guard scope(role,phase=="prefill");')
    replace('common/hs_observer.h','{{"event","decode"},{"role",role},{"phase",phase}',
            '{{"event","decode"},{"scope_mask",hs_scope::mask()},{"scope_active",hs_scope::active},{"role",role},{"phase",phase}')
    replace('tools/server/server-context.cpp','                        slot.stats.update_prompt_start();',
            '                        hs::phase="prefill";\n                        slot.stats.update_prompt_start();')
    replace('tools/server/server-context.cpp','                hs::emit({{"event","first_pending"},{"pending_id",id},{"logits_index",tok_idx},{"modules",hs::modules()}});',
            '                if(hs::enabled())hs::emit({{"event","first_pending"},{"pending_id",id},{"logits_index",tok_idx},{"modules",hs::modules()}});')
    replace('src/llama-graph.h','    // return true if the "other" params would result in a graph with the same topology as with the current params',
            '    bool hs_query_batch = false;\n\n    // return true if the "other" params would result in a graph with the same topology as with the current params')
    replace('src/llama-graph.h','    bool allow_reuse(const llm_graph_params & other) const {',
            '    bool allow_reuse(const llm_graph_params & other) const {\n        if (hs_query_batch != other.hs_query_batch) return false;')
    replace('src/llama-graph.h','struct llm_graph_context {\n    const llm_arch arch;',
            'struct llm_graph_context {\n    const llm_arch arch;\n    const bool hs_query_batch;')
    replace('src/llama-context.cpp','#include "llama-context.h"','#include "llama-context.h"\n#include "hs_scope.h"')
    replace('src/llama-context.cpp','        /*.res         =*/ res,\n    };',
            '        /*.res         =*/ res,\n        /*.hs_query_batch =*/ hs_scope::active,\n    };')
    replace('src/llama-graph.cpp','    arch             (params.arch),',
            '    arch             (params.arch),\n    hs_query_batch   (params.hs_query_batch),')
    replace('src/llama-graph.cpp','if (std::getenv("HS_ATTENTION_QUERY_BATCH") && q->ne[1] > 1)',
            'if (hs_query_batch && q->ne[1] > 1)')
    changed={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file() and before.get(p.relative_to(src).as_posix())!=sha(p)}
    save(HERE/'generated/PATCH_IDENTITY.json',{'changed_from_phase1':changed,'phase1_source_files_sha256':before})

if __name__=='__main__':patch()
