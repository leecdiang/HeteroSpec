"""Bounded final R2 accounting/placement/native cache-test integration."""
import json,shutil,subprocess
from s0_budget import ROOT,save
from recover_s0 import sha
def main():
    source=ROOT/'native/source'
    p=ROOT/'hs113_graph.h';s=p.read_text();s=s.replace('auto *a=ggml_mul_mat(ctx,k,qi);','auto *a=ggml_mul_mat(ctx,k,qi);ggml_set_name(a,"hs113_QK");')
    s=s.replace('auto *b=ggml_soft_max_ext(ctx,a,mi,scale,0.0f);','auto *b=ggml_soft_max_ext(ctx,a,mi,scale,0.0f);ggml_set_name(b,"hs113_softmax");')
    s=s.replace('auto *c=ggml_mul_mat(ctx,v,b);','auto *c=ggml_mul_mat(ctx,v,b);ggml_set_name(c,"hs113_AV");')
    s=s.replace('ggml_is_contiguous(q)?q:ggml_cont(ctx,q)','ggml_is_contiguous(q)?q:ggml_set_name(ggml_cont(ctx,q),"hs113_Q_pack")')
    s=s.replace('column=ggml_cont_2d(ctx,column,v->ne[1]*H,l==4?1:width);','column=ggml_set_name(ggml_cont_2d(ctx,column,v->ne[1]*H,l==4?1:width),"hs113_output_restore");')
    p.write_text(s);shutil.copy2(p,source/p.name)
    p=ROOT/'native113.cpp';s=p.read_text();s=s.replace('return {{"op",ggml_op_name(t->op)},','return {{"op",ggml_op_name(t->op)},{"name",std::string(t->name)},')
    s=s.replace('d["placement"]=backend&&t->buffer?', 'd["placement"]=backend&&t->buffer?')
    old='return {{"common_q1_original_arithmetic_chain",result.common},{"nodes",nodes},{"full_support",nullptr},{"actual_placement",nullptr},{"output",descriptor(result.ordinary)}};'
    new='bool full=true;if(backend)for(const auto &n:nodes)if(!n["metadata_only"].get<bool>()&&n["CUDA_support"]!=true)full=false;return {{"common_q1_original_arithmetic_chain",result.common},{"nodes",nodes},{"full_support",backend?J(full):J(nullptr)},{"actual_placement",nullptr},{"output",descriptor(result.ordinary)}};'
    assert old in s;s=s.replace(old,new)
    s=s.replace('J times=J::array();std::vector<unsigned char>expected;','J times=J::array(),intervals=J::array();std::vector<unsigned char>expected;')
    s=s.replace('if(i>=0)times.push_back(std::chrono::duration<double,std::milli>(end-begin).count());','if(i>=0){times.push_back(std::chrono::duration<double,std::milli>(end-begin).count());intervals.push_back({{"begin_ns",std::chrono::duration_cast<std::chrono::nanoseconds>(begin.time_since_epoch()).count()},{"end_ns",std::chrono::duration_cast<std::chrono::nanoseconds>(end.time_since_epoch()).count()}});}')
    s=s.replace('{"completed_host_wall_ms",times},','{"completed_host_wall_ms",times},{"raw_completed_intervals",intervals},{"pid",GetCurrentProcessId()},')
    s=s.replace('auto path=fs::path(plan.at("runtime_directory").get<std::string>())/"ggml-cuda.dll";','auto runtime=fs::path(plan.at("runtime_directory").get<std::string>());SetDllDirectoryW(runtime.wstring().c_str());auto path=runtime/"ggml-cuda.dll";')
    p.write_text(s);shutil.copy2(p,source/p.name);shutil.copy2(ROOT/'native_cache113.cpp',source/'native_cache113.cpp')
    p=source/'src/llama-context.cpp';s=p.read_text();needle='    // fprintf(stderr, "splits: %d\\n", ggml_backend_sched_get_n_splits(sched));';assert needle in s
    diagnostic='''    if(hsc::is_heavy() && std::getenv("HS113_PLACEMENT_TRACE")) {
        ggml_backend_sched_synchronize(sched.get());
        FILE *f=std::fopen(std::getenv("HS113_PLACEMENT_TRACE"),"ab");if(!f)throw std::runtime_error("placement receipt unavailable");
        if(std::ftell(f)>32*1024*1024){std::fclose(f);throw std::runtime_error("placement trace cap");}
        for(int i=0;i<ggml_graph_n_nodes(gf);i++) {
            auto *t=ggml_graph_node(gf,i);if(std::strncmp(t->name,"hs113_",6)!=0)continue;
            auto *b=ggml_backend_sched_get_tensor_backend(sched.get(),t);
            std::fprintf(f,"{\\"node\\":%d,\\"name\\":\\"%s\\",\\"op\\":\\"%s\\",\\"backend\\":\\"%s\\",\\"buffer\\":\\"%s\\",\\"supported\\":%s,\\"active_target\\":%s}\\n",i,t->name,ggml_op_name(t->op),b?ggml_backend_name(b):"UNKNOWN",t->buffer?ggml_backend_buffer_name(t->buffer):"UNKNOWN",b&&ggml_backend_supports_op(b,t)?"true":"false",hs_scope::active?"true":"false");
        }std::fclose(f);
    }
'''
    p.write_text(s.replace(needle,diagnostic+needle))
    p=source/'CMakeLists.txt'
    with p.open('a') as f:f.write('\nadd_executable(native-cache113 native_cache113.cpp)\ntarget_compile_features(native-cache113 PRIVATE cxx_std_17)\ntarget_include_directories(native-cache113 PRIVATE ${CMAKE_SOURCE_DIR} ${CMAKE_SOURCE_DIR}/src)\ntarget_link_libraries(native-cache113 PRIVATE llama)\n')
    original=json.loads((ROOT/'PARENT_SOURCE_HASHES.json').read_bytes());changed={}
    for name,h in original.items():
        if sha(source/name)!=h:changed[name]=dict(parent=h,current=sha(source/name))
    for name in ('hs113_graph.h','native113.cpp','native_cache113.cpp'):changed[name]=dict(parent=None,current=sha(source/name))
    save(ROOT/'SOURCE_DELTA_FINAL.json',dict(files=changed,changes='only graph glue/immutable layout cache key/CPU parser entry/diagnostic placement and bounded standalone host; original speculative and numerical sources unchanged'))
if __name__=='__main__':main()
