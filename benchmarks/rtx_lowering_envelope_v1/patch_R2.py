"""Recorded R2 API/runner integration fixes; same lowering and scientific plan."""
from s0_budget import ROOT,save
from recover_s0 import sha
import json,shutil
def main():
    source=ROOT/'native/source';p=source/'tools/server/server.cpp';s=p.read_text()
    old='std::ifstream file(argv[2]);json batch;file>>batch;json out=json::array();'
    assert s.count(old)==1;s=s.replace(old,'std::ifstream file(argv[2]);std::string encoded((std::istreambuf_iterator<char>(file)),{});json batch=json::parse(encoded);json out=json::array();')
    s=s.replace('#include "server-schema.h"','#include "server-schema.h"\n#include "ggml-backend.h"')
    needle='    std::setlocale(LC_NUMERIC, "C");';assert s.count(needle)==1
    s=s.replace(needle,'    const char *numeric_runtime=std::getenv("HS113_NUMERIC_RUNTIME");\n    if(!numeric_runtime)throw std::runtime_error("fixed HS113 numerical runtime path required");\n    ggml_backend_load_all_from_path(numeric_runtime);\n'+needle);p.write_text(s)
    shutil.copy2(ROOT/'native113.cpp',source/'native113.cpp')
    original=json.loads((ROOT/'PARENT_SOURCE_HASHES.json').read_bytes());changed={}
    for name,h in original.items():
        if sha(source/name)!=h:changed[name]=dict(parent=h,current=sha(source/name))
    for name in ('hs113_graph.h','native113.cpp'):changed[name]=dict(parent=None,current=sha(source/name))
    save(ROOT/'SOURCE_DELTA_R2.json',dict(files=changed,scope='watchdog race/native common_json API/complete CPU storage and guarded standalone runner integration; no CUDA shader/spec transaction edits'))
if __name__=='__main__':main()
