"""Compile the inherited exact k3 request loop with four physical scheduling policies."""
import json
import shutil
import subprocess
import time
from build import OUT, BASE, HERE

def generate():
    worker=(BASE/"worker.cpp").read_text(encoding="utf8").split("int main(int argc,char**argv)")[0]
    def replace(old,new):
        nonlocal worker
        assert worker.count(old)==1,old
        worker=worker.replace(old,new)
    replace("static int dense_target_layers=24;", "static int context_capacity=1024;\nstatic int dense_target_layers=24;")
    replace("p.n_ctx=1024;", "p.n_ctx=context_capacity;")
    # Reserve using the stock graph, then build the scoped real graph on decode.
    replace("c=llama_init_from_model(m,p);", "hs_scope::active=false;c=llama_init_from_model(m,p);hs_scope::active=scoped;")
    cuts=(HERE/"probe.cpp").read_text(encoding="utf8").split("static std::vector<size_t> cuts",1)[1].split("static void unit",1)[0]
    replace('#include "repair_boundary.hpp"', '#include "repair_boundary.hpp"\n#include "llama-kv-cache.h"\n#include "hs_reference_batching.hpp"\n#define check need\nstatic std::vector<size_t> cuts'+cuts)
    replace('target->decode(prompt,0,false,"PREFILL");', '''
        for (size_t pos=0;pos<prompt.size();) {
            const size_t n=std::min<size_t>(target->ub,prompt.size()-pos);
            for(size_t chunk:cuts(target->c,arm,int(pos),n)){
                target->decode(std::vector<int>(prompt.begin()+pos,prompt.begin()+pos+chunk),int(pos),false,"PREFILL");
                pos+=chunk;
            }
        }''')
    start=worker.index('        target->decode(verify,base,true,"VERIFY");')
    end=worker.index('        int accepted=0;',start)
    worker=worker[:start]+'''        std::vector<int> decisions;
        int offset=0;
        for(size_t n:cuts(target->c,arm,base,verify.size())){
            target->decode(std::vector<int>(verify.begin()+offset,verify.begin()+offset+n),base+offset,true,"VERIFY");
            for(size_t row=0;row<n;row++)decisions.push_back(target->sample(int(row),"verify-"+std::to_string(cycle)+"-"+std::to_string(offset+row)));
            offset+=int(n);
        }
'''+worker[end:]
    # R performs the historical single API call with scalar ubatch for prefill.
    replace('for (size_t pos=0;pos<prompt.size();)', 'if (arm=="R") target->decode(prompt,0,false,"PREFILL");\n        else for (size_t pos=0;pos<prompt.size();)')
    replace("bool done=commit(pending);","bool done=commit(pending);auto first_ready=Clock::now();r[\"prefill_wall_seconds\"]=std::chrono::duration<double>(first_ready-request_start).count();")
    replace('r["ids"]=ids;', 'r["continuation_wall_seconds"]=since(first_ready);r["ids"]=ids;')
    return worker+(HERE/"service_main.inc").read_text(encoding="utf8")

def build_service(oracle=False):
    root=OUT.parent/"oracle01" if oracle else OUT
    root.mkdir(exist_ok=True)
    src=root/"service.cpp";src.write_text(generate(),encoding="utf8")
    ref=BASE if oracle else OUT
    for row in json.loads((BASE/"COMMANDS.json").read_bytes()):
        if row["label"] not in ("worker","link"):continue
        cmd=[s.replace(str(BASE),str(ref)).replace(BASE.as_posix(),ref.as_posix()) for s in row["argv"]]
        cmd=[s.replace(str(ref/"worker.cpp"),str(src)).replace(str(ref/"worker.obj"),str(root/"service.obj"))
             .replace(str(ref/"bin/rtx-scope-transfer.exe"),str((root if oracle else root/"bin")/"service.exe")) for s in cmd]
        if oracle and row["label"]=="worker":cmd.insert(2,"-DTPDS_ORACLE")
        with (root/f'service-{row["label"]}-{time.time_ns()}.log').open("xb") as f:
            subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=600,check=True)
if __name__=="__main__":
    build_service();build_service(True)

