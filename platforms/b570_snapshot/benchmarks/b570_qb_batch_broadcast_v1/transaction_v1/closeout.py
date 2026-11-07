"""CPU-only evidence packaging and paper figure; never loads GGML or a device."""
import os
os.environ["OPENBLAS_NUM_THREADS"]="1"
import pathlib,json,hashlib,csv,shutil,zipfile,gzip
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
root=pathlib.Path(__file__).parent
prior=pathlib.Path("C:/hs/b570-qb-aa-balanced-20261020065000")
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):(root/name).write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
manifest=read(root/"BUILD_MANIFEST.json")
for entry in manifest["files"]:
    p=pathlib.Path(entry["path"])
    assert p.stat().st_size==entry["bytes"] and sha(p)==entry["sha256"]
ledger=read(root/"BUDGET_LEDGER.json")
assert ledger["status"]=="THREE_SESSIONS_COMPLETED"
assert abs(sum(x["charged_seconds"] for x in ledger["sessions"])+27.8414773-ledger["cumulative_charged_seconds"])<1e-10
checks=[]
for s in range(3):
    result=read(root/f"session-{s}/result.json")
    assert result["status"]=="EXPLORATORY_ALL_PASS" and result["transaction_qualification"]=="ALL_PASS" and result["normal_cleanup_returned"]
    for row in result["rows"]:
        assert row["support"]=="SUPPORTED" and row["numerical"]=="PASS" and row["transaction_qualification"]=="PASS"
        p=pathlib.Path(f"session-{s}/{row['key']}-q{row['q']}-i{row['input']}-{row['mode']}/gpu_final.f32")
        assert sha(root/p)==sha(prior/p)
        checks.append({"file":str(p),"sha256":sha(root/p),"equal_prior_compact_final":True})
write("REFERENCE_CONTINUITY.json",{"status":"ALL_243_PRIOR_REFERENCE_BYTES_PRESERVED","gpu_execution":False,
 "prior_root":str(prior),"prior_commit":"73d07c328da335cfdfc48ad0719181b69bd2e467","checks":checks})
analysis=read(root/"ANALYSIS.json")
shutil.copyfile(prior/"ANALYSIS.json",root/"RESIDENT_ANALYSIS.json")
rows=[]
for s in range(3):
    for line in (root/f"session-{s}/timing.jsonl").read_text().splitlines():
        r=json.loads(line)
        rows.append({k:r[k] for k in ["session","block","cell","visit","key","q","input"]}|{a:v*1000 for a,v in r["arm_means_ms"].items()})
with (root/"BLOCK_MEANS.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
plt.rcParams.update({"font.size":10,"svg.fonttype":"none"})
fig,axes=plt.subplots(1,2,figsize=(11.5,5.8),sharey=True)
labels=[f"k={n}, q={q}" for n in (1023,1024,1025) for q in (1,2,4)]
for ax,data,title in zip(axes,[read(root/"RESIDENT_ANALYSIS.json"),analysis],["Resident compact Q graph","Common permuted Q transaction"]):
    for y,row in enumerate(data["coordinates"]):
        d=row["qh_minus_qb_mean_us"];lo,hi=row["paired_difference_ci_us"]
        color="#77808a" if row["coordinate"]["q"]==1 else "#146b91"
        ax.errorbar(d,y,xerr=[[d-lo],[hi-d]],fmt="o",capsize=3,color=color)
    ax.axvline(0,color="#444444",lw=.8)
    ax.set_title(title)
    ax.set_xlabel("QH_C − mean(QB_A, QB_B), microseconds")
    ax.grid(axis="x",alpha=.2)
axes[0].set_yticks(range(9),labels);axes[0].invert_yaxis()
fig.suptitle("B570: no coordinate clears the declared A/A practical-effect screen",fontsize=13)
fig.text(.5,.02,"99.5% descriptive paired bootstrap intervals; 3 processes × 3 fixed inputs × 6 blocks per coordinate.\n"
 "Gray: q=1 controls. Different windows/layouts: do not subtract panels to estimate transfer cost.",ha="center",fontsize=9)
fig.tight_layout(rect=(0,.09,1,.94))
fig.savefig(root/"MAPPING_COSTS.svg");fig.savefig(root/"MAPPING_COSTS.png",dpi=160);fig.savefig(root/"MAPPING_COSTS.pdf")
plt.close(fig)
rawfiles=[p for s in range(3) for p in (root/f"session-{s}").rglob("*") if p.is_file()]
summary={
 "status":"SCOPED_TRANSACTION_EXPERIMENT_COMPLETE",
 "support_slots":243,"numerical_slots":243,"transaction_qualification_slots":243,
 "prior_reference_byte_checks":243,"paired_blocks":len(rows),
 "timed_transactions":sum(x["timed_calls"] for x in analysis["audit"]),
 "total_graph_computations":sum(x["native_graph_calls"] for x in analysis["audit"]),
 "q1_calibration_passed":analysis["q1_calibration_passed"],"coordinate_screens":[x["conclusion"] for x in analysis["coordinates"]],
 "core_panel":analysis["core_panel"],"cpu_raw_recheck":{k:v for k,v in read(root/"CPU_RAW_RECHECK.json").items() if k!="sessions"},
 "raw_files":len(rawfiles),"raw_bytes":sum(p.stat().st_size for p in rawfiles),
 "new_charged_seconds":sum(x["charged_seconds"] for x in ledger["sessions"]),
 "cumulative_charged_seconds":ledger["cumulative_charged_seconds"],"remaining_seconds":ledger["remaining_seconds"],
 "frozen_inputs_unchanged":True,"decision":"RETAIN_QB; CLOSE_TESTED_COMPACT_QH_OPTIMIZATION_BRANCH; HARDWARE_SOFTWARE_FIRST_HOLD",
 "not_established":["population equivalence","universal QB optimality","natural request speedup","physical bottleneck","whole B570/CPU8 qualification"],
}
write("RESULT_SUMMARY.json",summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ["core_panel","not_established"]},indent=2))
