from pathlib import Path
import difflib,shutil
r=Path(__file__).parent;p=Path("C:/hs/b570-formal-request-20261020")
s=(p/"formal.cpp").read_text();s=s[:s.index("void endpoint(")];orig=s
s=s.replace("Clock::time_point whole;", "bool bulk_prefill=false;\nClock::time_point whole;")
s=s.replace('std::string phase="setup";bool bad=false;', 'int prefill_q_max=0,prefill_q_nodes=0;\n std::string phase="setup";bool bad=false;')
s=s.replace('if(o.phase!="VERIFY")return false;', '''if(o.phase=="PREFILL"&&std::string(t->name).rfind("Qcur-",0)==0){o.prefill_q_max=std::max(o.prefill_q_max,int(t->ne[2]));o.prefill_q_nodes++;}
  if(o.phase!="VERIFY")return false;''')
s=s.replace("target.prefill(prompt);if(draft)draft->prefill(prompt);",
'''target.prefill(prompt);if(draft){if(bulk_prefill)draft->decode(prompt,0,false,"PREFILL");else draft->prefill(prompt);}''')
s=s.replace('o.record["target_calls"]=target.calls;', '''if(capture&&draft)need(draft->obs.prefill_q_max==1&&draft->obs.prefill_q_nodes>0,"draft prefill physical q admission");
 o.record["draft_prefill_q_observed"]=draft?draft->obs.prefill_q_max:0;
 o.record["draft_prefill_q_node_observations"]=draft?draft->obs.prefill_q_nodes:0;
 o.record["draft_prefill_api_calls"]=draft?(bulk_prefill?1:int(prompt.size())):0;o.record["draft_microbatch_limit"]=1;o.record["target_calls"]=target.calls;''')
assert s!=orig
main=Path("C:/hs/b570-draft-cpu-20261020/main.cpp.inc").read_text()
main=main.replace('draft_threads=label=="DRAFT1"?1:8;','bulk_prefill=label=="BULK1";').replace("DRAFT1","BULK1")
main=main.replace("draft_cpu OUTPUT","prefill_submit OUTPUT")
main=main.replace('std::vector<std::vector<std::string>>orders={{"R","BASE_A","BULK1","BASE_B"},{"BASE_A","BASE_B","R","BULK1"},{"BASE_B","BULK1","BASE_A","R"},{"BULK1","R","BASE_B","BASE_A"}};',
'''std::vector<std::vector<std::string>>orders={{"BASE_A","BASE_B","BULK1"},{"BASE_B","BULK1","BASE_A"},{"BULK1","BASE_A","BASE_B"}};need(index<3,"timing session");''')
main=main.replace('for(int j=0;j<4;j++){\n    int task=(index+j)%4;', 'for(int j=0;j<2;j++){\n    int task=2*((index+j)%2);')
main=main.replace("orders[(index+task)%4]","orders[index]").replace('deadline=mode=="qual"?170:590','deadline=mode=="qual"?170:290')
(r/"main.cpp.inc").write_text(main)
(r/"prefill_submit.cpp").write_text(s+main)
(r/"host-prefix.patch").write_text("".join(difflib.unified_diff(orig.splitlines(True),s.splitlines(True),fromfile="PR134/request-prefix",tofile="candidate/request-prefix")))
for n in ("INPUT_PANEL.json","MODEL_IDENTITY.json"):shutil.copy2(p/n,r/n)
(r/"CMakeLists.txt").write_text((p/"CMakeLists.txt").read_text().replace("b570_formal","b570_prefill_submit").replace("formal","prefill_submit"))
print("Prepared draft API submission batching with physical ubatch1; no native execution")
