"""Original Smol secondary deployment; immutable builds and reserved native units.

No output-based selection or performance exclusions. R is the unchanged binary;
the six-arm amendment keeps its strong historical whole-prompt draft caller H1.
"""
from smol_state import *
ARMS=['M','H1','C1U1','C4U1','C4U2','C4U4']
EPOCH='campaign02'

def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)

DRAFT=r'''
    for(int at=0;at<n_input;){
        int width;
        if(SMOL_CALLER==512)width=std::min(512,n_input-at);
        else{width=std::min(SMOL_CALLER,n_input-at);if(width==3)width=2;}
        auto b=llama_batch_init(width,0,1);
        for(int j=0;j<width;j++)common_batch_add(b,inp[at+j],at+j,{0},at+j==n_input-1);
        observer.decode(ctx_dft,b,"draft");llama_batch_free(b);at+=width;
    }
'''
SHADOW=r'''
    const char*shadow_path=std::getenv("HS_SMOL_DRAFT_PATH");
    if(!shadow_path)throw std::runtime_error("matched dual residency missing");
    auto shadow_params=params;shadow_params.model.path=shadow_path;
    shadow_params.n_ubatch=1;shadow_params.n_outputs_max=1;shadow_params.n_outputs_max_per_seq=1;
    auto shadow=common_init_from_params(shadow_params);
    if(!shadow->context())throw std::runtime_error("shadow draft context");
    smol_capacity();
'''

def build(arm):
 assert arm in ARMS;d=SROOT/EPOCH/arm;d.mkdir(parents=True)
 for n in ('native.cpp','target.cpp','observer.h','CMakeLists.txt'):shutil.copyfile(SROOT/'producer-observer03'/n,d/n)
 for n in ('smol_capture.hpp','smol_evidence.hpp','smol_bulk.hpp','resource_budget.hpp'):shutil.copyfile(HERE/n,d/n)
 (d/'smol_capacity.hpp').write_text('#pragma once\n#include <windows.h>\nstatic void need(bool x,const char*s){if(!x)throw std::runtime_error(s);}\n#include "resource_budget.hpp"\nstatic void smol_capacity(){MEMORYSTATUSEX r{};r.dwLength=sizeof(r);need(GlobalMemoryStatusEx(&r),"RAM query");need(r.ullAvailPhys>=2ULL*1024*1024*1024,"RAM reserve");need(bounded_vulkan_free()>=128ULL*1024*1024,"GPU reserve");}\n')
 p=d/'observer.h';s=p.read_text();s=replace(s,'#include "smol_evidence.hpp"','#include "smol_evidence.hpp"\n#include "smol_capacity.hpp"')
 s=replace(s,'sampler=clone;return dst;','smol_capacity();sampler=clone;return dst;')
 s=replace(s,'j["committed_states"]=evidence.states;','j["committed_states"]=evidence.states;j["draft_prefill_vectors"]=evidence.draft_vectors;')
 p.write_text(s)
 if arm=='M':
  p=d/'target.cpp';s=p.read_text();s=replace(s,'    const auto * vocab = llama_model_get_vocab(model);',SHADOW+'\n    const auto * vocab = llama_model_get_vocab(model);')
  s=replace(s,'    llama_memory_clear(llama_get_memory(ctx),true);llama_synchronize(ctx);','    llama_memory_clear(llama_get_memory(ctx),true);llama_synchronize(ctx);\n    llama_memory_clear(llama_get_memory(shadow->context()),true);llama_synchronize(shadow->context());')
  s=replace(s,'    for (int i=0;i<params.n_predict;++i) {','    for (int i=0;i<params.n_predict;++i) {\n        if(observer.evidence.heavy)observer.evidence.commit(ctx);')
  s=replace(s,'    if(ctx!=source_target){common_sampler_free(sampler);llama_free(ctx);}','    if(observer.evidence.final_only&&!observer.evidence.heavy)observer.evidence.commit(ctx);\n    if(ctx!=source_target){common_sampler_free(sampler);llama_free(ctx);}')
  s=replace(s,'    observer.finish(generated,eog,input);','    observer.finish(generated,eog,input);\n    const auto service_end=ggml_time_us();')
  s=replace(s,'{"whole_request_ms",(whole_end-whole_start)/1000.0}', '{"whole_request_ms",(whole_end-whole_start)/1000.0},{"service_ms",(service_end-whole_start)/1000.0}')
 else:
  p=d/'native.cpp';s=p.read_text();ub=1 if arm=='H1' else int(arm[3]);caller=512 if arm=='H1' else int(arm[1])
  s=replace(s,'    params.n_ubatch=1;',f'    params.n_ubatch={ub};')
  s=replace(s,'    model_dft = llama_init_dft->model();','    smol_capacity();\n    if(llama_n_ubatch(llama_init_dft->context())!='+str(ub)+')throw std::runtime_error("actual draft UB");\n    model_dft = llama_init_dft->model();')
  s=replace(s,'    observer.decode(ctx_tgt,llama_batch_get_one(inp.data(),n_input),"target");','    for(int at=0;at<n_input;at+=512)observer.decode(ctx_tgt,llama_batch_get_one(inp.data()+at,std::min(512,n_input-at)),"target");')
  s=replace(s,'    observer.decode(ctx_dft,llama_batch_get_one( inp.data(), n_input),"draft");',DRAFT.replace('SMOL_CALLER',str(caller)))
  s=replace(s,'                    continue;\n                } else {\n                    LOG("%s", token_str.c_str());','                    if(has_eos||n_predict>params.n_predict)break;\n                    continue;\n                } else {\n                    LOG("%s", token_str.c_str());')
  s=replace(s,'    observer.finish(hs_direct_ids.ids,hs_direct_ids.eog,inp);','    observer.finish(hs_direct_ids.ids,hs_direct_ids.eog,inp);\n    const auto service_end=ggml_time_us();')
  s=replace(s,'{"whole_request_ms",(whole_end-whole_start)/1000.0}', '{"whole_request_ms",(whole_end-whole_start)/1000.0},{"service_ms",(service_end-whole_start)/1000.0}')
 p.write_text(s)
 cm=d/'CMakeLists.txt';cm.write_text(cm.read_text()+'\nfind_package(Vulkan REQUIRED)\nforeach(t b570-closeout-target b570-closeout-native)\ntarget_compile_definitions(${t} PRIVATE NOMINMAX SMOL_BULK_OBSERVER)\ntarget_include_directories(${t} PRIVATE "${PINNED_SOURCE}/src" "${PINNED_SOURCE}/ggml/src")\ntarget_compile_options(${t} PRIVATE /utf-8)\ntarget_link_libraries(${t} PRIVATE Vulkan::Vulkan)\nendforeach()\n')
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 target='b570-closeout-target' if arm=='M' else 'b570-closeout-native'
 command(['cmake','--build',d/'build','--config','Release','--target',target,'--parallel','4'],d/'compile.log')
 bins=d/'build/Release'
 for p in (SROOT/'original-runtime').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.dll','.exe')]))
 write(d/'SOURCE.json',dict(arm=arm,source_files={p.name:sha(p) for p in d.iterdir() if p.suffix in ('.cpp','.h','.hpp','.txt')},numerical_dlls_changed=False,lifecycle='resident/reset; target prefill UB128; native continuation UB1 created/destroyed inside service; same dual weight residency',caller=512 if arm in ('M','H1') else int(arm[1]),draft_ub=1 if arm in ('M','H1') else int(arm[3]),terminal_accept_stop_repaired=True,unused_intermediate_target_prefill_rows_captured=False))

def execute(name,arm,requests,heavy=False,original=False,forced=False):
 folder=SROOT/EPOCH/'runs'/name;folder.mkdir(parents=True)
 jobs=[]
 for j,r in enumerate(requests):
  jobs.append(dict(request_id=name+'-'+str(j),prompt_ids=r['prompt_ids'],output=str(folder/(str(j)+'.json')),**{k:v for k,v in r.items() if k not in ('prompt_ids','id','root_id','formatted_sha256','source_message_ids')}))
 inp=folder/'REQUESTS.jsonl'
 with inp.open('x') as f:
  for x in jobs:f.write(json.dumps(x)+'\n')
 write(folder/'JOBS.json',jobs)
 env=dict(HS_PREFILL_OUTPUT=jobs[0]['output'],HS_PREFILL_UB='128')
 if not heavy:env['HS_TRACE_OFF']='1'
 if arm=='M':env.update(HS_NO_TRANSFER='1',HS_SMOL_DRAFT_PATH=read(SROOT/'AUTHENTICATION.json')['models'][1]['path'])
 envfile=folder/'ENV.json';write(envfile,env)
 template='old-R-0' if arm=='M' else 'old-N-k1-0'
 argv=list(read(SROOT/'units'/template/'SUPERVISOR.json')['argv'])
 d=SROOT/'original-runtime' if original else SROOT/'forced-reference02' if forced else SROOT/EPOCH/arm
 argv[0]=str(d/('b570-closeout-target.exe' if original else 'build/Release/b570-closeout-target.exe' if arm=='M' else 'build/Release/b570-closeout-native.exe'))
 manifest=SROOT/'original-FILES.json' if original else d/'FILES.json'
 cost=dict(requests=len(jobs),token_rows=sum(len(x['prompt_ids'])+len(x.get('forced_suffix',[])) if forced else (len(x['prompt_ids'])+128 if arm=='M' else 2*len(x['prompt_ids'])+512) for x in jobs),operators=0)
 streamed=any(x.get('heavy_state') or x.get('audit_final') or x.get('state_prefixes') for x in jobs)
 unit,rc=supervised(EPOCH+'-'+name,manifest,argv,cost,stdin_file=inp,environment_file=envfile,progress_limit=180,stream_folder=folder if streamed else None)
 assert rc==0,(name,rc)
 finish_native(name,manifest)
 return jobs

def finish_native(name,manifest):
 unit=SROOT/'units'/(EPOCH+'-'+name);folder=SROOT/EPOCH/'runs'/name
 assert read(unit/'SUPERVISOR.json')['status']=='complete'
 # Extra packaged frontends need not be loaded. Every observed packaged DLL
 # must match, and all six numerical/common libraries must actually be present.
 loaded={Path(x['path']).name.lower():x['sha256'] for x in read(unit/'SUPERVISOR.json')['loaded_module_hashes']}
 expected={Path(x['path']).name.lower():x['sha256'] for x in read(manifest)['files'] if x['path'].lower().endswith('.dll')}
 required={'llama.dll','llama-common.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll'}
 assert required<=loaded.keys() and all(loaded[k]==v for k,v in expected.items() if k in loaded)
 write(folder/'MODULE_AUDIT.json',dict(required=sorted(required),observed_packaged={k:loaded[k] for k in expected if k in loaded},packaged_not_loaded=sorted(set(expected)-set(loaded)),all_observed_match=True))
 for x in read(folder/'JOBS.json'):
  assert Path(x['output']).exists()
  for p in sorted(Path(x['output']+'.states').glob('*.bin')):pack(p)

def development(index,arm):
 panel=read(SROOT/'cohort/PANEL.json');r=read(SROOT/'cohort/INPUTS.json')[panel['development'][index]['id']]
 execute('dev-'+str(index)+'-'+arm+'-heavy',arm,[r,dict(r,heavy_state=True)],heavy=True)
 return execute('dev-'+str(index)+'-'+arm+'-off',arm,[r,dict(r,audit_final=True)])

def prospective():
 write(SROOT/EPOCH/'PROSPECTIVE.json',dict(utc=utc(),arms=ARMS,main_slots=864,measurements=432,warmups=432,development_roots=4,test_roots=12,reason='Retain stronger inherited H1 whole-prompt UB1 in separate Smol family',selection_sha256=sha(SROOT/'cohort/SELECTION_AUDIT.json'),panel_sha256=sha(SROOT/'cohort/PANEL.json'),schedule_sha256=sha(SROOT/'cohort/SCHEDULE.json'),output_screening=False,budgets=LIMITS,original_R_unchanged=True,lifecycle='Each arm/root pair gets one immediate same-arm resident warm request followed by measure; fresh worker/model load outside service, recorded separately. Qualification bridges heavy and clean with this priming history.',service='reset/sync, prefill, sampling/propose/verify/trim, original required state transfer/checks, continuation context destruction, response capture file close',costs='All loads, offline qualification, engineering failures, warmups, measurements and delivery retained separately',scope='Secondary Smol family, not Qwen capacity rescue; no AUTO',per_worker_wall_seconds=900,per_request_watchdog_seconds=180,job_memory_bytes=16*1024**3,disk_reserve_bytes=20*1024**3,device_reserve_bytes=128*1024**2))

if __name__=='__main__':
 if sys.argv[1]=='build':build(sys.argv[2])
 elif sys.argv[1]=='prospective':prospective()
 else:development(int(sys.argv[2]),sys.argv[3])
