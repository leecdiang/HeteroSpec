"""Diagnostic successor capturing nonaliasing real attention operands."""
from pathlib import Path
import argparse,sys,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import write,sha,need

def prepare(repo,out):
    repo=Path(repo);out=Path(out);need(not out.exists(),'fresh diagnostic source');out.mkdir(parents=True)
    base=repo/'scripts/experiments/b570_llama_companion_v1';s=(base/'worker.cpp').read_text(encoding='utf-8')
    anchor='            dump(o.root/"trace"/(std::to_string(o.files-1)+".json"),j);return true;'
    need(s.count(anchor)==1,'observer source anchor')
    replacement=r'''
            // QK and AV are out-of-place MUL_MAT operations. Capture their
            // read-only operands only after proving they do not alias output.
            // Softmax's mask is likewise read-only and disjoint from its output.
            if (o.phase=="VERIFY" && (name=="hs_qb_qk-0" || name=="hs_qb_av-0" || name=="hs_qb_prob-0" || name=="kq-0" || name=="kqv-0" || name=="kq_soft_max-0")) {
                const bool probability=name=="hs_qb_prob-0" || name=="kq_soft_max-0";
                need(t->op==(probability?GGML_OP_SOFT_MAX:GGML_OP_MUL_MAT),"captured attention operation contract");
                const int first=probability?1:0,last=probability?2:2;
                for(int operand=first;operand<last;++operand){
                    auto *v=t->src[operand];need(v&&v->buffer&&t->buffer,"allocated attention operands");
                    const size_t span=ggml_nbytes(v);
                    const auto a=reinterpret_cast<uintptr_t>(v->data),b=reinterpret_cast<uintptr_t>(t->data);
                    const bool separate=v->buffer!=t->buffer || a+span<=b || b+n<=a;
                    need(separate,"attention operand aliases consumer output; invalid capture");
                    need(span<=o.max_bytes-o.total,"operand trace storage reservation");
                    std::vector<uint8_t>raw(span);ggml_backend_tensor_get(v,raw.data(),0,span);o.total+=span;
                    auto folder=o.root/"operands"/std::to_string(o.files-1);
                    std::string key="src"+std::to_string(operand);bytes(folder/(key+".bin"),raw.data(),span);
                    auto meta=shape(v);meta["span_bytes"]=span;meta["read_only_consumer_op"]=ggml_op_name(t->op);
                    meta["consumer_name"]=name;meta["source_output_disjoint"]=separate;
                    meta["caller_base"]=o.base;meta["caller_ids"]=o.input;meta["call"]=o.call;
                    meta["source_is_view"]=v->view_src!=nullptr;meta["view_offset"]=v->view_offs;
                    meta["consumer_output_trace"]=std::to_string(o.files-1)+".json";
                    dump(folder/(key+".json"),meta);
                    j["raw_operands"][key]={{"meta",(folder/(key+".json")).string()},{"payload",(folder/(key+".bin")).string()}};
                }
            }
            dump(o.root/"trace"/(std::to_string(o.files-1)+".json"),j);return true;'''
    (out/'worker.cpp').write_text(s.replace(anchor,replacement),encoding='utf-8')
    for name in ('cycle.hpp','companion_scope.hpp'):shutil.copyfile(base/name,out/name)
    write(out/'SOURCE.json',{'original_worker_sha256':sha(base/'worker.cpp'),'diagnostic_worker_sha256':sha(out/'worker.cpp'),'scope':'Additional raw attention operands only for traced layer0 QB and original scalar probe calls; out-of-place consumer disjointness checked; no numerical source change; own-path/native control still required.'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--out',required=True);a=p.parse_args();prepare(a.repo,a.out)
