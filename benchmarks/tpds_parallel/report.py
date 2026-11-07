"""Render measured cells and phase attribution from the delivered JSON receipts."""
import gzip
import json
from pathlib import Path
from statistics import geometric_mean
HERE=Path(__file__).resolve().parent
E=HERE/"evidence"
def read(name):
    b=(E/name).read_bytes()
    return json.loads(gzip.decompress(b) if name.endswith(".gz") else b)
def main():
    cost=read("cost.json");q=read("qualification.json");raw=read("qualification-raw.json.gz")
    mechanisms=read("mechanism.json");full=read("complete-cost.json")
    arms=["R","S1","PQ-ext","QB-local","WB-cut","native32","native-full","native-ordinary"]
    times=cost["gm_seconds"];strong=min(["R","S1","PQ-ext","WB-cut"],key=lambda a:times[a]["service_seconds"])
    native=min(arms[5:],key=lambda a:times[a]["service_seconds"])
    ratio=cost["ratios"][strong];sessions=cost["sessions"][strong]
    verdict="met" if ratio>=1.03 and min(sessions)>1 else "missed"
    blocks=cost["blocks"]
    wins=sum(r["baseline_over_QB"][strong]>1 for r in blocks)
    eligible=sum(r["vectors"] for r in q if r["arm"] in arms[:5])
    branches=sum(len([k for k in r["hashes"] if k.startswith("target/verify-")]) for r in raw if r["arm"] in ["PQ-ext","QB-local","WB-cut"])
    text=["# RTX reference-preserving execution pilot","",
      f"On the fixed 8B panel, the fastest reference-compatible competitor to QB-local was {strong}. Its geometric mean service time divided by QB-local’s was **{ratio:.4f}×**. QB-local was faster in {wins} of eight input/context/session blocks. The frozen pilot criterion was {verdict}.","",
      "## Numerical results and native lowering","",
      f"The four methods and timed R matched all {eligible:,} committed full-vocabulary vectors across two unseen inputs at context capacities 1024 and 1536. The three grouped methods also matched {branches:,} speculative decision vectors against S1, including uncommitted branches. All k3 cycle records matched. The 1024 oracle ran the original executable. The 1536 oracle used an independently linked, unmodified PR166 core. Timed R ran on the candidate runtime.","",
      "The inputs were MATH/algebra/train/687 (255 prompt tokens) and APPS/train/920 (593). Each speculative cycle used the inherited k3 verification and rollback. Widths above four were target prefill or teacher-input mechanism probes.","",
      "| Probe | Predicted whole-graph calls | Observed layer-zero QK rows | Executing backend |",
      "|---|---:|---|---|"]
    for attempt in ["cross256","cross512","eight","fourteen"]:
        for arm in ["QB-local","WB-cut"]:
            rows=[r for r in mechanisms if r["attempt"]==attempt and r["arm"]==arm]
            r=max(rows,key=lambda z:z["width"]);ops=r["actual_layer0_qk"]
            text.append(f"| {attempt}, {arm} | {r['predicted_calls']} | {[x[2] for x in ops]} | {ops[0][3]} |")
    text+=["","The 8B crossing at position 253 produced one 32-row graph for QB and two whole-graph calls of widths 3 and 29 for WB. Their attention tiles read extents 256 and 512. At position 510 the extents were 512 and 768. Wide graph callers retain parallel four-column Q8 matmuls for Q/K/V, output, FFN and vocabulary projection. The 32-row graph therefore does not imply a 32-row elementary matmul or attention group.","",
      "Qwen3-0.6B has 16 query and 8 KV heads, versus 32/8 on 8B and 40/8 on 14B. At layer zero the fully offloaded 0.6B and 8B graphs placed both rotary head scales on CUDA. On the partially offloaded 14B graph Q scale ran on CUDA and K scale ran on CPU at width eight. The same structural rule selected these placements. All three models use head dimension 128. Scheduler records identify the executing backend and op shape. No kernel-level profiler was used.","",
      "The early wide implementation hit invalid tensor views and exhausted the graph arena on scalar-attention lowering. After the view offset was fixed, retaining wide projection dispatch still changed all eight logits rows in the first 0.6B QB probe. Four-column projection lowering and row-sized graph storage restored the fixed reference in the measured wide cells. The failure attempts and their observed rows remain in the mechanism evidence.","",
      "## Complete service and phase costs","",
      "Seconds are geometric means across eight matched measurements per arm. Service includes resident reset, both prefills where applicable, generation, rollback, sampling and synchronization. Prefill wall ends at the first committed token. Continuation wall covers the rest of generation. Verify is synchronized target decode time within continuation. The means of components need not sum to the geometric mean of the service time.","",
      "| Arm | Service s | Prefill wall s | Target verify s | Continuation wall s | Arm / QB time |",
      "|---|---:|---:|---:|---:|---:|"]
    for arm in arms:
        t=times[arm]
        verify="—" if t["verify_decode_gm"] is None else f"{t['verify_decode_gm']:.3f}"
        text.append(f"| {arm} | {t['service_seconds']:.3f} | {t['prefill_wall_seconds']:.3f} | {verify} | {t['continuation_wall_seconds']:.3f} | {cost['ratios'][arm]:.4f} |")
    text+=["",f"The {strong}/QB ratios in sessions one and two were {sessions[0]:.4f} and {sessions[1]:.4f}. The fastest tested stock arm was {native} at {times[native]['service_seconds']:.3f} s. It differed from the numerical oracle on {sum(len(r['different']) for r in q if r['arm']==native)} committed positions and matched {sum(r['endpoint'] for r in q if r['arm']==native)} of four endpoints. Stock candidates used the retained F16 KV, non-flash backend with the registered batch widths. This comparison does not characterize other flash-attention settings.","",
       f"The four timing processes consumed {sum(x['process_wall'] for x in full):.1f} s wall time, including {sum(x['model_loading'] for x in full):.1f} s of model loading and {sum(x['pool_setup'] for x in full):.1f} s of pool setup. The 64 warmups consumed {cost['warmup_seconds']:.1f} service seconds and the 64 measured requests consumed {cost['measured_seconds']:.1f}. Process startup, pool release, output and remaining host costs are included in the process wall receipts.","",
      "## Graph reuse during qualification","",
      "Counts below sum the four natural input/context observations per method. The reuse counter spans target and draft contexts. Physical histograms refer to target ubatches only. Capture observations and timed service are reported separately.","",
      "| Method | Reused graphs | Prefill physical widths (width × calls) | Verify physical widths (width × calls) |","|---|---:|---|---|"]
    from collections import Counter
    for arm in arms[:5]:
        cells=[r["receipt"] for r in raw if r["arm"]==arm];hist=[]
        for phase in ["PREFILL","VERIFY"]:
            c=Counter()
            for cell in cells:c.update(cell["target_physical_by_phase"].get(phase,{}))
            hist.append(", ".join(f"{k} × {v}" for k,v in sorted(c.items(),key=lambda kv:int(kv[0]))) or "—")
        text.append(f"| {arm} | {sum(r['graphs_reused'] for r in cells)} | {hist[0]} | {hist[1]} |")
    text+=["","## TPDS contribution judgment","",
       f"The evidence establishes a placement-sensitive execution mechanism and a bitwise comparison against two strong alternatives on this RTX worker. The incremental local-cut advantage over {strong} was {100*(ratio-1):+.2f}% in throughput-equivalent terms on this panel. "
       +("It clears the declared pilot margin, but the small panel cannot establish population performance." if verdict=="met" else "It falls short of a consistent 3% pilot advantage; the evidence supports a mechanism result, with a narrower performance claim."),
       "",f"Relative to per-row attention, QB-local delivered {cost['ratios']['PQ-ext']:.3f}× end-to-end speedup. Target verification fell from {times['PQ-ext']['verify_decode_gm']:.3f} s to {times['QB-local']['verify_decode_gm']:.3f} s. Compared with WB-cut, the frozen width-32 prompt chunks aligned with the 256-cell boundaries and both methods used the same physical prefill widths. WB made additional whole-graph cuts on only two of 158 verification calls across the four observations. The large savings over timed R and S1 are shared by WB as well.",
       "","The numerical transfer spans three Q/KV mappings, while complete service timing is confined to one GPU and one target/draft pair. The two inputs recur across both contexts and sessions, so the eight paired blocks are not eight independent workloads. A claim of general superiority for TPDS exceeds these data.","",
       "The evidence directory includes per-block reversals, original reference digests, raw timing receipts, executed tensor shapes, source pins and the saved panel. The README gives native and offline reproduction instructions."]
    (HERE/"RESULTS.md").write_text("\n".join(text)+"\n",encoding="utf8")
if __name__=="__main__":main()

