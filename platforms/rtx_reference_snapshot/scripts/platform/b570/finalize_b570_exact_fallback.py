#!/usr/bin/env python3
"""Analyze, report, archive, commit, and push the B570 exact-fallback run."""
import argparse, csv, hashlib, json, math, random, shutil, statistics, subprocess
from datetime import datetime, timezone
from pathlib import Path

def utc(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2)+"\n",encoding="utf-8")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def gm(xs): return math.exp(statistics.fmean(math.log(x) for x in xs)) if xs else None
def prompt_means(pairs,key,exact=False):
    groups={}
    for x in pairs:
        if exact and not x["exact"]: continue
        groups.setdefault(x["task_id"],[]).append(x[key])
    return {k:gm(v) for k,v in groups.items()}
def bootstrap(vals,seed=20260910,n=10000):
    if not vals:return None
    r=random.Random(seed); xs=list(vals); dist=sorted(gm([r.choice(xs) for _ in xs]) for _ in range(n))
    return [dist[int(.025*n)],dist[min(n-1,int(.975*n))]]
def fmt(x): return "N/A" if x is None else f"{x:.4f}"
def run(cmd,cwd,timeout=600):
    git=r"C:\Users\DIANG\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
    if cmd[0]=="git": cmd[0]=git
    z=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=timeout)
    if z.returncode: raise RuntimeError(f"command failed: {cmd}\n{z.stdout}\n{z.stderr}")
    return z.stdout.strip()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,required=True); ap.add_argument("--run-root",type=Path,required=True)
    a=ap.parse_args(); repo=a.repo.resolve(); root=a.run_root.resolve()
    cfg=load(repo/"benchmarks/b570_backend_control/exact_fallback_validation_v1.json")
    v=load(root/"processed/v2_exact.json"); h=load(root/"processed/humaneval30_exact_fallback.json")
    pairs=h["pairs"]; exact=sum(x["exact"] for x in pairs); all_exact=exact==len(pairs)
    sp=prompt_means(pairs,"speedup"); en=prompt_means(pairs,"board_energy_ratio")
    spx=prompt_means(pairs,"speedup",True); enx=prompt_means(pairs,"board_energy_ratio",True)
    runs={x["run_id"]:x for x in h["runs"]}
    spec_runs=[x for x in h["runs"] if x["condition"]=="vulkan_k2"]
    acceptance=[x["metrics"].get("acceptance_rate") for x in spec_runs if x["metrics"].get("acceptance_rate") is not None]
    accepted_per_round=[x["metrics"].get("stats_accepted_tokens",x["metrics"].get("accepted_tokens"))/x["metrics"]["verification_rounds"] for x in spec_runs if x["metrics"].get("verification_rounds")]
    baseline_jpt=[x["energy"]["board_energy_j_per_output_token"] for x in h["runs"] if x["condition"]=="baseline"]
    fallback_jpt=[x["energy"]["board_energy_j_per_output_token"] for x in spec_runs]
    speed_values=list(sp.values()); energy_values=list(en.values())
    analysis={"schema":"heterospec.b570.exact_fallback_analysis.v1","run_id":root.name,"created_at":utc(),
      "correctness":{"exact_pairs":exact,"total_pairs":len(pairs),"exact_prompts":sum(all(x["exact"] for x in pairs if x["task_id"]==t) for t in sp),"total_prompts":len(sp),"global_admissible":all_exact},
      "V2_exact":{k:x.get("v2_ratio_of_medians") for k,x in v["cells"].items()},
      "performance":{"scientific_label":"GLOBAL_ADMISSIBLE" if all_exact else "DIAGNOSTIC_OVERALL; EXACT_SUBSET_SEPARATELY",
        "prompt_geometric_mean_speedup":gm(speed_values),"prompt_median_speedup":statistics.median(speed_values),"bootstrap_95_ci":bootstrap(speed_values),"prompts_faster":sum(x>1 for x in speed_values),
        "exact_subset_prompt_geometric_mean_speedup":gm(spx.values()),"exact_subset_bootstrap_95_ci":bootstrap(spx.values())},
      "speculation":{"acceptance_mean":statistics.fmean(acceptance) if acceptance else None,"acceptance_median":statistics.median(acceptance) if acceptance else None,"accepted_tokens_per_round_mean":statistics.fmean(accepted_per_round) if accepted_per_round else None},
      "energy":{"boundary":"Arc B570 board only","ratio_definition":"baseline J/token / fallback J/token","prompt_geometric_mean_efficiency_ratio":gm(energy_values),"prompt_median_efficiency_ratio":statistics.median(energy_values),"bootstrap_95_ci":bootstrap(energy_values),
        "baseline_mean_j_per_token":statistics.fmean(baseline_jpt),"baseline_median_j_per_token":statistics.median(baseline_jpt),"fallback_mean_j_per_token":statistics.fmean(fallback_jpt),"fallback_median_j_per_token":statistics.median(fallback_jpt),
        "exact_subset_efficiency_ratio":gm(enx.values()),"greater_is_better":True},
      "closure":"CLOSED_AFTER_UNIQUE_SERIALIZED_CANDIDATE"}
    save(root/"processed/exact_fallback_analysis.json",analysis)
    save(repo/"analysis/b570_exact_fallback_summary.json",analysis)
    csvpath=root/"processed/exact_fallback_prompt_summary.csv"
    with csvpath.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["task_id","all_3_exact","speedup_gm","board_energy_ratio_gm"])
        for t in sorted(sp,key=lambda x:int(x.split('/')[1])):
            w.writerow([t,all(x["exact"] for x in pairs if x["task_id"]==t),sp[t],en[t]])
    (repo/"analysis").mkdir(parents=True,exist_ok=True)
    shutil.copy2(csvpath,repo/"analysis/b570_exact_fallback_prompt_summary.csv")
    v512=analysis["V2_exact"].get("512"); v2048=analysis["V2_exact"].get("2048")
    report=f"""# B570 Exact Fallback Validation

Status: **{'PASS / GLOBALLY ADMISSIBLE' if all_exact else 'CORRECTNESS FAIL / DIAGNOSTIC PERFORMANCE ONLY'}**

## Frozen candidate

The unique serialized fallback changes only speculative `n_ubatch` from 128 to 1. Models, hashes, Vulkan0 placement, full target/draft offload, greedy decode, seed, k=2, context, batch, and output contract remained frozen.

## Correctness

- Exact pairs: {exact}/{len(pairs)}
- Stable exact prompts: {analysis['correctness']['exact_prompts']}/{analysis['correctness']['total_prompts']}
- Global performance admissible: {str(all_exact).upper()}

## Verification mechanism

- V2_exact(512): {fmt(v512)}
- V2_exact(2048): {fmt(v2048)}

V2 is a PP2/PP1 target-forward mechanism proxy, not end-to-end speedup.

## End-to-end timing

- Prompt-level geometric-mean speedup (baseline/fallback): {fmt(analysis['performance']['prompt_geometric_mean_speedup'])}
- Prompt-level median speedup: {fmt(analysis['performance']['prompt_median_speedup'])}
- 95% prompt bootstrap CI: {analysis['performance']['bootstrap_95_ci']}
- Prompts faster: {analysis['performance']['prompts_faster']}/30
- Exact-subset speedup: {fmt(analysis['performance']['exact_subset_prompt_geometric_mean_speedup'])}

## Board energy

- Energy-efficiency ratio (baseline/fallback board J per token): {fmt(analysis['energy']['prompt_geometric_mean_efficiency_ratio'])}
- 95% prompt-bootstrap CI: {analysis['energy']['bootstrap_95_ci']}
- Baseline mean/median board J/token: {fmt(analysis['energy']['baseline_mean_j_per_token'])} / {fmt(analysis['energy']['baseline_median_j_per_token'])}
- Fallback mean/median board J/token: {fmt(analysis['energy']['fallback_mean_j_per_token'])} / {fmt(analysis['energy']['fallback_median_j_per_token'])}
- Exact-subset efficiency ratio: {fmt(analysis['energy']['exact_subset_efficiency_ratio'])}

The boundary is Arc B570 adapter board power only; CPU package, wall, and whole-system energy are excluded.

## Platform decision

This exhausts the single preregistered exact fallback candidate. No additional parameter or backend search is authorized; the B570 backend-control campaign is **CLOSED**.
"""
    (repo/"reports/b570/B570_EXACT_FALLBACK_VALIDATION.md").write_text(report,encoding="utf-8")
    comparison=f"""# B570 Fast Path versus Exact Fallback

| Path | Correctness | V2(512) | V2(2048) | Speedup GM | Board-energy ratio |
|---|---:|---:|---:|---:|---:|
| Fast path | 45/90 pairs | 1.2426 | 1.6373 | 0.5383 | 0.6961 |
| Serialized fallback | {exact}/{len(pairs)} pairs | {fmt(v512)} | {fmt(v2048)} | {fmt(analysis['performance']['prompt_geometric_mean_speedup'])} | {fmt(analysis['energy']['prompt_geometric_mean_efficiency_ratio'])} |

Fast-path timing remains diagnostic because its correctness gate failed. Serialized-fallback timing is globally admissible only when all 90 normalized pairs are exact.
"""
    (repo/"reports/b570/B570_FAST_VS_EXACT_FALLBACK.md").write_text(comparison,encoding="utf-8")
    closure=f"""# B570 Final Closure

The Arc B570 backend-control work is closed after the one preregistered serialized fallback candidate.

- Formal exactness: {exact}/{len(pairs)} pairs
- Formal V2_exact: 512={fmt(v512)}, 2048={fmt(v2048)}
- End-to-end speedup GM: {fmt(analysis['performance']['prompt_geometric_mean_speedup'])}
- Board-energy efficiency ratio: {fmt(analysis['energy']['prompt_geometric_mean_efficiency_ratio'])}
- Further search: **not authorized**
"""
    (repo/"reports/b570/B570_PLATFORM_FINAL_CLOSURE.md").write_text(closure,encoding="utf-8")
    section=f"""\n\n## Exact fallback final validation ({root.name})\n\n- correctness: {exact}/{len(pairs)} exact pairs\n- V2_exact: 512={fmt(v512)}, 2048={fmt(v2048)}\n- speedup GM: {fmt(analysis['performance']['prompt_geometric_mean_speedup'])}\n- Arc B570 board-energy efficiency ratio: {fmt(analysis['energy']['prompt_geometric_mean_efficiency_ratio'])}\n- platform status: CLOSED\n"""
    for name in ("B570_VERIFICATION_MECHANISM.md","B570_HUMANEVAL30_DIAGNOSTIC.md","B570_PLATFORM_CLOSEOUT.md"):
        p=repo/"reports/b570"/name; p.write_text(p.read_text(encoding="utf-8").rstrip()+section,encoding="utf-8")
    cross=f"""# Cross-platform Backend Summary\n\n| Platform | Backend | Fast-path correctness | V2 fast/raw | Exact fallback | V2 exact | HumanEval exactness | Valid speedup | Energy boundary | Main limitation |\n|---|---|---|---|---|---|---|---|---|---|\n| Apple M4 | Metal | PASS | not recorded here | available | not recorded here | 90/90 | 1.387x | Apple package | representative 24Q was 0.842x |\n| RTX 5070 Ti | CUDA | blocked | 1.009 / 0.983 | available | 2.431 / 2.137 | fallback 90/90 | 0.650x | RTX component where measured | exact fallback expensive |\n| Intel Arc B570 | Vulkan | blocked, 45/90 | 1.2426 / 1.6373 | unique serialized candidate | {fmt(v512)} / {fmt(v2048)} | {exact}/{len(pairs)} | {fmt(analysis['performance']['prompt_geometric_mean_speedup']) if all_exact else 'not globally admissible'} | Arc B570 board | strict exactness changes the admissible path |\n\nStrict exactness can alter the admissible execution path across multiple tested discrete-GPU backends. This does not claim that CUDA and Vulkan share an identical root cause.\n"""
    (repo/"reports/b570/B570_CROSS_PLATFORM_SUMMARY.md").write_text(cross,encoding="utf-8")

    run(["git","add","--","analysis/b570_exact_fallback_summary.json","analysis/b570_exact_fallback_prompt_summary.csv"],repo)
    run(["git","commit","-m","experiment: complete B570 exact fallback validation"],repo)
    archive=repo/"artifacts/b570_backend_control"/root.name/"exact_fallback"
    if archive.exists(): raise RuntimeError(f"Archive already exists: {archive}")
    archive.mkdir(parents=True)
    for rel in ("processed","stdout","stderr","telemetry","v2_exact","humaneval30"):
        src=root/rel
        if src.exists(): shutil.copytree(src,archive/rel,dirs_exist_ok=True)
    for name in ("status.json","status.txt","EXACT_FALLBACK_STATUS.txt","manifest-preflight.json","todesk-disconnect-check.json"):
        if (root/name).exists(): shutil.copy2(root/name,archive/name)
    shutil.copy2(repo/"benchmarks/b570_backend_control/exact_fallback_validation_v1.json",archive/"exact_fallback_validation_v1.json")
    files=[]
    for p in sorted(x for x in archive.rglob("*") if x.is_file()): files.append({"path":str(p.relative_to(repo)),"size":p.stat().st_size,"sha256":sha(p)})
    manifest={"schema":"heterospec.b570.exact_fallback_archive.v1","run_id":root.name,"created_at":utc(),
      "classification":"formal exact fallback validation","runtime_commit":cfg["platform"]["runtime_commit"],
      "target_sha256":cfg["platform"]["target"]["sha256"],"draft_sha256":cfg["platform"]["draft"]["sha256"],
      "backend_device":"Vulkan0 / Intel Arc B570","derived_outputs":["analysis/b570_exact_fallback_summary.json","analysis/b570_exact_fallback_prompt_summary.csv"],
      "exclusions":["models","runtime binaries","private caches","fast-path archives retained separately","remote-contaminated fallback V2"],"files":files}
    save(archive/"manifest.json",manifest)
    run(["git","add","-f","--",str(archive.relative_to(repo))],repo); run(["git","commit","-m","archive: preserve B570 exact fallback validation"],repo)
    run(["git","add","--","reports/b570"],repo); run(["git","commit","-m","docs: close B570 backend-control platform"],repo)
    run(["git","push","origin","windows/b570-backend-control"],repo,timeout=1200)
    final={"schema":"heterospec.b570.exact_fallback_final_status.v1","status":"COMPLETE","run_id":root.name,
      "correctness":"PASS" if all_exact else "FAIL","exact_pairs":f"{exact}/{len(pairs)}","V2_exact":analysis["V2_exact"],
      "correctness_prompts":f"{analysis['correctness']['exact_prompts']}/{analysis['correctness']['total_prompts']}",
      "speedup_gm":analysis["performance"]["prompt_geometric_mean_speedup"],"speedup_median":analysis["performance"]["prompt_median_speedup"],"speedup_CI":analysis["performance"]["bootstrap_95_ci"],"faster_prompts":analysis["performance"]["prompts_faster"],
      "acceptance":analysis["speculation"],"baseline_board_J_per_token":analysis["energy"]["baseline_mean_j_per_token"],"fallback_board_J_per_token":analysis["energy"]["fallback_mean_j_per_token"],"energy_efficiency_ratio":analysis["energy"]["prompt_geometric_mean_efficiency_ratio"],"energy_CI":analysis["energy"]["bootstrap_95_ci"],
      "fast_path_comparison":"reports/b570/B570_FAST_VS_EXACT_FALLBACK.md","cross_platform_interpretation":"reports/b570/B570_CROSS_PLATFORM_SUMMARY.md",
      "platform":"CLOSED","branch":"windows/b570-backend-control","pull_request":"https://github.com/leecdiang/HeteroSpec/pull/7",
      "archive":str(archive.relative_to(repo)),"head":run(["git","rev-parse","HEAD"],repo),"shutdown_status":"PENDING"}
    save(repo/"work/b570/EXACT_FALLBACK_FINAL_STATUS.json",final)
    (repo/"work/b570/EXACT_FALLBACK_FINAL_STATUS.txt").write_text("\n".join(f"{k}={v}" for k,v in final.items())+"\n",encoding="utf-8")

if __name__=="__main__": main()
