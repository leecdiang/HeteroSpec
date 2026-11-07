from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).parent;parent=Path("C:/hs/b570-gqa-av-preserve-20261020190000")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
    return h.hexdigest()
for f in json.loads((parent/"BUILD_MANIFEST.json").read_text())["files"]:
    assert sha(Path(f["path"]))==f["sha256"],f["path"]
release=r/"build/Release"
shutil.copy2(parent/"build/Release/ggml-vulkan.dll",release/"ggml-vulkan.dll")
for n in ("ggml.dll","ggml-base.dll","ggml-cpu.dll"):
    shutil.copy2(Path("C:/hs/b570-direct-id-v1-build/bin/Release")/n,release/n)
models=Path("C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf")
target=models/"Qwen3-8B-Q8_0.gguf";draft=models/"Qwen3-0.6B-Q8_0.gguf"
ident=[{"path":str(p),"bytes":p.stat().st_size,"sha256":sha(p)} for p in (target,draft)]
assert ident[0]["sha256"]=="408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6"
(r/"MODEL_IDENTITY.json").write_text(json.dumps(ident,indent=2))
reg={"study":"B570_REAL_SPECULATIVE_Q2_BRIDGE","uuid":"697f2bad-6d24-48db-9c9c-bd4d0b0576c1",
 "parent":"PR132@7e98e288b4137c998604a0809c7e956474967de1","prior_cumulative_seconds":249.2473593,
 "remaining_seconds":50.7526407,"cap_seconds":300,"process_count":1,"outer_deadline_seconds":38,"internal_cutoff_seconds":35,
 "admission_margin_seconds":12,"input":"Existing exposed HumanEval/42,124IDs,16token cap",
 "reference":"Existing PR129 first clean q1 complete logits and endpoint, plus full PQ/QB logits and complete native IDs/EOG/length/terminal/stop equality",
 "plan":["q1 R, every full output logits checked against PR129 before draft load",
         "actual draft Qwen3-0.6B, k1 native proposal/verification/accept/correction/bonus/trim; fresh PQ then QB target contexts",
         "all actual verification geometry must be observed; QB q2/H32/8/key256 on B570; all PQ/QB saved logits and cycle traces equal",
         "only after gates pass, one fresh clean QB/PQ pair; full endpoints checked; diagnostic costs only"],
 "runtime":"Private llama-graph integration, immutable layout per fresh context, q1 serial prefill both arms, reused184 other llama objects; PR132 Vulkan DLL",
 "request_boundary":"After fresh context initialization, include target/draft prefill, speculative generation, sampling, reconciliation and final synchronization; exclude model/context setup, included in whole-parent budget",
 "reference_scope":"16token window only, no historical128token qualification; q1 unchanged raw comparison required",
 "stop":"First native, placement, actual shape, byte or endpoint failure stops entire process; no timing, retries or budget reset",
 "non_goals":["actor","RTL","CPU8","new input generalization","speedup claim from one pair"]}
(r/"PREREGISTRATION.json").write_text(json.dumps(reg,indent=2))
run=(parent/"RUN.ps1").read_text()
run=run.replace(parent.as_posix(),r.as_posix())
run=run.replace("C:\\hs\\b570-gqa-admission-20261020184000\\BUDGET_LEDGER.json",(parent/"BUDGET_LEDGER.json").as_posix())
run=run.replace("248.4105591","249.2473593").replace("-lt 35","-lt 50").replace("20s execution","38s execution").replace("deadline_seconds=20","deadline_seconds=38").replace("WaitForExit(20000)","WaitForExit(38000)")
run=run.replace("gqa.exe","spec_bridge.exe")
run=run.replace("$info.ArgumentList.Add((Join-Path $studyRoot 'build/Release/ggml-vulkan.dll'))",
f"""$info.ArgumentList.Add('{target.as_posix()}')
$info.ArgumentList.Add('{draft.as_posix()}')
$info.ArgumentList.Add((Join-Path $studyRoot 'INPUT.json'))""")
(r/"RUN.ps1").write_text(run)
files=[r/n for n in ("spec_bridge.cpp","llama-graph.cpp","runtime-integration.patch","CMakeLists.txt","PREREGISTRATION.json","INPUT.json","MODEL_IDENTITY.json","RUN.ps1")]
files+=list(release.glob("*.dll"))+list(release.glob("*.exe"))
files+=[target,draft]
files+=list(Path("C:/hs/b570-direct-id-v1-build/src/llama.dir/Release").rglob("*.obj"))
files+=[Path("C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/native/query_head.h")]
ref=Path("C:/hs/b570-model-bridge-20261020162500/session-0")
files+=[ref/"result.json"]+list(ref.glob("run-0-step-*.f32"))
manifest={"files":[{"path":str(p),"bytes":p.stat().st_size,"sha256":sha(p)}for p in files]}
(r/"BUILD_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({"frozen":len(files),"models":ident,"prior":reg["prior_cumulative_seconds"]}))
