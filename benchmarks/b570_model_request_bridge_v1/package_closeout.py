"""CPU-only report, plot and evidence package. Never invokes native programs."""
from pathlib import Path
import json,hashlib,zipfile,gzip,shutil,difflib,base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
root=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=read(root/"ANALYSIS.json");g=r["observer_gates"][-1];t=r["corrected_profile_tables"][2]
parent=Path("C:/hs/b570-qb-broadcast-20261020061400/ggml-vulkan.cpp")
(root/"concurrent-logger.patch").write_bytes("".join(difflib.unified_diff(parent.read_text().splitlines(True),(root/"ggml-vulkan.cpp").read_text().splitlines(True),fromfile="a/ggml/src/ggml-vulkan/ggml-vulkan.cpp",tofile="b/ggml/src/ggml-vulkan/ggml-vulkan.cpp")).encode())
roots={
 "failed_entry":Path("C:/hs/b570-model-bridge-20261020162000"),
 "bridge":Path("C:/hs/b570-model-bridge-20261020162500"),
 "serial_logger":Path("C:/hs/b570-model-profile-20261020163000"),
 "concurrent_missing_tail":Path("C:/hs/b570-model-concurrent-20261020163500"),
 "tail_fixed":Path("C:/hs/b570-model-tailfix-20261020163300"),
 "active_labels_fixed":root}
brief={k:v for k,v in r.items() if k not in ["raw_byte_checks","corrected_profile_tables","processes","budget_receipts"]}
brief["final_profile_group_fractions"]=t["group_fractions"]
(root/"RESULT_SUMMARY.json").write_text(json.dumps(brief,indent=2)+"\n")
text=f"""# B570 real-request bridge and corrected timestamp observer

The real-request scope check is complete for one exposed HumanEval prompt. The final diagnostic logger retains reference bytes, passes the unchanged coarse observer screen and accounts for the previously omitted final interval. It does not establish whole-workload qualification, a natural-request critical-path fraction or a physical hardware bottleneck.

## Actual changes

1. A small standalone native host loads the existing Qwen3-8B Q8_0 model on B570 and runs the unchanged124-token HumanEval/42 input with ubatch1, F16 KV, FlashAttention off and a16-token greedy cap. The first entry attempt failed because it used a dynamic-plugin ABI against linked backend registration. Removing those calls repaired the entry; that0.1694517-second failure is preserved.
2. The Vulkan concurrent logger now emits a terminal timestamp and graph-end index, closing the final group. Previously its output-projection count was zero; the corrected count is16 per request.
3. Group attribution now skips empty/non-compute nodes using the executor's predicate. This removes inactive n=0 operations from the tail label.

The backend repair changes only performance-logging paths. Shaders, arithmetic, model graph and sampling are unchanged. See `concurrent-logger.patch`. The final DLL SHA256 is `618f2f222791480b0536236ff84e6375dd2becface2c59e8adde9fe0d61a0685`. It retains PR128's scoped QB admission repair. The executable is unchanged across successful attempts; the initial host loader repair preceded them.

## Qualification and actual geometry

Across11 successful native processes,33 requests and528 full logit arrays, CPU re-reading verifies all151,936 logits per array byte-for-byte against the first new clean reference, plus greedy ID identity. This is one prompt repeated under observer/runtime controls, not33 independent workload samples. One failed entry process remains in the ledger. All successful processes exit normally with complete capture; no deadline kill is requested.

The observed model has36 layers,32 Q heads and8 KV heads, d128. Its attention physical key extent is256, q1; context capacity1024 is not the executed key extent. The KQ/KQV metadata and runtime logs identify B570 placement. The model log reports37/37 layers offloaded, while CPU-mapped storage also exists.

Thus the earlier Hq=Hkv=8, key1023–1025 micrograph cannot directly establish request benefit. This request does not exercise a q2/q4 mapping. No model optimization is enabled or claimed.

## Observer calibration and integrity

The fixed screen compares third-context medians of15 dependent decode-completion times. Clean A/B and profile versus each clean must all fall within[0.90,1.10]. This is an exploratory necessary check, not statistical equivalence or per-op calibration. Clean/profile/clean processes use the same DLL within each final comparison.

| Observer | Profile overhead vs clean A / B | Coarse gate | Integrity |
|---|---:|---|---|
| Per-operation serial logger | +12.54% / +12.03% | FAIL | Perturbs execution |
| Original concurrent logger | +5.10% / +5.59% | PASS | Missing terminal group; NOT COMPLETE |
| Terminal-only repair | +7.88% / +7.15% | PASS | Tail labels include inactive nodes |
| Terminal + active-node repair | +{(g['profile_over_a']-1)*100:.2f}% / +{(g['profile_over_b']-1)*100:.2f}% | PASS | Counters and active labels pass |

Final clean/profile/clean medians are{g['clean_a_ms']:.4f}/{g['profile_ms']:.4f}/{g['clean_b_ms']:.4f}ms. These measure observer disturbance, not an algorithm speedup. First-context compilation, full-request raw capture and prefill timing are excluded from this median; their full costs still count toward the execution budget.

Every final profile-context table contains5,004 QK, softmax, AV and CONT operations each:36×(124+15). Each contains16 positive-width output projections, with no n=0 matrix labels. Mixed groups are not divided among their members.

## Scoped device-cost result

The final third-context device timestamp subtotal is{t['total_us']/1e6:.6f}s over prefill plus continuation.

| Classification | Instrumented GPU subtotal |
|---|---:|
| Pure QK/softmax/AV core | {t['group_fractions']['attention_core_pure']*100:.4f}% |
| Mixed group containing QK | {t['group_fractions']['attention_core_mixed']*100:.4f}% |
| Final recombination CONT | {t['group_fractions']['recombine_cont']*100:.4f}% |
| Quantized matvec groups, including fused additions | {t['group_fractions']['quantized_matvec_groups']*100:.4f}% |
| Other groups | {t['group_fractions']['other']*100:.4f}% |

The core's conservative mixed-group bound is[{t['core_fraction_bounds'][0]*100:.4f}%,{t['core_fraction_bounds'][1]*100:.4f}%]. This excludes Q/K/V and output projections, RoPE and cache updates; it is not “all attention.” Quantized groups include both attention projections and FFN. Operation names do not establish a DRAM-bandwidth or arithmetic bottleneck.

These are synchronized, instrumented GPU subtotals, not clean natural-request critical-path fractions. Even the final observer retains about7% median overhead. Do not use these fractions in an Amdahl formula or claim an end-to-end optimization.

Decision: the present evidence does not justify an attention-mapping accelerator. Retain the fixed reference baseline and close the immediate QB/QH branch. A future physical study should begin with a new hypothesis about the observed projection workload and calibrated physical counters, not reuse these fractions as a hardware model.

## Budget and preservation

Starting cumulative charge was53.7774511s. This follow-up charges{r['new_charge_this_turn_seconds']:.7f}s across all attempts, including the failed entry, model initialization, diagnostics, raw capture and cleanup. Final cumulative charge is **{r['cumulative_seconds']:.7f}/300s**, leaving **{r['remaining_seconds']:.7f}s**. No budget is reset.

All old roots remain intact. `COMPACT_EVIDENCE.zip` includes every stage's frozen design, source host, build/launch logs, process receipts, metadata and budget. `SOURCE_SNAPSHOT.zip` includes the parent and final backend sources. Full raw logits, model weights and DLLs remain local and are listed by hashes; they are not silently replaced by summaries.

`analyze_closeout.py` reruns the full CPU audit with the original local roots. It does not load GGML or a GPU. The compact ZIP supports metadata/counter review; its delivery is not external authentication of locally retained raw logits.

The backend was rebuilt with147 unchanged precompiled shader objects. `BUILD_MANIFEST.json` binds them and the external headers/import libraries; this is not a fresh shader compilation or a self-contained remote build environment.

See `PAPER_ADDENDUM.md` and `OBSERVER_COSTS.svg` for paper integration. The existing manuscript directories were not overwritten. Actor, RTL, CPU8 and merges were not started. Formal PR127/F0 status remains unchanged.
"""
for before,after in [("unchanged124","unchanged 124"),("a16-token","a 16-token"),("that0.1694517","that 0.1694517"),("is16","is 16"),("Across11","Across 11"),(",33",", 33"),("and528","and 528"),("all151,936","all 151,936"),("not33","not 33"),("has36","has 36"),(",32 Q",", 32 Q"),("and8 KV","and 8 KV"),("d128","d=128"),("extent is256","extent is 256"),("capacity1024","capacity 1024"),("reports37/37","reports 37/37"),("of15","of 15"),("within[","within ["),("contains5,004","contains 5,004"),("each:36","each: 36"),("contains16","contains 16"),("was53.7774511","was 53.7774511"),("with147","with 147"),("about7%","about 7%")]:
    text=text.replace(before,after)
(root/"RESULT.md").write_text(text,encoding="utf-8")
# Publication-friendly static figure; explicitly label diagnostic quantities.
plt.rcParams.update({"font.size":10,"svg.fonttype":"none"})
fig,axes=plt.subplots(1,2,figsize=(11.5,4.9),gridspec_kw={"width_ratios":[1.2,1]})
names=["Serial per-op\n(rejected)","Concurrent\n(incomplete)","Tail fixed\n(labels incomplete)","Final concurrent"]
vals=[100*((v["profile_over_a"]+v["profile_over_b"])/2-1) for v in r["observer_gates"]]
axes[0].bar(range(4),vals,color=["#bb4444","#999999","#999999","#237ba1"])
axes[0].axhline(10,color="#bb4444",ls="--",lw=1);axes[0].set_xticks(range(4),names,fontsize=8)
axes[0].set_ylabel("Median decode overhead vs clean controls (%)")
axes[0].set_title("Observer calibration; no algorithm speedup")
for i,v in enumerate(vals):axes[0].text(i,v+.25,f"{v:.2f}%",ha="center",fontsize=9)
fr=t["group_fractions"]
labels=["Quantized matvec\nand fused groups","QK/softmax/AV\nplus mixed bound","Recombine CONT","Other"]
v=[fr["quantized_matvec_groups"],fr["attention_core_pure"]+fr["attention_core_mixed"],fr["recombine_cont"],fr["other"]]
axes[1].barh(range(4),[x*100 for x in v],color=["#237ba1","#58a78a","#adc6c2","#999999"])
axes[1].set_yticks(range(4),labels,fontsize=9);axes[1].invert_yaxis();axes[1].set_xlim(0,105)
for i,x in enumerate(v):axes[1].text(x*100+1,i,f"{x*100:.2f}%",va="center",fontsize=9)
axes[1].set_xlabel("Instrumented GPU subtotal (%)")
axes[1].set_title("One fixed Qwen3-8B request")
fig.text(.5,.02,"One exposed prompt, one device/date. Final observer still adds ~7% overhead.\nGPU subtotals are not request critical-path shares; QKV/O projections are in quantized groups.",ha="center",fontsize=9)
fig.tight_layout(rect=(0,.12,1,1));fig.savefig(root/"OBSERVER_COSTS.svg");fig.savefig(root/"OBSERVER_COSTS.png",dpi=160);fig.savefig(root/"OBSERVER_COSTS.pdf");plt.close(fig)
# Exact compact metadata from every failed and successful stage.
compact=[]
allowed={".json",".log",".ps1",".py",".md",".txt",".patch"}
for label,d in roots.items():
    for p in d.iterdir():
        if p.is_file() and (p.suffix in allowed or p.name=="model_bridge.cpp") and p.name not in {"GIT_PAYLOAD.json","FINAL_MANIFEST.json"}:
            if p.name!="PRE_DELIVERY_MANIFEST.json":compact.append((p,f"{label}/{p.name}"))
    for f in d.glob("session-*"):
        if f.is_dir() and (f/"result.json").exists():compact.append((f/"result.json",f"{label}/{f.name}/result.json"))
with zipfile.ZipFile(root/"COMPACT_EVIDENCE.zip","w",zipfile.ZIP_DEFLATED) as z:
    for p,name in compact:z.write(p,name)
with zipfile.ZipFile(root/"COMPACT_EVIDENCE.zip") as z:
    for p,name in compact:assert z.read(name)==p.read_bytes()
with zipfile.ZipFile(root/"SOURCE_SNAPSHOT.zip","w",zipfile.ZIP_DEFLATED) as z:
    z.write(parent,"parent-pr128/ggml-vulkan.cpp");z.write(root/"ggml-vulkan.cpp","final/ggml-vulkan.cpp")
    z.write(roots["tail_fixed"]/"ggml-vulkan.cpp","terminal-only/ggml-vulkan.cpp")
    z.write(root/"CMakeLists.txt","final/CMakeLists.txt")
manifest=[]
for label,d in roots.items():
    paths=[p for f in d.glob("session-*") if f.is_dir() for p in f.rglob("*") if p.is_file()]
    paths += [p for p in d.iterdir() if p.is_file() and p.name not in {"GIT_PAYLOAD.json","FINAL_MANIFEST.json","FINAL_MANIFEST.json.gz","FINAL_MANIFEST.sha256"}]
    paths += [p for p in (d/"build/Release").iterdir() if p.suffix in {".exe",".dll"}]
    for p in paths:manifest.append({"stage":label,"path":str(p),"bytes":p.stat().st_size,"sha256":sha(p)})
data=(json.dumps({"roots":{k:str(v) for k,v in roots.items()},"files":manifest},indent=2)+"\n").encode()
(root/"FINAL_MANIFEST.json").write_bytes(data)
(root/"FINAL_MANIFEST.json.gz").write_bytes(gzip.compress(data,mtime=0))
(root/"FINAL_MANIFEST.sha256").write_text(hashlib.sha256(data).hexdigest()+"  FINAL_MANIFEST.json\n")
dest=Path("C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/benchmarks/b570_model_request_bridge_v1")
dest.mkdir(exist_ok=True)
names=["model_bridge.cpp","CMakeLists.txt","concurrent-logger.patch","RUN.ps1","INPUT.json","MODEL_IDENTITY.json","PREREGISTRATION.json","BUILD_MANIFEST.json","BUDGET_LEDGER.json","analyze_closeout.py","package_closeout.py","ANALYSIS.json","RESULT_SUMMARY.json","RESULT.md","PAPER_ADDENDUM.md","OBSERVER_COSTS.svg","COMPACT_EVIDENCE.zip","SOURCE_SNAPSHOT.zip","FINAL_MANIFEST.json.gz","FINAL_MANIFEST.sha256"]
payload=[]
for name in names:
    p=root/name;b=p.read_bytes();binary=name.endswith((".zip",".gz"))
    shutil.copyfile(p,dest/name)
    payload.append({"name":name,"path":"benchmarks/b570_model_request_bridge_v1/"+name,"binary":binary,
     "content":base64.b64encode(b).decode() if binary else b.decode("utf-8-sig"),"bytes":len(b),
     "git_blob_sha":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()})
(root/"GIT_PAYLOAD.json").write_text(json.dumps(payload))
print(json.dumps({"files":len(names),"bytes":sum(x["bytes"] for x in payload),"manifest_entries":len(manifest),"manifest_sha256":hashlib.sha256(data).hexdigest(),"compact_archive_files":len(compact)}))
