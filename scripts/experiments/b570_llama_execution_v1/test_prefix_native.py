"""Compile the actual patched KV method against minimal state fixtures."""
from pathlib import Path
import argparse,subprocess

def test(source,out):
    source=Path(source);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    s=(source/'src/llama-kv-cache.cpp').read_text(encoding='utf-8');start=s.index('std::vector<uint32_t> llama_kv_cache::get_prefix_n_kv(');end=s.index('\nggml_tensor * llama_kv_cache::get_k(',start);method=s[start:end]
    harness=r'''
#include <algorithm>
#include <vector>
#include <cstdint>
#include <cassert>
#define GGML_PAD(x,n) (((x)+(n)-1)/(n)*(n))
struct Cells {uint32_t used=769,max=769,capacity=1024;uint32_t get_used()const{return used;}uint32_t used_max_p1()const{return max;}uint32_t size()const{return capacity;}};
struct slot_info {std::vector<uint32_t> strm{0};uint32_t h=765,count=4,streams=1;bool contiguous=true;bool empty()const{return !count;}uint32_t n_stream()const{return streams;}bool is_contiguous()const{return contiguous;}uint32_t head()const{return h;}uint32_t size()const{return count;}};
struct llama_kv_cache {uint32_t n_swa=0,n_pad=32;std::vector<Cells> v_cells{Cells{}};std::vector<uint32_t>get_prefix_n_kv(const slot_info&)const;};
'''+method+r'''
int main(){llama_kv_cache c;slot_info s;
 assert((c.get_prefix_n_kv(s)==std::vector<uint32_t>{768,768,768,1024}));
 s.h=768;c.v_cells[0].used=c.v_cells[0].max=772;
 assert((c.get_prefix_n_kv(s)==std::vector<uint32_t>{1024,1024,1024,1024}));
 s.h=0;c.v_cells[0].used=c.v_cells[0].max=4;
 assert((c.get_prefix_n_kv(s)==std::vector<uint32_t>{256,256,256,256}));
 c.n_pad=512;assert(c.get_prefix_n_kv(s).front()==512);c.n_pad=32;
 c.n_swa=1;assert(c.get_prefix_n_kv(s).empty());c.n_swa=0;
 s.contiguous=false;assert(c.get_prefix_n_kv(s).empty());s.contiguous=true;
 s.streams=2;assert(c.get_prefix_n_kv(s).empty());s.streams=1;
 c.v_cells[0].used=3;assert(c.get_prefix_n_kv(s).empty());c.v_cells[0].used=4;
 s.h=1;assert(c.get_prefix_n_kv(s).empty());s.h=0;
 s.count=0;assert(c.get_prefix_n_kv(s).empty());
}
'''
    cpp=out/'test.cpp';cpp.write_text(harness,encoding='utf-8');exe=out/'test.exe'
    subprocess.run(['cl','/nologo','/EHsc','/std:c++17','/W4','/WX',str(cpp),'/Fe:'+str(exe)],cwd=out,check=True)
    subprocess.run([str(exe)],check=True);print('ACTUAL_PREFIX_METHOD_NATIVE_GUARDS_PASS')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();test(a.source,a.out)
