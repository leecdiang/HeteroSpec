from pathlib import Path
import json,difflib,shutil
r=Path(__file__).parent;s=Path("C:/hs/b570-direct-id-v1-src")
orig=(s/"src/llama-graph.cpp").read_text(encoding="utf-8")
out='#include "query_head.h"\n'+orig
anchor="    const bool use_flash_attn = cparams.flash_attn && kq_b == nullptr;"
hook='''    // Private request bridge: immutable layout per fresh context, single-threaded host.
    const char * hs_layout = getenv("HS_REQUEST_LAYOUT");
    if (hs_layout && q->ne[0] == 128 && q->ne[2] == 32 && k->ne[2] == 8 &&
        (q->ne[1] == 2 || q->ne[1] == 4) && (k->ne[1] == 256 || k->ne[1] == 512) &&
        q->ne[3] == 1 && k->ne[3] == 1 && v->ne[3] == 1 &&
        !cparams.flash_attn && !kq_b && !sinks && !v_mla && v_trans &&
        !hparams.attn_soft_cap && hparams.f_max_alibi_bias == 0 && cparams.offload_kqv) {
        const bool qb = strcmp(hs_layout, "QB") == 0;
        GGML_ASSERT(qb || strcmp(hs_layout, "PQ") == 0);
        auto b = hs_qh::build(ctx0, qb ? hs_qh::Mode::QB4 : hs_qh::Mode::PQ,
                              q, k, v, kq_mask, kq_scale);
        GGML_ASSERT(!b.common_original && !b.copied_kv);
        for (auto * t : b.scores) cb(t, qb ? "hs_qb_qk" : "hs_pq_qk", il);
        for (auto * t : b.probs) cb(t, qb ? "hs_qb_prob" : "hs_pq_prob", il);
        for (auto * t : b.values) cb(t, qb ? "hs_qb_av" : "hs_pq_av", il);
        cb(b.out, qb ? "hs_qb_final" : "hs_pq_final", il);
        ggml_build_forward_expand(gf, b.out);
        return b.out;
    }

'''
assert out.count(anchor)==1;out=out.replace(anchor,hook+anchor)
(r/"llama-graph.cpp").write_text(out,encoding="utf-8",newline="\n")
(r/"runtime-integration.patch").write_text("".join(difflib.unified_diff(orig.splitlines(True),out.splitlines(True),fromfile="a/src/llama-graph.cpp",tofile="b/src/llama-graph.cpp")),encoding="utf-8",newline="\n")
shutil.copy2("C:/hs/b570-model-profile-final-20261020164000/INPUT.json",r/"INPUT.json")
(r/"CMakeLists.txt").write_text('''cmake_minimum_required(VERSION 3.20)
project(b570_request_bridge LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(SRC "C:/hs/b570-direct-id-v1-src")
set(OLD "C:/hs/b570-direct-id-v1-build")
set(QH "C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/native")
file(GLOB_RECURSE OBJS "${OLD}/src/llama.dir/Release/*.obj")
list(FILTER OBJS EXCLUDE REGEX "/llama-graph[.]obj$")
list(LENGTH OBJS COUNT)
if(NOT COUNT EQUAL 184)
 message(FATAL_ERROR "Unexpected frozen llama object count")
endif()
add_library(llama SHARED llama-graph.cpp ${OBJS})
target_include_directories(llama PRIVATE "${SRC}/src" "${SRC}/include" "${SRC}/ggml/include" "${OLD}/src" "${QH}")
target_compile_definitions(llama PRIVATE LLAMA_BUILD LLAMA_SHARED _CRT_SECURE_NO_WARNINGS GGML_USE_CPU GGML_USE_VULKAN GGML_SHARED GGML_BACKEND_SHARED)
target_compile_options(llama PRIVATE /O2 /Ob2 /utf-8)
target_link_libraries(llama PRIVATE "${OLD}/ggml/src/Release/ggml.lib" "${OLD}/ggml/src/Release/ggml-cpu.lib" "${OLD}/ggml/src/ggml-vulkan/Release/ggml-vulkan.lib" "${OLD}/ggml/src/Release/ggml-base.lib")
add_executable(spec_bridge spec_bridge.cpp)
target_include_directories(spec_bridge PRIVATE "${SRC}/include" "${SRC}/ggml/include" "C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1/_host/pr97/dependencies/pinned-source/vendor")
target_compile_options(spec_bridge PRIVATE /O2 /W4 /fp:precise /utf-8)
target_link_libraries(spec_bridge PRIVATE llama "${OLD}/ggml/src/Release/ggml.lib" "${OLD}/ggml/src/Release/ggml-base.lib")
''')
print("Private runtime integration prepared; no native execution")
