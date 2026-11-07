from host import *
def preserve():
 s=(HERE/'worker.cpp').read_text(encoding='utf-8')
 old=s.replace('static json seed(llama_model*m,const json&s){\n auto start=clock_t_tp::now();','static json seed(llama_model*m,const json&s){',1)
 old=old.replace('{"prefix_calls",at},{"prefix_construction_seconds",sec(start)}','{"prefix_calls",at}',1)
 for role in ('reference-00','candidate-00'):
  p=ROOT/role/'worker.cpp';p.write_text(old,encoding='utf-8',newline='\n')
  assert sha(p)==read(ROOT/role/'SOURCE.json')['files']['worker.cpp'],role
 write(ROOT/'ENGINEERING_EPOCHS.json',dict(utc=utc(),events=[
  dict(event='initial candidate-00 link failed',log='candidate-00/compile.log',sha256=sha(ROOT/'candidate-00/compile.log'),repair='Explicitly link unchanged ggml-base import library; no numerical source change',success_log='candidate-00/compile-repair01.log',model_requests=0),
  dict(event='historical exposure JSON parser rejected an empty historical placeholder',repair='Preserve placeholder path/hash explicitly; retain inherited complete audit and all other panels',model_requests=0),
  dict(event='reference/candidate-00 admitted C4096',model_requests=0,zero_forward_probes=2),
  dict(event='reference/candidate-01 worker epoch',repair='Add explicit native prefix_construction_seconds; original epoch retained. Same library bytes.',model_requests_before_change=0),
  dict(event='git lazy-fetch auto packing consumed host RAM',repair='Stopped only task-owned git maintenance processes before native launch; subsequent git commands disable automatic maintenance',model_requests=0)
 ],engineering_wall_time='Preparation commands not all instrumented; no invented timing. Native owned lifetimes and every attempted request are separately measured.'))
if __name__=='__main__':preserve()
