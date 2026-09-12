#!/usr/bin/env python3
"""Summarize, report, archive, and publish one B570 diagnostic extension."""
import argparse, hashlib, json, math, random, shutil, statistics, subprocess
from datetime import datetime, timezone
from pathlib import Path

def utc(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2)+"\n",encoding="utf-8")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def gm(xs): return math.exp(statistics.fmean(math.log(x) for x in xs)) if xs else None
def median(xs): return statistics.median(xs) if xs else None
def prompt_values(pairs,key,exact_only=False):
    groups={}
    for x in pairs:
        if exact_only and not x["exact"]: continue
        groups.setdefault(x["task_id"],[]).append(x[key])
    return {k:gm(v) for k,v in groups.items()}
def bootstrap(vals,seed=20260910,n=10000):
    if len(vals)<2:return None
    r=random.Random(seed); samples=sorted(gm([r.choice(vals) for _ in vals]) for _ in range(n))
    return [samples[int(.025*n)],samples[int(.975*n)-1]]
def corr(x,y,rank=False):
    rows=[(a,b) for a,b in zip(x,y) if a is not None and b is not None]
    if len(rows)<3:return None
    a,b=zip(*rows)
    if rank:
        def ranks(v):
            order=sorted(range(len(v)),key=lambda i:v[i]); out=[0.0]*len(v); i=0
            while i<len(v):
                j=i
                while j+1<len(v) and v[order[j+1]]==v[order[i]]:j+=1
                rankv=(i+j+2)/2
                for k in range(i,j+1):out[order[k]]=rankv
                i=j+1
            return out
        a,b=ranks(a),ranks(b)
    ma,mb=statistics.fmean(a),statistics.fmean(b); den=math.sqrt(sum((z-ma)**2 for z in a)*sum((z-mb)**2 for z in b))
    return sum((u-ma)*(v-mb) for u,v in zip(a,b))/den if den else None
def run(cmd,cwd,timeout=300): return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=timeout)
def fmt(x): return "NOT RUN" if x is None else f"{x:.4f}"
def append_once(path,marker,text):
    old=path.read_text(encoding="utf-8") if path.exists() else ""
    if marker not in old:path.write_text(old.rstrip()+"\n\n"+text.strip()+"\n",encoding="utf-8")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,required=True); ap.add_argument("--run-root",type=Path,required=True); a=ap.parse_args()
    repo,root=a.repo.resolve(),a.run_root.resolve(); proc=root/"processed"
    v=load(proc/"v2_raw.json"); h=load(proc/"humaneval30_diagnostic.json"); f=load(proc/"fallback.json")
    runs={x["run_id"]:x for x in h["runs"]}
    for pair in h["pairs"]:
        b,s=runs[pair["baseline_run_id"]],runs[pair["speculative_run_id"]]
        pair["baseline_elapsed_s"],pair["speculative_elapsed_s"]=b["elapsed_s"],s["elapsed_s"]
        pair["baseline_board_j_per_token"]=b["energy"]["board_energy_j_per_output_token"]
        pair["speculative_board_j_per_token"]=s["energy"]["board_energy_j_per_output_token"]
        pair["board_energy_ratio"]=pair["baseline_board_j_per_token"]/pair["speculative_board_j_per_token"]
        pair["baseline_mean_board_power_w"],pair["speculative_mean_board_power_w"]=b["energy"]["mean_board_power_w"],s["energy"]["mean_board_power_w"]
    exact_prompts=[q for q in sorted(set(x["task_id"] for x in h["pairs"])) if all(x["exact"] for x in h["pairs"] if x["task_id"]==q)]
    mismatch_prompts=sorted(set(x["task_id"] for x in h["pairs"] if not x["exact"]))
    divergence=[]
    for q in sorted(set(x["task_id"] for x in h["pairs"]),key=lambda z:int(z.split('/')[1])):
        p=[x for x in h["pairs"] if x["task_id"]==q]; bad=[x for x in p if not x["exact"]]; signatures={(x["first_divergence_index"],x["baseline_token"],x["speculative_token"]) for x in bad}
        cls="NO_DIVERGENCE" if not bad else "STABLE_3_OF_3" if len(bad)==3 and len(signatures)==1 else "STABLE_2_OF_3" if len(bad)==2 and len(signatures)==1 else "UNSTABLE"
        divergence.append({"task_id":q,"classification":cls,"mismatch_repetitions":len(bad),"signatures":[list(x) for x in signatures]})
    raw=prompt_values(h["pairs"],"raw_speedup"); exact=prompt_values(h["pairs"],"raw_speedup",True)
    raw_e=prompt_values(h["pairs"],"board_energy_ratio"); exact_e=prompt_values(h["pairs"],"board_energy_ratio",True)
    analyses={"schema":"heterospec.b570.diagnostic_summary.v1","run_id":root.name,"original_correctness":"FAIL","labels":{"all_pairs":"RAW DIAGNOSTIC / NOT CORRECTNESS-ADMISSIBLE AS A WHOLE","exact_subset":"POST-HOC EXACT-SUBSET DESCRIPTIVE STATISTIC"},
      "counts":{"exact_prompts":len(exact_prompts),"mismatch_prompts":len(mismatch_prompts),"exact_pairs":sum(x["exact"] for x in h["pairs"]),"mismatch_pairs":sum(not x["exact"] for x in h["pairs"])},
      "exact_prompt_ids":exact_prompts,"mismatch_prompt_ids":mismatch_prompts,
      "raw_speedup":{"gm":gm(list(raw.values())),"median":median(list(raw.values())),"ci95":bootstrap(list(raw.values())),"faster_prompts":sum(x>1 for x in raw.values())},
      "exact_subset_speedup":{"gm":gm(list(exact.values())),"median":median(list(exact.values())),"ci95":bootstrap(list(exact.values())),"prompt_count":len(exact)},
      "raw_energy":{"gm_ratio":gm(list(raw_e.values())),"median_ratio":median(list(raw_e.values())),"ci95":bootstrap(list(raw_e.values()))},
      "exact_subset_energy":{"gm_ratio":gm(list(exact_e.values())),"median_ratio":median(list(exact_e.values())),"ci95":bootstrap(list(exact_e.values())),"prompt_count":len(exact_e)},
      "divergence":divergence,
      "exploratory_correlations":{"pearson_acceptance_raw_speedup":corr([x["acceptance"] for x in h["pairs"]],[x["raw_speedup"] for x in h["pairs"]]),"spearman_acceptance_raw_speedup":corr([x["acceptance"] for x in h["pairs"]],[x["raw_speedup"] for x in h["pairs"]],True),"pearson_acceptance_exactness":corr([x["acceptance"] for x in h["pairs"]],[1 if x["exact"] else 0 for x in h["pairs"]])}}
    save(proc/"diagnostic_summary.json",analyses); save(proc/"divergence_summary.json",{"run_id":root.name,"prompts":divergence})
    v512=v["cells"].get("512",{}).get("v2_ratio_of_medians"); v2048=v["cells"].get("2048",{}).get("v2_ratio_of_medians")
    fv=f.get("v2_exact",{}) if isinstance(f.get("v2_exact"),dict) else {}; fv512=fv.get("512",{}).get("v2_ratio_of_medians") if fv else None; fv2048=fv.get("2048",{}).get("v2_ratio_of_medians") if fv else None
    stable=[x["task_id"] for x in divergence if x["classification"].startswith("STABLE")]
    report=f"""# B570 Diagnostic Extension

## Frozen prior result

The valid formal v2 gate remains **CORRECTNESS = FAIL** (9/18 exact pairs). This post-gate work is a **DIAGNOSTIC EXTENSION**, not a rescue or replacement validation. The fast Vulkan speculative path remains correctness-blocked.

## V2_raw

- context 512: `{fmt(v512)}`
- context 2048: `{fmt(v2048)}`

These are raw PP2/PP1 target-forward mechanism ratios, not V2_exact and not end-to-end speedup. Per-operation microbenchmark energy is not reliable because each telemetry trace combines PP1 and PP2 work.

## Frozen HumanEval30 diagnostic

- exact prompts: {analyses['counts']['exact_prompts']}/30
- mismatch prompts: {analyses['counts']['mismatch_prompts']}/30
- exact pairs: {analyses['counts']['exact_pairs']}/90
- mismatch pairs: {analyses['counts']['mismatch_pairs']}/90
- stable divergence prompts: {', '.join(stable) if stable else 'none'}

## Raw performance and board energy

The all-pair geometric-mean raw speedup is `{fmt(analyses['raw_speedup']['gm'])}x` (95% prompt-bootstrap CI `{analyses['raw_speedup']['ci95']}`). This is **DIAGNOSTIC / NOT CORRECTNESS-ADMISSIBLE AS A WHOLE**. The raw board-energy-efficiency ratio is `{fmt(analyses['raw_energy']['gm_ratio'])}x`, at the Intel Arc B570 GPU board boundary only.

The exact-only geometric-mean speedup is `{fmt(analyses['exact_subset_speedup']['gm'])}x` across {len(exact_prompts)} wholly exact prompts; its board-energy ratio is `{fmt(analyses['exact_subset_energy']['gm_ratio'])}x`. Both are **POST-HOC EXACT-SUBSET DESCRIPTIVE STATISTICS**, not unbiased primary estimates.

## Single predefined fallback

- candidate: serialized speculative `n_ubatch=1`
- correctness: `{f['status']}`
- V2_exact 512: `{fmt(fv512)}`
- V2_exact 2048: `{fmt(fv2048)}`
- fallback HumanEval30: **NOT AUTHORIZED / NOT RUN**

## Limitations

Mismatch timing and energy are descriptive only. GPU board energy is not whole-system or CPU package energy. Correlations are exploratory and do not establish causality. No backend, model, runtime, driver, k, p_min, prompt, or numerical-instrumentation search was performed.
"""
    (repo/"reports/b570/B570_DIAGNOSTIC_EXTENSION.md").write_text(report,encoding="utf-8")
    table="\n".join(f"| {x['task_id']} | {x['classification']} | {x['mismatch_repetitions']}/3 |" for x in divergence)
    he=f"""# B570 HumanEval30 Diagnostic

This is a post-gate prevalence study. The frozen fast path remains correctness-blocked.

| Prompt | Divergence stability | Mismatch pairs |
|---|---|---:|
{table}

Raw all-pair speedup: `{fmt(analyses['raw_speedup']['gm'])}x`; exact-subset descriptive speedup: `{fmt(analyses['exact_subset_speedup']['gm'])}x`. See the machine-readable result and diagnostic summary for all 90 pair classifications, individual timing, acceptance, telemetry, and divergence evidence.
"""
    (repo/"reports/b570/B570_HUMANEVAL30_DIAGNOSTIC.md").write_text(he,encoding="utf-8")
    note=f"""## Post-gate diagnostic extension ({root.name})

The original formal correctness result remains **FAIL** and unchanged. A later explicitly post-hoc diagnostic extension measured frozen HumanEval30 prevalence and raw mechanisms; it cannot rescue or replace the gate. See `B570_DIAGNOSTIC_EXTENSION.md`.
"""
    for name in ("B570_CORRECTNESS_GATE.md","B570_VERIFICATION_MECHANISM.md","B570_PLATFORM_CLOSEOUT.md"): append_once(repo/"reports/b570"/name,root.name,note)

    archive=repo/"artifacts/b570_backend_control"/root.name; archive.mkdir(parents=True,exist_ok=False)
    sources=[repo/"benchmarks/b570_backend_control/diagnostic_extension_v1.json",root/"manifest-preflight.json"]+list(proc.glob("*.json"))
    for td in (root/"v2raw/telemetry",root/"humaneval30/telemetry",root/"fallback/telemetry",root/"fallback_v2/telemetry"):
        if td.exists(): sources += list(td.glob("*.csv"))+list(td.glob("*.metadata.json"))
    entries=[]
    for src in sources:
        rel=src.relative_to(repo) if repo in src.parents else src.name; dst=archive/("telemetry" if src.parent.name=="telemetry" else "raw")/src.name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        if src.read_bytes()!=dst.read_bytes():raise RuntimeError(f"Archive byte mismatch: {src}")
        entries.append({"source_path":str(rel),"archived_path":str(dst.relative_to(repo)),"size":dst.stat().st_size,"sha256":sha(dst),"run_id":root.name,"classification":"authoritative" if src.suffix==".json" and src.name not in ("manifest-preflight.json",) else "supporting","runtime_commit":"0cae43063cf15170e91a2ff4d034da0ecef4a1b2","target_sha256":"408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6","draft_sha256":"9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031","backend_device":"Vulkan0 / Intel Arc B570"})
    manifest={"schema":"heterospec.b570.diagnostic_archive.v1","run_id":root.name,"created_at":utc(),"files":entries,"derived_reports":["reports/b570/B570_DIAGNOSTIC_EXTENSION.md","reports/b570/B570_HUMANEVAL30_DIAGNOSTIC.md"],"exclusions":["models","binaries","installers","caches","redundant stdout","mismatch timing as admissible optimization evidence"]}; save(archive/"manifest.json",manifest)
    commits=[]
    run(["git","add","-f","--",str(archive.relative_to(repo))],repo); z=run(["git","commit","-m","archive: preserve B570 diagnostic provenance"],repo); 
    if z.returncode==0: commits.append(run(["git","rev-parse","HEAD"],repo).stdout.strip())
    run(["git","add","--","reports/b570"],repo); z=run(["git","commit","-m","docs: close B570 diagnostic extension"],repo)
    if z.returncode==0: commits.append(run(["git","rev-parse","HEAD"],repo).stdout.strip())
    push=run(["git","push","origin","windows/b570-backend-control"],repo,300); push_status="PASS" if push.returncode==0 else "FAIL: "+push.stderr[-1000:]
    pr_url=None
    z=run(["gh","pr","list","--head","windows/b570-backend-control","--base","main","--json","url","--jq",".[0].url"],repo)
    if z.returncode==0 and z.stdout.strip():pr_url=z.stdout.strip()
    else:
        z=run(["gh","pr","create","--base","main","--head","windows/b570-backend-control","--title","Characterize Arc B570 post-gate diagnostic behavior","--body","Post-gate diagnostic extension preserving the prior correctness failure while reporting V2_raw, frozen HumanEval30 prevalence, descriptive timing, board energy, and one preregistered serialized fallback."],repo)
        if z.returncode==0:pr_url=z.stdout.strip().splitlines()[-1]
    final={"original_correctness":"FAIL","V2_raw_512":v512,"V2_raw_2048":v2048,"humaneval30_status":h["status"],**analyses["counts"],"raw_GM_speedup":analyses["raw_speedup"]["gm"],"raw_speedup_CI":analyses["raw_speedup"]["ci95"],"exact_subset_GM_speedup":analyses["exact_subset_speedup"]["gm"],"exact_subset_count":len(exact_prompts),"raw_board_energy_ratio":analyses["raw_energy"]["gm_ratio"],"exact_subset_energy_ratio":analyses["exact_subset_energy"]["gm_ratio"],"stable_divergence_prompts":stable,"fallback_status":f["status"],"fallback_correctness":"PASS" if f["status"]=="PASS" else "FAIL","fallback_V2_exact":{"512":fv512,"2048":fv2048},"archive_status":"PASS","git_commits":commits,"push_status":push_status,"PR_url":pr_url,"auto_shutdown":False,"completed_at":utc()}
    save(repo/"work/b570/DIAGNOSTIC_FINAL_STATUS.json",final); (repo/"work/b570/DIAGNOSTIC_FINAL_STATUS.txt").write_text(json.dumps(final,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":main()
