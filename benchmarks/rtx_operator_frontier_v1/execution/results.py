"""Offline reconstruction of the operator, coordinate and natural evidence."""
import gzip,json,statistics,math,hashlib,base64
from pathlib import Path
HERE=Path(__file__).resolve().parent
E=HERE/"evidence"
def read(name):
    data=(E/name).read_bytes()
    return json.loads(gzip.decompress(data) if name.endswith(".gz") else data)
def gm(xs):return statistics.geometric_mean(xs)
def audit():
    ops=read("operands.json.gz");assert len(ops)==16
    for op in ops:
        routes={(r["q"],r["route"]):r for r in op["routes"]}
        for (n,path),r in routes.items():
            assert (r["sha"]==routes[n,"scalar"]["sha"])==r["scalar_equal"]
            assert r["scalar_equal"]==(path!="wide" or n<=4)
        assert op["inputs"]["output"]==routes[32,"wide"]["sha"]
    sample=read("operand-sample.json.gz")
    for op in ops:
        name=op["descriptor"]["weight"]["name"]
        if op["model"]=="8B" and name in sample:
            hashes={k:hashlib.sha256(base64.b64decode(v)).hexdigest() for k,v in sample[name].items()}
            routes={(r["q"],r["route"]):r["sha"] for r in op["routes"]}
            assert hashes["input"]==op["inputs"]["input"] and hashes["live32"]==routes[32,"wide"] and hashes["scalar32"]==hashes["packed32"]==routes[32,"scalar"] and hashes["native8"]==routes[8,"wide"]
    matrix=read("matrix-vectors.json.gz");assert len(matrix)==840 and all(r["actual"]==r["oracle"] for r in matrix)
    geom=read("coordinates.json");assert len(geom)==40 and all(r["actual_calls"]==r["predicted_calls"] for r in geom)
    costs=read("append-cost.json.gz");plan=read("matrix-plan.json")["plan"]
    assert len(plan)==len(costs)==120
    for p,c in zip(plan,costs):
        assert all(c[k]==v for k,v in p.items())
        assert all(c[s]["unit"]["mode"]=="cost" and not c[s]["nodes"] and c[s]["calls"]==next(x["actual_calls"] for x in geom if x["cell"]==c["cell"] and x["arm"]==c["arm"]) for s in ("measured","warm"))
    proof=read("natural-qualification.json.gz");cap=read("natural-transactions.json.gz")
    for r in proof:
        i=r["i"];a=r["arm"];folder="reference" if a=="S1" else "historical" if a=="oldQB" else "changed"
        c=cap[f"{folder}/i{i}/{a}/capture"]
        assert c["endpoint"]==cap[f"reference/i{i}/R/capture"]["endpoint"]
        assert c["cycles"]==cap[f"reference/i{i}/S1/capture"]["cycles"]
        assert r["oracle"]==r["vectors"] and r["branch"]==r["scalar_branch"]
    service=read("service-cost.json.gz")
    plan=[r for session in read("natural-freeze.json")["order"] for r in session]
    assert len(plan)==len(service)==36
    for r,p in zip(service,plan):
        assert all(r[k]==v for k,v in p.items())
        for role in ("warm","measured"):
            assert not r[role]["capture"] and r[role]["endpoint"]==cap[f"reference/i{r['index']}/R/capture"]["endpoint"] and r[role]["cycles"]==cap[f"reference/i{r['index']}/S1/capture"]["cycles"]
    return ops,geom,costs,proof,service
def main():
    ops,geo,cost,proof,service=audit()
    text=["# RTX operator frontier","",
        "Sixteen captured model/operator pairs passed own-path replay. On identical weight and F32 activation bytes, all eight Q8 operator classes in both models matched scalar outputs at native widths 2 and 4 and diverged at 8, 16 and 32. A single broadcast matmul over independent four-column groups matched the scalar output at 8, 16 and 32 for every captured descriptor. These are finite observations on this CUDA cohort.","",
        "## Operator evidence","",
        "The first graph-ordered relevant operation was the layer-zero Q projection. For each model the live scalar input columns concatenated byte-for-byte to the live native-wide input, the weights were identical, and scalar operator replay reproduced the live scalar outputs. Direct width-eight Q reproduced its corresponding replay. All eight rows in the retained 0.6B scoped wide-projection witness differ from its scalar oracle. In the new C1536 observer run only two of eight final rows equaled the earlier C1024 unscoped native witness; operator conclusions use own-path replay within each run.","",
        "CUPTI recorded the same row-Q8_1 activation quantizer at native widths four and eight. The MMVQ launch block changed from 32 × 4 threads to 32 × 2. The CUDA source uses four reduction warps through width four and two at width eight. At 16 and 32 the trace switched to MMQ quantization, matrix multiplication and stream-K fixup. These observations localize width-eight divergence without assuming a change from F32 to Q8 activation arithmetic. Internal temporary quantized bytes were not separately captured.","",
        "The candidate represents complete groups as [K,4,g], broadcasts the original Q8 weight, and reshapes the result as a view. A remainder uses the existing bounded tile and one join. The activation must be contiguous, with a dense, unbatched weight and at least eight columns. The runtime study admits fully GPU-offloaded Qwen3-8B on this RTX backend. CPU and hybrid execution of this candidate are unqualified. Both local and whole-graph cuts use the same linked operator core.","",
        "Isolated Qwen8B width-32 replay below uses the same observed CUDA0 operands. Times are median synchronized graph execution over the three post-warm repeats in the unprofiled replay. GPU kernel sums come from a separate CUPTI pass. The tile concatenation bytes count logical output writes.","",
        "| Class | Descriptor K × output | Tile / pack kernels | Tile / pack execution µs | Tile / pack GPU kernel µs | Tile concat MiB |",
        "|---|---:|---:|---:|---:|---:|"]
    for op in ops:
        if op["model"]!="8B":continue
        desc=op["descriptor"]["weight"];routes={r["route"]:r for r in op["routes"] if r["q"]==32}
        a,b=routes["tile"],routes["packed"]
        def wall(r):return statistics.median([1e6*(x+y) for x,y in zip(r["submit_s"][1:],r["sync_s"][1:])])
        text.append(f"| {desc['name']} | {desc['ne'][0]} × {desc['ne'][1]} | {a['activity']['kernels']} / {b['activity']['kernels']} | {wall(a):.1f} / {wall(b):.1f} | {1000*a['activity']['kernel_ms']:.1f} / {1000*b['activity']['kernel_ms']:.1f} | {a['concat_output_bytes']/2**20:.2f} |")
    text+=["","At q32 the old Q projection issued eight four-column matmuls with seven joins. The packed projection issued one four-column, eight-group matmul. Trace records include kernel names, launch grids, block dimensions and durations. The profiler and clean measurements used separate binaries. CPU graph-definition time, submission and synchronization wait are separate fields in the replay receipts. GPU kernel times can overlap CPU submission and must not be added to the wall interval.","",
       "## Active KV boundaries","",
       "Each cell restores a scalar R prefix from the same serialized state. P was measured as 256. Five paths matched all 800 appended vocabulary vectors and 40 subsequent continuation vectors. The append clock includes splitting, graph work, materialization, compute and synchronization. All 120 measured appends have an immediate same-arm warmup from identical state. The table gives geometric means in milliseconds over three paired blocks.","",
       "| Boundary | Head | q | Cross | S1 | QB4 | WB4 | New QB | New WB | New WB / QB |","|---:|---:|---:|:---:|---:|---:|---:|---:|---:|---:|"]
    blocks={(r["cell"],r["block"],r["arm"]):r["measured"]["append_s"] for r in cost}
    arms=["S1","QB4","WB4","newQB","newWB"]
    ratios={}
    for i,(b,q,h,cross) in enumerate(read("matrix-plan.json")["cells"]):
        v={a:gm([blocks[i,s,a] for s in range(3)]) for a in arms}
        ratios[i]=v["newWB"]/v["newQB"]
        text.append(f"| {b} | {h} | {q} | {'yes' if cross else 'no'} | "+" | ".join(f"{1000*v[a]:.2f}" for a in arms)+f" | {ratios[i]:.3f} |")
    text+=["",f"New WB time / new QB time is {gm([ratios[i] for i in (0,2,4,6)]):.3f}× for noncrossing cells and {gm([ratios[i] for i in (1,3,5,7)]):.3f}× for crossing cells. The coordinates have deliberately balanced cut density. Their average has no deployment-frequency interpretation.","",
       "Every QK and AV row group agreed with the registered geometry. At B1024/H1021, q32 uses extents 1024 then 1280 with QK/AV groups 3+4+4+4+4+4+4+4+1. Local submits [32], whereas WB submits [3,29]. Local Q projection uses one [output,4,8] matmul. WB restarts at the boundary and uses three columns in the first graph, then seven four-column groups and a one-column tail. Counts, bytes and physical graph-build/reuse observations for every cell are in coordinates.json.","",
       "## Unseen natural confirmation and service cost","",
       f"The fixed panel used four fresh inputs, C1536, k3 and cap128. Old QB4, new QB and new WB matched {sum(len(r['vectors']) for r in proof if r['arm']!='S1')} committed-vector comparisons against immutable R and {sum(len(r['branch']) for r in proof if r['arm']!='S1')} branch-vector comparisons against scalar k3, including uncommitted positions. The sets overlap. Endpoints and complete cycle transactions matched. Timed R was not an arm in this panel.","",
       "| Arm | Complete service s | Prefill wall s | Target verify s | Continuation wall s |","|---|---:|---:|---:|---:|"]
    times={}
    for a in ["oldQB","newQB","newWB"]:
        rows=[r["measured"] for r in service if r["arm"]==a];cols=[gm([r[k] for r in rows]) for k in ("service_seconds","prefill_wall_seconds","continuation_wall_seconds")]
        times[a]=cols[0];ver=gm([r["target_phases"]["VERIFY"] for r in rows]);text.append(f"| {a} | {cols[0]:.4f} | {cols[1]:.4f} | {ver:.4f} | {cols[2]:.4f} |")
    phase=times["oldQB"]/times["newQB"];cut=times["newWB"]/times["newQB"]
    pairs={(x["session"],x["index"],x["arm"]):x["measured"]["service_seconds"] for x in service}
    text+=["",f"Old QB / new QB was **{phase:.4f}×**. New WB / new QB was **{cut:.4f}×**. The first ratio isolates the operator change with local grouping fixed. The second compares group organization with identical operator lowering. Per-session WB/QB ratios were "+", ".join(f"{gm([pairs[s,i,'newWB']/pairs[s,i,'newQB'] for i in range(4)]):.4f}" for s in range(3))+".","",
       f"The 36 service measurements and 36 immediate warmups used {sum(r['measured']['service_seconds'] for r in service):.1f} and {sum(r['warm']['service_seconds'] for r in service):.1f} service seconds. Model loading, pool provisioning and process wall are recorded separately in the raw receipts. Resident service includes reset, target and draft prefill, the inherited verify/rollback/sampling loop and synchronization.","",
       "## Contribution boundary","",
       "The supported mechanism is parallel execution of independent compatible reductions using an existing CUDA dispatch. It removes repeated launch and concat work without relaxing the original numerical reference. The operator benefit applies to WB and QB alike. Local grouping and operator packing are separate contributions; their estimates must stay separate. The aligned PR168 pilot and its mixed session directions remain historical evidence. Four natural inputs on one RTX system do not establish population speedup. This result is ready for comparison with the independent B570 work."]
    (HERE/"RESULTS.md").write_text("\n".join(text)+"\n",encoding="utf8")
    print(f"16 replay descriptors, {len(geo)} coordinate receipts, 840 vector checks, {len(cost)} append and {len(service)} service pairs")
if __name__=="__main__":main()

