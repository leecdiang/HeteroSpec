"""Reproducible final source derivation after port_worker + add_observations."""
from pathlib import Path
import difflib
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'native/worker.cpp';t=p.read_text(encoding='utf-8')
if '#include "transaction_contract.h"' not in t:
 t='#include "transaction_contract.h"\n'+t
 old='auto commit=[&](int id){if(out.size()>=size_t(cap)||(!flags.empty()&&flags.back()))throw std::runtime_error("Native suffix prevented");out.push_back(id);flags.push_back(llama_vocab_is_eog(v,id));return flags.back()||out.size()==size_t(cap);};'
 assert t.count(old)==1;t=t.replace(old,'auto commit=[&](int id){return b570_commit(out,flags,id,cap,llama_vocab_is_eog(v,id));};').replace('int keep=base+1+n;','int keep=b570_keep(base,n);')
 p.write_text(t,encoding='utf-8',newline='\n')
t=p.read_text(encoding='utf-8')
if 'json initial108=json::array();' not in t:
 t=t.replace('json binding108=json::array();','json initial108=json::array();json binding108=json::array();').replace('binding108=json::array();request_dir108=dir;','initial108=json::array();binding108=json::array();request_dir108=dir;').replace('binding108.push_back({','std::ofstream after_file(request_dir108+"/handoff.after.seqkv.bin",std::ios::binary);after_file.write((const char*)b.data(),b.size());after_file.close();if(!after_file)throw std::runtime_error("After-state persistence");\n   binding108.push_back({').replace('result["binding108"]=binding108;','result["initial108"]=initial108;result["binding108"]=binding108;')
 a='if(!f)throw std::runtime_error("Initial logits persistence");';t=t.replace(a,a+'initial108.push_back({{"role",role},{"bytes",bytes},{"sha256",sha96(l,bytes)},{"path",role+".initial.logits.f32"}});');p.write_text(t,encoding='utf-8',newline='\n')
before=(ROOT/'_host/pr97/native/worker.cpp').read_text(encoding='utf-8');(ROOT/'p0/source-worker.cpp.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),t.splitlines(True),fromfile='PR97/native/worker.cpp',tofile='PR108/native/worker.cpp')),encoding='utf-8')
