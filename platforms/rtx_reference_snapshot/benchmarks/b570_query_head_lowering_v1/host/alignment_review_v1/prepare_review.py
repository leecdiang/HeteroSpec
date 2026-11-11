"""Bounded offline preparation. Launches only the metadata executable, never diagnostic."""
import difflib
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import time
import zipfile

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'))
from common import modules, save, sha, load
SOURCE=pathlib.Path('C:/hs/b570-direct-id-v1-src')
OLD=pathlib.Path('C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1')


def new_text(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)


def main():
    before=modules()
    vk=SOURCE/'ggml/src/ggml-vulkan/ggml-vulkan.cpp'
    assert sha(vk)=='04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d'
    original=ROOT/'native/host/vulkan.cpp'
    assert sha(original)=='3dccfa2f6f54673076d0990cfa1c0b032c24bb74e5fb436be66cfee0436605a1'
    generated=HERE/'generated';generated.mkdir(exist_ok=False)
    text=original.read_text(encoding='utf-8')
    start=text.index('static hs_qh::Built common(')
    end=text.index('static json capability(')
    block=text[start:end]
    walk=next(line for line in text.splitlines() if line.startswith('static void walk('))
    changed=block.replace('require(', 'fixture_need(')
    changed=changed.replace('std::vector<ggml_tensor*>nodes;','std::vector<ggml_tensor*>nodes;std::vector<std::pair<ggml_tensor*,size_t>>slabs;')
    changed=changed.replace('if(s=="MQ")', 'if(s=="QB4")return hs_qh::Mode::QB4;if(s=="MQ")')
    changed=changed.replace('static Graph graph(json cell,std::string name)', 'static Graph graph(json cell,std::string name,int q_offset=32,bool relocate_pq_mask=false)')
    changed=changed.replace('8+128*h*q', 'q_offset/4+128*h*q').replace('512*h*q,32)', '512*h*q,q_offset)')
    needle=' x.g=ggml_new_graph(x.c);'
    assert changed.count(needle)==1
    relocation=''' fixture_need(q_offset==0||q_offset==32,"declared Q storage offset");
 if(relocate_pq_mask&&q>1&&name=="PQ")for(int j=0;j<q;++j){
  auto*old=x.built.probs[j]->src[1];auto*slab=ggml_new_tensor_1d(x.c,GGML_TYPE_F32,n);
  auto*mi=ggml_view_4d(x.c,slab,n,1,1,1,old->nb[1],old->nb[2],old->nb[3],0);
  x.slabs.push_back({slab,size_t(j)*x.m->nb[1]});x.built.probs[j]->src[1]=mi;
 }
'''
    changed=changed.replace(needle,relocation+needle)
    header='''#pragma once
#include "query_head.h"
#include "nlohmann/json.hpp"
#include <algorithm>
#include <iostream>
#include <utility>
using json=nlohmann::ordered_json;
static void fixture_need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
'''+walk+'\n'+changed
    new_text(generated/'fixture.hpp',header)
    diagnostic=text[:start]+'#include "fixture.hpp"\n'+text[end:]
    diagnostic=diagnostic.replace(walk+'\n','')
    diagnostic=diagnostic.replace('request["study"]=="b570-query-head-lowering-v1"','request["study"]=="b570-query-head-alignment-diagnostic-v1"')
    bound='require(request["kind"]=="graph"&&(request["q_offset_bytes"]==0||request["q_offset_bytes"]==32),"diagnostic graph only");'
    diagnostic=diagnostic.replace('char exe[MAX_PATH];',bound+'\n  char exe[MAX_PATH];')
    diagnostic=diagnostic.replace('graph(cell,request["mode"])','graph(cell,request["mode"],request["q_offset_bytes"],request["relocate_pq_mask"])')
    diagnostic=diagnostic.replace('physical(8+128*nh*nq)', 'physical(request["q_offset_bytes"].get<int>()/4+128*nh*nq)')
    diagnostic=diagnostic.replace('physical[8+(j*nh+h)*128+d]', 'physical[request["q_offset_bytes"].get<int>()/4+(j*nh+h)*128+d]')
    needle='   fs::path dest=request["output_dir"].get<std::string>();'
    assert diagnostic.count(needle)==1
    diagnostic=diagnostic.replace(needle,'''   for(auto&slab:g.slabs)inputbytes.push_back({slab.first,std::vector<char>(mb.begin()+slab.second,mb.begin()+slab.second+ggml_nbytes(slab.first))});
'''+needle)
    needle='   std::ifstream in(request["input"].get<std::string>(),std::ios::binary);'
    assert diagnostic.count(needle)==1
    physical='''   json physical_layout=json::array();std::vector<ggml_tensor*>all;
   for(auto*t=ggml_get_first_tensor(g.c);t;t=ggml_get_next_tensor(g.c,t))all.push_back(t);
   auto tid=[&](ggml_tensor*t)->int{return t?int(std::find(all.begin(),all.end(),t)-all.begin()):-1;};
   for(auto*t:all){auto z=metadata(t);z["ctx_id"]=tid(t);z["view_root"]=tid(t->view_src);z["bytes"]=ggml_nbytes(t);
    z["buffer_relative_offset"]=(uintptr_t)t->data-(uintptr_t)ggml_backend_buffer_get_base(t->buffer);
    z["buffer_bytes"]=ggml_backend_buffer_get_size(t->buffer);z["buffer_name"]=ggml_backend_buffer_name(t->buffer);
    z["device_matches"]=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer))==dev;physical_layout.push_back(z);
   }
   out<<json({{"event","PHYSICAL_LAYOUT"},{"minStorageBufferOffsetAlignment",ggml_backend_buft_get_alignment(ggml_backend_get_default_buffer_type(backend))},{"tensors",physical_layout}}).dump()<<std::endl;
'''
    diagnostic=diagnostic.replace(needle,physical+needle)
    new_text(generated/'diagnostic.cpp',diagnostic)
    new_text(HERE/'fixture.diff',''.join(difflib.unified_diff(block.splitlines(True),changed.splitlines(True),fromfile='frozen-host-graph',tofile='fixture-only-candidate')))
    new_text(HERE/'diagnostic.diff',''.join(difflib.unified_diff(text.splitlines(True),diagnostic.splitlines(True),fromfile='frozen-vulkan-host',tofile='instrumented-diagnostic-host')))
    spans={
        'ggml/src/ggml-vulkan/ggml-vulkan.cpp':[(2509,2549),(2586,2632),(8280,8306),(9716,9755),(9831,9846),(10155,10178),(10207,10268),(12125,12134),(12277,12284),(13846,13888),(16555,16566),(16700,16713),(18924,19005),(19275,19279)],
        'ggml/src/ggml-alloc.c':[(53,91),(1127,1166),(1170,1206)],
        'ggml/src/ggml-backend.cpp':[(2115,2139)],
        'ggml/src/ggml.c':[(1526,1530),(1773,1793),(4094,4124)],
        'ggml/src/ggml-vulkan/vulkan-shaders/soft_max.comp':[(7,27),(43,60),(88,94)]}
    source=[]
    with zipfile.ZipFile(ROOT/'host/ACTOR_SOURCE_FIXED.zip') as archive:
        names=archive.namelist()
        for path,ranges in spans.items():
            f=SOURCE/path;lines=f.read_text(encoding='utf-8').splitlines()
            matches=[n for n in names if n==path or n.endswith('/'+path)]
            capsule_match=bool(matches) and hashlib.sha256(archive.read(matches[0])).hexdigest()==sha(f)
            source.append(dict(path=path,sha256=sha(f),matches_archived_source_capsule=capsule_match,
                identity_scope='vulkan.cpp and ggml.c also match pre-S1 source binding; other files are recovered adjacent source with independently recorded hashes',
                excerpts=[dict(first=a,last=b,lines=['%d: %s'%(i,lines[i-1]) for i in range(a,b+1)]) for a,b in ranges]))
    save(HERE/'FROZEN_SOURCE_REVIEW.json',dict(reviewed_commit='27cfad39cbffcac413760900c6deedbb93bdfc78',sources=source,
        original_host_sha256=sha(original),source_capsule_sha256=sha(ROOT/'host/ACTOR_SOURCE_FIXED.zip'),device_alignment=None))
    output=ROOT/'host_outputs/alignment_review_v1';output.mkdir(exist_ok=False)
    dep=OLD/'_host/pr97/dependencies'
    cmds=[['C:/Program Files/CMake/bin/cmake.exe','-S',str(HERE),'-B',str(output/'build'),'-G','Visual Studio 17 2022','-A','x64',
           '-DPINNED='+str(dep/'pinned-source'),'-DBASE_LIB='+str(dep/'pinned-build/ggml/src/Release/ggml-base.lib'),'-DGENERATED='+str(generated)],
          ['C:/Program Files/CMake/bin/cmake.exe','--build',str(output/'build'),'--config','Release']]
    logs=[]
    for cmd in cmds:
        start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        logs.append(dict(argv=cmd,returncode=r.returncode,elapsed_s=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr))
        if r.returncode:break
    success=all(x['returncode']==0 for x in logs)
    save(HERE/'OFFLINE_BUILD.json',dict(success=success,logs=logs,diagnostic_launched=False))
    assert success,'offline build failed; retain log'
    runtime=output/'build/Release'
    for name in ('ggml-base.dll','ggml-vulkan.dll'):shutil.copy2(OLD/'_host/build/Release'/name,runtime/name)
    cells=[]
    for i in load(ROOT/'host/S1_INPUTS.json'):cells.append(i['cell'])
    save(output/'CELLS.json',cells)
    cmd=[str(runtime/'alignment-metadata.exe'),str(output/'CELLS.json'),str(output/'METADATA.jsonl')]
    start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    save(HERE/'METADATA_PROCESS.json',dict(argv=cmd,returncode=r.returncode,elapsed_s=time.monotonic()-start,
        stdout=r.stdout,stderr=r.stderr,executable_sha256=sha(runtime/'alignment-metadata.exe'),
        modules_before=before,modules_after=modules(),GPU_launches=0,graph_computes=0))
    assert r.returncode==0
    print(dict(offline_build=True,metadata_returncode=r.returncode,diagnostic_launched=False))


if __name__=='__main__':main()
