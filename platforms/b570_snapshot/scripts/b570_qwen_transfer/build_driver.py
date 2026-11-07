"""Input/recording adapter for the original PR152 boundary driver and libraries."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess
from map_vulkan import replace

HERE=Path(__file__).resolve().parent
KIT=Path('C:/hs/b570-producer-consumer-20261028/source-freeze/benchmarks')
OLD=Path('C:/hs/b570-native-reproduction-20261026')
ROOT=Path('I:/HeteroSpec/b570-qwen-transfer-20261103')

def build(name, candidate, version):
    destination=ROOT/name
    destination.mkdir()
    source=destination/'kit'
    for sub in ('b570_producer_consumer_boundary_v1','b570_native_reproduction_v1'):
        shutil.copytree(KIT/sub/'native',source/sub/'native')
    unit=source/'b570_producer_consumer_boundary_v1'
    p=unit/'native/boundary.cpp'
    s=p.read_text(encoding='utf-8')
    s=replace(s,'#include <bcrypt.h>','#include "transfer_scope.hpp"\n#include <bcrypt.h>')
    shutil.copyfile(HERE/'transfer_scope.hpp',p.parent/'transfer_scope.hpp')
    s=replace(s,'p.cb_eval=BoundaryObs::cb;p.cb_eval_user_data=&obs;', 'if (!policy.clean) { p.cb_eval=BoundaryObs::cb;p.cb_eval_user_data=&obs; }')
    s=replace(s,'int rc=llama_decode(c,b);','''DecodeScope scope(role,phase); capacity_check();
  if(std::getenv("HS_TRANSFER_TRACE")) std::fprintf(stderr,"HS_DECODE role=%s phase=%s pos=%d width=%d\\n",role.c_str(),phase,pos,int(ids.size()));
  const auto phase_start=policy.phase_clocks?Clock::now():Clock::time_point{};
  int rc=llama_decode(c,b);''')
    s=replace(s,'llama_synchronize(c);calls++;','llama_synchronize(c);calls++; if(policy.phase_clocks)phase_seconds[role+"/"+phase]+=seconds(phase_start);')
    s=replace(s,'void trim(int keep){need(llama_memory_seq_rm(llama_get_memory(c),0,keep,-1),"trim");}', '''void trim(int keep){
  const auto start=policy.phase_clocks?Clock::now():Clock::time_point{};
  need(llama_memory_seq_rm(llama_get_memory(c),0,keep,-1),"trim");
  if(policy.phase_clocks)phase_seconds[role+"/KV_TRIM"]+=seconds(start);
 }''')
    s=replace(s,'  caller_trace.push_back(', '  if(!policy.clean) caller_trace.push_back(')
    s=replace(s,' NativeContext target(t,slot.at("target_ub"),heavy,"target");', '''
 policy.producer=slot.at("producer_layout")=="QB"?2:1;
 policy.consumer=layout=="QB"?2:1;
 if(slot.at("route")=="strict_reference")policy.producer=policy.consumer=0;
 policy.precision=slot.value("precision",true);policy.prefix=slot.value("prefix",true);
 policy.clean=slot.value("clean",false);
 policy.phase_clocks=slot.value("phase_clocks",false);phase_seconds.clear();
 _putenv_s("HS_TRANSFER_TRACE",slot.value("trace",false)?"1":"");
 need(!policy.clean || (!heavy && !resume), "clean natural request");
 NativeContext target(t,slot.at("target_ub"),heavy,"target");''')
    s=replace(s,'if(slot.at("route")!="strict_reference")','if(!policy.clean && slot.at("route")!="strict_reference")')
    s=replace(s,'if(!resume&&slot.at("producer")=="P4T")','if(!policy.clean&&!resume&&slot.at("producer")=="P4T")')
    s=replace(s,'if(name.rfind("hs_pq_qk",0)==0)','if(name.rfind(policy.producer==2?"hs_qb_qk":"hs_pq_qk",0)==0)')
    s=replace(s,'&&j["ne"][3]==1,"unexpected producer geometry"', '&&(j["ne"][3]==1||j["ne"][3]==j["caller_width"]),"unexpected producer geometry"')
    s=replace(s,'if(spec&&cycle){int count=0;', 'if(!policy.clean&&spec&&cycle){int count=0;')
    s=replace(s,'need(count>0,"layout bridge not observed");', '''bool split=false;
  for(const auto &item:target.obs.legacy.seen) {
      const std::string name=item.second.at("name");
      split=split || name.rfind("hs_prefix_attention",0)==0;
  }
  need(count>0 || split,"neither layout bridge nor native split observed");''')
    s=replace(s,'  need(gpu,"B570 absent");','  need(gpu,"B570 absent");selected_device=gpu;')
    s=replace(s,'  mp.progress_callback=', '  auto load_begin=Clock::now();mp.progress_callback=')
    s=replace(s,'  const auto*tv=', '''
  result["model_load_seconds"]=seconds(load_begin);capacity_check();
  if(job.value("admit",false)){
    { NativeContext target(t,job.at("slots")[0].at("target_ub"),false,"target");
      NativeContext draft(d,1,false,"draft");capacity_check(); }
    cleanup();result["status"]="ZERO_FORWARD_ADMITTED";result["forward_calls"]=0;
    result["normal_cleanup_returned"]=true;result["min_device_free"]=min_device_free;
    result["min_ram_free"]=min_ram_free;dump(root/"result.json",result);return 0;
  }
  const auto*tv=''')
    s=replace(s,'row.update(run_request(t,d,input,slot,donor));', '''
    auto service=Clock::now();auto result_row=run_request(t,d,input,slot,donor);
    row["service_seconds"]=seconds(service);row.update(result_row);
    row["performance_eligible"]=policy.clean && !policy.phase_clocks && !slot.value("trace",false) && !slot.value("probe",false);
    if(policy.phase_clocks)row["phase_seconds"]=phase_seconds;''')
    s=replace(s,'cleanup();result["status"]="WORKER_COMPLETE";', 'result["min_device_free"]=min_device_free;result["min_ram_free"]=min_ram_free;cleanup();result["status"]="WORKER_COMPLETE";')
    s=replace(s,'json run_request(', (HERE/'probe.inc').read_text(encoding='utf-8')+'\njson run_request(')
    s=replace(s,'  std::map<std::string,json>completed;', '''  if(job.value("probe",false)) {
    result["probe_runs"]=structural_probe(t,panel.at(job.at("slots")[0].at("input_id").get<std::string>()));
    cleanup();result["normal_cleanup_returned"]=true;result["status"]="PROBE_COMPLETE";
    dump(root/"result.json",result);return 0;
  }
  std::map<std::string,json>completed;''')
    p.write_text(s,encoding='utf-8')
    runtime=ROOT/('build-'+version) if candidate else OLD/'build'
    native=ROOT/('source-'+version) if candidate else OLD/'clean-source2/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
    cm=(KIT/'b570_producer_consumer_boundary_v1/CMakeLists.txt').read_text(encoding='utf-8')
    cm+='\ntarget_compile_definitions(boundary PRIVATE LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED'+(' TRANSFER_CANDIDATE' if candidate else '')+')\n'
    (unit/'CMakeLists.txt').write_text(cm,encoding='utf-8')
    b=destination/'build'
    for i,cmd in enumerate((['cmake','-S',str(unit),'-B',str(b),'-G','Visual Studio 17 2022','-A','x64','-DLLAMA_SOURCE='+native.as_posix(),'-DQUALIFIED_BUILD='+runtime.as_posix()],['cmake','--build',str(b),'--config','Release','--parallel','4'])):
        with (destination/f'build-{i}.log').open('x',encoding='utf-8') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
    bins=b/'bin/Release'
    for dll in (runtime/'bin/Release').glob('*.dll'):shutil.copyfile(dll,bins/dll.name)
    files=[{'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(bins.iterdir()) if f.suffix.lower() in ('.dll','.exe')]
    assert len(files)>=6
    (destination/'FILES.json').write_text(json.dumps({'files':files},indent=2))
    if not candidate:
        original=json.loads(Path('C:/hs/b570-producer-consumer-20261028/run-primary/B1-2.launch.json').read_text())['files']
        historical={Path(f['path']).name:f['sha256'] for f in original if f['path'].lower().endswith('.dll')}
        assert all(f['sha256']==historical[Path(f['path']).name] for f in files if f['path'].endswith('.dll'))
    print('DRIVER_BUILT',name,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('--candidate',action='store_true');ap.add_argument('--version',default='00');a=ap.parse_args();build(a.name,a.candidate,a.version)

