from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).parent
old=Path("C:/hs/b570-spec-bridge-20261020200000")
repo=Path("C:/Users/DIANG/Documents/ChatGPT/HeteroSpec")
source=repo/"benchmarks/m4_runtime/PROMPT_TOKENS.json"
tasks=json.loads(source.read_text())["tasks"]
ids=["HumanEval/38","HumanEval/65","HumanEval/115","HumanEval/127"]
panel=[]
for name in ids:
    matches=[t for t in tasks if t["task_id"]==name]
    assert len(matches)==1
    t=matches[0]
    panel.append({"id":name,"prompt_ids":t["prompt_token_ids"],"cap":64,"source_record":t,
                  "exposure":"Existing project input; not claimed unseen"})
assert [len(t["prompt_ids"])for t in panel]==[181,109,349,277]
warm=json.loads((old/"INPUT.json").read_text());warm["cap"]=16
(r/"INPUT_PANEL.json").write_text(json.dumps({"inputs":panel,"warmup":warm,
    "source_path":str(source),"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest()},indent=2))
shutil.copy2(old/"MODEL_IDENTITY.json",r/"MODEL_IDENTITY.json")
s=(old/"spec_bridge.cpp").read_text()
s=s[:s.index("int main(int argc,char**argv)")]
s=s.replace('Clock::time_point whole;void cutoff(){need(seconds(whole)<35,"internal deadline");}',
    'Clock::time_point whole;double deadline=230;void cutoff(){need(seconds(whole)<deadline,"internal deadline");}')
s=s.replace('bool capture;int calls=0;','bool capture;int calls=0;std::map<std::string,double> decode_seconds;')
s=s.replace('int rc=llama_decode(c,b);','auto decode_start=Clock::now();int rc=llama_decode(c,b);')
s=s.replace('llama_synchronize(c);calls++;','llama_synchronize(c);decode_seconds[phase]+=seconds(decode_start);calls++;')
s=s.replace('fs::path dir,bool capture){','fs::path dir,bool capture,int cap){')
s=s.replace('o.ids.size()==16','o.ids.size()==size_t(cap)')
s=s.replace('j["ne"][0]==256','(j["ne"][0]==256||j["ne"][0]==512)')
s=s.replace('o.record["target_calls"]=target.calls;', 'o.record["target_decode_seconds"]=target.decode_seconds;o.record["draft_decode_seconds"]=draft?json(draft->decode_seconds):json::object();\n o.record["target_calls"]=target.calls;')
(r/"formal.cpp").write_text(s+(r/"main.cpp.inc").read_text(),encoding="utf-8")
c=(Path("C:/hs/b570-spec-cost-20261020203000/CMakeLists.txt")).read_text().replace("b570_spec_cost","b570_formal").replace("spec_cost","formal")
(r/"CMakeLists.txt").write_text(c)
print("Prepared four fixed existing inputs",[(x["id"],len(x["prompt_ids"]))for x in panel])
