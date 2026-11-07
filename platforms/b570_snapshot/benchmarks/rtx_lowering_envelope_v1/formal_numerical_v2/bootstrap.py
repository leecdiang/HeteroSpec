"""Create independent v2 glue from the reviewed GPU14 source; no native execution."""
import json,shutil
from pathlib import Path
V=Path(__file__).resolve().parent;B=V.parent;R=B/'repair_timer_v1'
for name in ('core_gate.h','hs113_graph.h','libggml.dll.a','libggml-base.dll.a','ggml.dll.def','ggml-base.dll.def','pe_review.py'):
    shutil.copyfile(R/name,V/name)
shutil.copyfile(R/'run_cpu.py',V/'cpu_job.py')
text=(R/'native_repair.cpp').read_text(encoding='utf-8')
text=text.replace('f<<j.dump(2)', 'f<<j.dump()')
at='static int gpu_run(const J&job,const fs::path&out){'
text=text.replace(at,'#include "formal_gate.h"\n'+at)
text=text.replace('hs113::require(job.contains("approved_stage_F0"),"separate S1 approval binding missing");','formal113::admit(job,false);hs113::require(job.at("stage")=="NUMERICAL","numeric stage required");')
text=text.replace('hs113::require(job.at("run_id")=="pr113-timer-gpu-regression-v1","new independent regression run only");','')
text=text.replace('hs113::require(kind=="numeric","14-attempt engineering regression only; no timing/trace");','hs113::require(kind=="numeric","formal numerical only; no timing/trace");')
old='hs113::require(b==initial[i],"full input before-start readback differs");std::ofstream f(out/(std::string("input_")+roles[i]+".before.bin"),std::ios::binary);f.write((char*)b.data(),b.size());hs113::require(bool(f),"input pre dump");'
new='formal113::retain(job,out,std::string("input_")+roles[i]+".before",b);hs113::require(b==initial[i],"full input before-start readback differs");'
assert old in text;text=text.replace(old,new)
old='hs113::require(b==initial[i],"full input mutation");std::ofstream f(out/(std::string("input_")+roles[i]+".after.bin"),std::ios::binary);f.write((char*)b.data(),b.size());hs113::require(bool(f),"input post dump");'
new='formal113::retain(job,out,std::string("input_")+roles[i]+".after",b);hs113::require(b==initial[i],"full input mutation");'
assert old in text;text=text.replace(old,new)
old='std::ofstream f(out/(std::string(name)+".bin"),std::ios::binary);f.write((char*)b.data(),b.size());hs113::require(bool(f),"tensor write failed");'
assert old in text;text=text.replace(old,'formal113::retain(job,out,name,b);')
text=text.replace('    if(mode=="--gpu-run")return gpu_run(plan,argv[3]);','    if(mode=="--cpu-wires")return formal113::cpu_wires(plan,argv[3]);\n    if(mode=="--cpu-one-wire"){repair113::no_gpu_modules();formal113::admit(plan,true);repair113::no_gpu_modules();write(argv[3],{{"status","PASS"},{"GPU_queries",0}});return 0;}\n    if(mode=="--gpu-census")return formal113::census(plan,argv[3]);\n    if(mode=="--gpu-run")return gpu_run(plan,argv[3]);')
with (V/'native_formal.cpp').open('x',encoding='utf-8',newline='\n') as out:out.write(text)
print('Independent v2 sources copied and bounded glue delta applied; no process/backend/device started')
