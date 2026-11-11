from pathlib import Path
import json,shutil
p=Path(__file__).parent;r=Path(str(p)+"-r2");r.mkdir(exist_ok=False)
for name in ["prepare.py","setup.py","CMakeLists.txt","INPUT_PANEL.json","MODEL_IDENTITY.json","recheck.py","freeze.py","SOURCE_AUDIT.md","main.cpp.inc","host-prefix.patch"]:
    shutil.copy2(p/name,r/name)
s=(p/"prefill_submit.cpp").read_text()
s=s.replace('int prefill_q_max=0,prefill_q_nodes=0;', 'int prefill_q_max=0,prefill_q_nodes=0;std::map<std::string,json>prefill_shapes;')
s=s.replace('if(o.phase=="PREFILL"&&std::string(t->name).rfind("Qcur-",0)==0){o.prefill_q_max=std::max(o.prefill_q_max,int(t->ne[2]));o.prefill_q_nodes++;}',
'''if(o.phase=="PREFILL"){
   std::string name=t->name;
   if(name.rfind("Qcur",0)==0||name.rfind("kq-",0)==0){auto j=tensor(t);j["op"]=ggml_op_name(t->op);o.prefill_shapes[j.dump()]=j;}
   if(name.rfind("kq-",0)==0&&t->op==GGML_OP_MUL_MAT){o.prefill_q_max=std::max(o.prefill_q_max,int(t->ne[1]));o.prefill_q_nodes++;}
  }''')
s=s.replace('if(capture&&draft)need(draft->obs.prefill_q_max==1&&draft->obs.prefill_q_nodes>0,"draft prefill physical q admission");',
'''if(capture&&draft){json shapes=json::array();for(auto&kv:draft->obs.prefill_shapes)shapes.push_back(kv.second);
 dump(dir/"draft-prefill-shapes.json",{{"q_max",draft->obs.prefill_q_max},{"observations",draft->obs.prefill_q_nodes},{"shapes",shapes}});
 need(draft->obs.prefill_q_max==1&&draft->obs.prefill_q_nodes>0,"draft prefill physical q admission");}''')
(r/"prefill_submit.cpp").write_text(s)
old=json.loads((p/"BUDGET_LEDGER.json").read_text())
remaining=1800-old["new_charged_seconds"]
pr=json.loads((p/"PREREGISTRATION.json").read_text())
pr["attempt"]=2
pr["previous_attempt"]={"root":str(p),"commit":"d1e52cf07cddd31e5f06e5d09f77c63ee63988be","status":"STOPPED_FIRST_FAILURE","charged_seconds":old["new_charged_seconds"],"qualification_not_transferred":True}
pr["repair"]="Observer-only: read query axis1 of consumed kq MUL_MAT tensor; persist Qcur/kq shapes before assertion. Original Qcur axis2 gate failed without diagnostics;97 prior vectors matched in postfailure diagnostic, not qualification. Numerical candidate unchanged."
pr["qualification"]["geometry"]="Draft PREFILL kq MUL_MAT observed query axis1 must remain1, with persisted shape metadata. No readback; observer absent from timing."
pr["execution"].update(new_cap_seconds=remaining,old_cumulative_seconds=old["all_history_cumulative_seconds"],original_study_cap_seconds=1800)
(r/"PREREGISTRATION.json").write_text(json.dumps(pr,indent=2))
s=(p/"RUN.ps1").read_text().replace(p.as_posix(),r.as_posix())
s=s.replace("C:/hs/b570-draft-cpu-20261020/BUDGET_LEDGER.json",str(p/"BUDGET_LEDGER.json"))
s=s.replace("3133.8366524000003",repr(old["all_history_cumulative_seconds"]))
s=s.replace("1800",repr(remaining))
(r/"RUN.ps1").write_text(s)
(r/"OBSERVER_REPAIR.md").write_text("# Prospective observer repair\n\n"+pr["repair"]+"\n\nAttempt1 is retained unchanged. The new attempt uses only the remaining "+str(remaining)+" seconds of the original1800-second envelope. No timing/reference PASS is transferred. All four original inputs must qualify afresh.\n")
shutil.copy2(Path(__file__),r/"prepare_retry.py")
print(r,remaining)
