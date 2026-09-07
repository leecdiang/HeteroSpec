import csv, json, math, random
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "logs/windows-humaneval-replication-30q-ub1.json"
OUT = ROOT / "reports/5070ti"
FIG = OUT / "figures"
BOOT_SEED, N_BOOT = 20260910, 10000

data = json.loads(SRC.read_text(encoding="utf-8"))
runs = data["runs"]
by_key = {(r["task_id"], r["repetition"], r["condition"]): r for r in runs}
tasks = sorted({r["task_id"] for r in runs}, key=lambda x: int(x.split("/")[1]))

rows, prompt = [], defaultdict(lambda: defaultdict(list))
for task in tasks:
    for rep in (1, 2, 3):
        b = by_key[(task, rep, "baseline")]
        for cond in ("cpu_k2", "rtx_k2"):
            s = by_key[(task, rep, cond)]
            speed = b["metrics"]["decode_ms"] / s["metrics"]["decode_ms"]
            m = s["metrics"]
            row = {
                "task_id": task, "repetition": rep, "condition": cond,
                "baseline_decode_ms": b["metrics"]["decode_ms"],
                "spec_decode_ms": m["decode_ms"], "paired_speedup": speed,
                "exact_match": bool(s["exact_match"]),
                "acceptance_rate": m.get("acceptance_rate"),
                "accepted_tokens": m.get("accepted_tokens"),
                "drafted_tokens": m.get("drafted_tokens"),
                "accepted_per_round": m.get("accepted_per_round"),
                "verification_rounds": m.get("verification_rounds"),
                "baseline_decode_tok_s": b["metrics"]["decode_tok_s"],
                "spec_decode_tok_s": m["decode_tok_s"],
                "baseline_peak_vram_MB": b["telemetry"]["peak_vram_MB"],
                "spec_peak_vram_MB": s["telemetry"]["peak_vram_MB"],
                "spec_process_window_mean_power_W": s["telemetry"]["mean_power_W"],
            }
            rows.append(row); prompt[cond][task].append(row)

def gmean(xs): return math.exp(sum(math.log(x) for x in xs) / len(xs))
def summarize(cond):
    prs = []
    for task in tasks:
        rr = prompt[cond][task]
        prs.append({
            "task_id": task, "speedup": gmean([x["paired_speedup"] for x in rr]),
            "acceptance": sum(x["accepted_tokens"] for x in rr) / sum(x["drafted_tokens"] for x in rr),
            "accepted_per_round": sum(x["accepted_tokens"] for x in rr) / sum(x["verification_rounds"] for x in rr),
        })
    vals = [x["speedup"] for x in prs]
    rng = random.Random(BOOT_SEED)
    boots = [gmean([vals[rng.randrange(len(vals))] for _ in vals]) for _ in range(N_BOOT)]
    boots.sort()
    allr = [x for x in rows if x["condition"] == cond]
    exact = sum(x["exact_match"] for x in allr)
    return prs, {
        "condition": cond, "prompt_n": len(prs), "pair_n": len(allr),
        "geomean_speedup": gmean(vals), "ci95_low": boots[249], "ci95_high": boots[9749],
        "median_prompt_speedup": float(np.median(vals)), "faster_prompts": sum(x > 1 for x in vals),
        "exact_pairs": exact, "exact_rate": exact / len(allr),
        "weighted_acceptance": sum(x["accepted_tokens"] for x in allr) / sum(x["drafted_tokens"] for x in allr),
        "accepted_per_round": sum(x["accepted_tokens"] for x in allr) / sum(x["verification_rounds"] for x in allr),
        "mean_spec_tok_s": float(np.mean([x["spec_decode_tok_s"] for x in allr])),
        "median_spec_tok_s": float(np.median([x["spec_decode_tok_s"] for x in allr])),
        "peak_vram_MB": max(x["spec_peak_vram_MB"] for x in allr),
        "pearson_acceptance_speedup": float(pearsonr([x["acceptance"] for x in prs], vals).statistic),
        "spearman_acceptance_speedup": float(spearmanr([x["acceptance"] for x in prs], vals).statistic),
        "pearson_accepted_per_round_speedup": float(pearsonr([x["accepted_per_round"] for x in prs], vals).statistic),
        "spearman_accepted_per_round_speedup": float(spearmanr([x["accepted_per_round"] for x in prs], vals).statistic),
    }

summaries, prompt_sets = [], {}
for c in ("cpu_k2", "rtx_k2"):
    prompt_sets[c], s = summarize(c); summaries.append(s)

OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
with (OUT / "HUMANEVAL_LLAMA_REPLICATION.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

cross = [{"platform":"MacBook Air M4 24GB","condition":"CPU/GPU unified-memory fixed k=2","status":"valid primary","geomean_speedup":1.387,"ci95_low":1.351,"ci95_high":1.422,"exact_pairs":90,"pair_n":90,"faster_prompts":30,"prompt_n":30,"acceptance_rate":0.901,"accepted_per_round":1.798,"peak_vram_MB":"","note":"Values supplied by frozen M4 result summary; result commit absent from fetched branch."}]
for s in summaries:
    cross.append({"platform":"Windows RTX 5070 Ti Laptop","condition":s["condition"],"status":"serialized exact diagnostic (ubatch=1)","geomean_speedup":s["geomean_speedup"],"ci95_low":s["ci95_low"],"ci95_high":s["ci95_high"],"exact_pairs":s["exact_pairs"],"pair_n":s["pair_n"],"faster_prompts":s["faster_prompts"],"prompt_n":s["prompt_n"],"acceptance_rate":s["weighted_acceptance"],"accepted_per_round":s["accepted_per_round"],"peak_vram_MB":s["peak_vram_MB"],"note":"Default batched CUDA path failed token-exact gate; this exact control serializes verification."})
with (OUT / "HUMANEVAL_CROSS_PLATFORM_COMPARISON.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(cross[0])); w.writeheader(); w.writerows(cross)
(OUT / "windows_humaneval_summary.json").write_text(json.dumps({"source":str(SRC),"bootstrap_seed":BOOT_SEED,"bootstrap_resamples":N_BOOT,"summaries":summaries},indent=2),encoding="utf-8")

labels=["M4\nfixed k=2","Windows CPU→RTX\nubatch=1","Windows RTX→RTX\nubatch=1"]
means=[1.387]+[s["geomean_speedup"] for s in summaries]
lo=[1.351]+[s["ci95_low"] for s in summaries]; hi=[1.422]+[s["ci95_high"] for s in summaries]
fig,ax=plt.subplots(figsize=(8,4.8)); x=np.arange(3)
ax.bar(x,means,color=["#4c78a8","#f58518","#e45756"]); ax.errorbar(x,means,yerr=[np.array(means)-lo,np.array(hi)-means],fmt="none",ecolor="black",capsize=4)
ax.axhline(1,color="black",lw=1,ls="--"); ax.set_ylabel("Paired decode speedup (×)"); ax.set_xticks(x,labels); ax.set_title("HumanEval 30-prompt fixed-k=2 comparison")
fig.tight_layout(); fig.savefig(FIG/"humaneval_30q_speedup.png",dpi=180); fig.savefig(FIG/"humaneval_30q_speedup.pdf"); plt.close(fig)

fig,ax=plt.subplots(figsize=(7,5))
for c,color,label in [("cpu_k2","#f58518","CPU→RTX"),("rtx_k2","#e45756","RTX→RTX")]:
    p=prompt_sets[c]; ax.scatter([z["acceptance"] for z in p],[z["speedup"] for z in p],label=label,alpha=.8,color=color)
ax.axhline(1,color="black",lw=1,ls="--"); ax.set_xlabel("Weighted acceptance rate"); ax.set_ylabel("Prompt geometric-mean speedup (×)"); ax.legend(); ax.set_title("Windows exact serialized diagnostics")
fig.tight_layout(); fig.savefig(FIG/"humaneval_acceptance_speedup.png",dpi=180); fig.savefig(FIG/"humaneval_acceptance_speedup.pdf"); plt.close(fig)
print(json.dumps(summaries, indent=2))
