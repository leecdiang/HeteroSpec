import copy,json,shutil,time,uuid
from pathlib import Path
V=Path('D:/hs123/benchmarks/rtx_dispatch_intervention_v1');P=Path('D:/hs122/benchmarks/rtx_mechanism_baselines_v1');old=Path('D:/hs122-5e483f69-dac1-41a4-a046-14401910e6e5')
for n in ['common.py','lifecycle.py','cpu_job.py','graph_base.h','hs113_graph.h','core_gate.h','boundary_cpu.cpp','cupti_observer.h','identity_audit.py']:
    shutil.copyfile(P/n,V/n)
(V/'.gitignore').write_text('__pycache__/\nraw/\nlocal/\nbuild/\nLOCAL_RUN.json\n*.pyc\n')
import sys
sys.path.insert(0,str(V));from common import load,save,sha
r=Path('D:/hs123-'+str(uuid.uuid4()));r.mkdir();save(V/'LOCAL_RUN.json',dict(root=str(r)))
s=load(old/'RUN_SPEC.json');s.update(run_id='rtx-dispatch-intervention-v1',execution_id=r.name,start_epoch=1792328700.0,parent_commit='a1f15bfc8222054aa7b94b40f41af0dd0492ddab',design_commit='30d586fb52351e045b5a0606b597ad08c9389926')
# Task receipt at 21:05 Asia/Shanghai, conservative before first preparation.
save(r/'RUN_SPEC.json',s);save(r/'RUNTIME_MANIFEST.json',s['numerical_DLLs'])
for n,h in s['numerical_DLLs'].items():assert sha(Path(s['runtime_directory'])/n)==h
(V/'build').mkdir()
for n in ['libggml.dll.a','libggml-base.dll.a']:shutil.copyfile(P/'build'/n,V/'build'/n)
c=(P/'collector.cpp').read_text().replace('rtx-mechanism-baselines-v1','rtx-dispatch-intervention-v1')
c=c.replace('const auto context=job.at("context");','const auto context=job.at("context");hs113::require(context.at("logical").get<int>()<=context.at("physical").get<int>()&&context.at("physical").get<int>()>=1,"logical physical domain");')
c=c.replace('std::string layout=job.at("layout"),life=', 'hs113::require(meta["K"]["ne"][1]==context["physical"]&&meta["V"]["ne"][0]==context["physical"]&&meta["mask"]["ne"][0]==context["physical"],"actual physical span metadata");std::string layout=job.at("layout"),life=')
c=c.replace('{"context",context["id"]}', '{"context",context["id"]},{"run_id",spec["run_id"]},{"logical",context["logical"]},{"physical",context["physical"]}')
(V/'collector.cpp').write_text(c)
p=(P/'prepare_rtx.py').read_text();p=p.replace("str(r/'tools/nvidia", "str(Path(s['tool_root'])/'nvidia")
p=p.replace("for layout in LAYOUTS:","for layout in c['layouts']:")
(V/'prepare_rtx.py').write_text(p)
s['tool_root']=str(old/'tools'); # immutable existing tool files are referenced, not duplicated
# spec was already saved; preserve first receipt, write final spec under a new filename then swap before freeze
(r/'RUN_SPEC.json').rename(r/'RUN_SPEC_INITIAL_CPU.json');save(r/'RUN_SPEC.json',s)
print(r)
