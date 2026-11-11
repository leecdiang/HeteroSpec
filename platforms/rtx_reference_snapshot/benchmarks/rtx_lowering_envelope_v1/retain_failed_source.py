"""Recover initial failed native delta, requiring exact recorded SHA per file."""
import hashlib,json
from pathlib import Path
from s0_budget import ROOT,save
def main():
    expected=json.loads((ROOT/'SOURCE_DELTA.json').read_bytes())['files'];source=ROOT/'native/source';dest=ROOT/'engineering/FAILED_INITIAL_NATIVE_DELTA_UTF8';dest.mkdir(parents=True,exist_ok=False);results=[]
    for name,item in expected.items():
        s=(source/name).read_text(encoding='utf-8')
        if name=='native113.cpp':
            s=s.replace('#include <chrono>\n','').replace('#include <cmath>\n','')
            s=s.replace('if(m.contains("bytes"))hs113::require(integer(m["bytes"],1,64*1024*1024)==(int64_t)total,"view owner span differs");','')
            s=s.replace('{"op",ggml_op_name(t->op)},{"name",std::string(t->name)},','{"op",ggml_op_name(t->op)},')
            begin=s.index('using I=std::array');end=s.index('int main(int argc',begin);s=s[:begin]+s[end:]
            s=s.replace('    if(mode=="--cpu-addresses"){write(argv[3],address_tests(plan));return 0;}\n','').replace('    if(mode=="--gpu-run")return gpu_run(plan,argv[3]);\n','')
            start='bool full=true;if(backend)for(const auto &n:nodes)if(!n["metadata_only"].get<bool>()&&n["CUDA_support"]!=true)full=false;'
            s=s.replace(start,'').replace('{"full_support",backend?J(full):J(nullptr)}','{"full_support",nullptr}')
            s=s.replace('auto runtime=fs::path(plan.at("runtime_directory").get<std::string>());SetDllDirectoryW(runtime.wstring().c_str());auto path=runtime/"ggml-cuda.dll";','auto path=fs::path(plan.at("runtime_directory").get<std::string>())/"ggml-cuda.dll";')
        if name=='hs113_graph.h':
            s=s.replace('ggml_is_contiguous(t)?t:ggml_cont(ctx,t)','ggml_cont(ctx,t)')
            s=s.replace('ggml_is_contiguous(q)?q:ggml_set_name(ggml_cont(ctx,q),"hs113_Q_pack")','ggml_cont(ctx,q)')
            s=s.replace('ggml_is_contiguous(mq)?mq:ggml_cont(ctx,mq)','ggml_cont(ctx,mq)')
            s=s.replace(';ggml_tensor *ordinary=nullptr;',';')
            for text in ('ggml_set_name(a,"hs113_QK");','ggml_set_name(b,"hs113_softmax");','ggml_set_name(c,"hs113_AV");'):s=s.replace(text,'')
            start=s.index('        // Ordinary output follows');end=s.index('        for(int s=0;s<3;s++)',start);s=s[:start]+s[end:]
            old='    ggml_set_name(ordinary,"hs113_ordinary_output");return {{sum[0],sum[1],sum[2]},ordinary,common};'
            new='    auto *out=ggml_permute(ctx,sum[2],0,2,1,3);out=ggml_cont_2d(ctx,out,v->ne[1]*H,width);\n    ggml_set_name(out,"hs113_ordinary_output");return {{sum[0],sum[1],sum[2]},out,common};';s=s.replace(old,new)
        if name=='tools/server/server.cpp':
            s=s.replace('#include "ggml-backend.h"\n','')
            s=s.replace('std::ifstream file(argv[2]);std::string encoded((std::istreambuf_iterator<char>(file)),{});json batch=json::parse(encoded);json out=json::array();','std::ifstream file(argv[2]);json batch;file>>batch;json out=json::array();')
            s=s.replace('    const char *numeric_runtime=std::getenv("HS113_NUMERIC_RUNTIME");\n    if(!numeric_runtime)throw std::runtime_error("fixed HS113 numerical runtime path required");\n    ggml_backend_load_all_from_path(numeric_runtime);\n','')
        if name=='src/llama-context.cpp':
            begin=s.index('    if(hsc::is_heavy() && std::getenv("HS113_PLACEMENT_TRACE"))');end=s.index('    // fprintf(stderr, "splits:',begin);s=s[:begin]+s[end:]
        if name=='CMakeLists.txt':s=s[:s.index('\nadd_executable(native-cache113')]
        candidates=[s.encode(),s.replace('\n','\r\n').encode()];match=next((b for b in candidates if hashlib.sha256(b).hexdigest()==item['current']),None)
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True)
        if match is not None:p.write_bytes(match);results.append(dict(path=name,sha256=item['current'],status='EXACT_RECONSTRUCTED_RECORDED_SHA'))
        else:
            p.with_suffix(p.suffix+'.candidate').write_bytes(candidates[0]);results.append(dict(path=name,expected_sha256=item['current'],status='NOT_EXACTLY_RECONSTRUCTED'))
    save(ROOT/'FAILED_SOURCE_RETENTION.json',dict(files=results,method='reverse retained bounded R2 edits; accept only exact original recorded native delta SHA, never a plausible substitute'))
    print(json.dumps(results))
if __name__=='__main__':main()
