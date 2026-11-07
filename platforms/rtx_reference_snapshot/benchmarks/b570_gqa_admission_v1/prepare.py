from pathlib import Path
import difflib, json, hashlib, shutil
root=Path(__file__).parent
parent=Path("C:/hs/b570-model-profile-final-20261020164000")
src=(parent/"ggml-vulkan.cpp").read_text()
old='b->ne[1] == 1 && a->ne[2] == b->ne[2] && ggml_is_contiguous(a);'
new='''b->ne[1] == 1 && a->ne[2] == b->ne[2] && ggml_is_contiguous(a);
                // Experimental Qwen3 32/8 GQA, d=128, capacity=1024 only.
                // K is head-interleaved; V has a capacity-strided row.
                // Both use the existing copy + broadcast matvec path for q>1.
                const bool gqa_k = a->ne[0] == 128 && (a->ne[1] == 256 || a->ne[1] == 512) &&
                    a->nb[0] == 2 && a->nb[1] == 2048 && a->nb[2] == 256 && a->nb[3] == 2097152;
                const bool gqa_v = (a->ne[0] == 256 || a->ne[0] == 512) && a->ne[1] == 128 &&
                    a->nb[0] == 2 && a->nb[1] == 2048 && a->nb[2] == 262144 && a->nb[3] == 2097152;
                const bool qb_gqa_broadcast = op->op == GGML_OP_MUL_MAT &&
                    a->type == GGML_TYPE_F16 && b->type == GGML_TYPE_F32 &&
                    a->ne[2] == 8 && b->ne[2] == 32 && a->ne[3] == 1 &&
                    (b->ne[3] == 2 || b->ne[3] == 4) && b->ne[1] == 1 &&
                    b->nb[0] == 4 && (gqa_k || gqa_v);'''
assert src.count(old)==1
out=src.replace(old,new).replace('&& !qb_batch_broadcast) {','&& !qb_batch_broadcast && !qb_gqa_broadcast) {')
oldnc='''!ggml_is_permuted(src0) && !ggml_is_permuted(src1) &&
               src0->ne[3] <= ctx->device->properties.limits.maxComputeWorkGroupCount[0]'''
assert out.count(oldnc)==1
out=out.replace(oldnc,'''!ggml_is_permuted(src0) && !ggml_is_permuted(src1) &&
               src0->ne[3] == src1->ne[3] && // nc shader has no batch-3 broadcast
               src0->ne[3] <= ctx->device->properties.limits.maxComputeWorkGroupCount[0]''')
(root/"ggml-vulkan.cpp").write_text(out,newline="\n")
(root/"gqa-scoped.patch").write_text("".join(difflib.unified_diff(src.splitlines(True),out.splitlines(True),fromfile="a/ggml/src/ggml-vulkan/ggml-vulkan.cpp",tofile="b/ggml/src/ggml-vulkan/ggml-vulkan.cpp")),newline="\n")
cm=(parent/"CMakeLists.txt").read_text()+'''
add_executable(gqa gqa.cpp)
target_include_directories(gqa PRIVATE "${BASE_SOURCE}/include" "C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1/_host/pr97/dependencies/pinned-source/vendor" "C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/native")
target_link_libraries(gqa PRIVATE "C:/hs/b570-direct-id-v1-build/ggml/src/Release/ggml-base.lib")
target_compile_options(gqa PRIVATE /O2 /W4 /fp:precise)
'''
(root/"CMakeLists.txt").write_text(cm,newline="\n")
print("Prepared scoped candidate; no GPU launched")
