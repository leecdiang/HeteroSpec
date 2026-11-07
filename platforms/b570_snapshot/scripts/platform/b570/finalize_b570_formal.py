#!/usr/bin/env python3
"""Close, archive, commit, push, and shut down one unattended B570 formal run."""

from __future__ import annotations

import argparse, hashlib, json, math, shutil, statistics, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

def utc(): return datetime.now(timezone.utc).isoformat()
def write_json(path, value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""): h.update(b)
    return h.hexdigest()
def run(cmd,cwd,timeout=120): return subprocess.run(cmd,cwd=cwd,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout)
def fmt(x,d=4): return "NOT RUN" if x is None else f"{x:.{d}f}"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,required=True); ap.add_argument("--run-root",type=Path,required=True); a=ap.parse_args()
    repo,root=a.repo.resolve(),a.run_root.resolve(); processed=root/"processed"
    outcome=json.loads((root/"stage-outcome.json").read_text(encoding="utf-8-sig")) if (root/"stage-outcome.json").exists() else {"overall_status":"RUNTIME_FAILURE"}
    correctness=json.loads((processed/"correctness.json").read_text(encoding="utf-8-sig")) if (processed/"correctness.json").exists() else None
    verification=json.loads((processed/"verification.json").read_text(encoding="utf-8-sig")) if (processed/"verification.json").exists() else None
    cstatus=correctness.get("status") if correctness else outcome.get("correctness","NOT_RUN")
    v512=v2048=None
    if verification and verification.get("status")=="PASS":
        v512=verification["depths"].get("512",{}).get("fast_ubatch2",{}).get("v2_ratio_of_medians")
        v2048=verification["depths"].get("2048",{}).get("fast_ubatch2",{}).get("v2_ratio_of_medians")
    if cstatus=="PASS" and v512 is not None: classification="CASE A" if v512<=1.20 else "CASE C"
    elif cstatus=="FAIL": classification="UNCLASSIFIED (V2 prohibited after correctness failure)"
    else: classification="UNCLASSIFIED"
    human="NOT_RUN_BY_PREREGISTRATION_V2_SEPARATE_LATER_PHASE"
    run_id=root.name

    cruns=correctness.get("runs",[]) if correctness else []
    pairs=sum(1 for r in cruns if r.get("condition")=="vulkan_k2" and r.get("exact_match"))
    bycond={k:[r["energy"]["board_energy_j_per_output_token"] for r in cruns if r.get("condition")==k and r.get("energy",{}).get("board_energy_j_per_output_token") is not None] for k in ("baseline","vulkan_k2")}
    acceptance_values=[r.get("metrics",{}).get("acceptance_rate") for r in cruns if r.get("condition")=="vulkan_k2" and r.get("metrics",{}).get("acceptance_rate") is not None]
    report_c=f"""# B570 Correctness Gate — Formal v2 Closeout

Run `{run_id}` executed the six frozen prompts under preregistration commit `59185f24793eb2b852be0821295d13c44ad97636`. The earlier `formal-20260912-001606` attempt remains **INVALID / CONFIGURATION-BLOCKED** and is excluded from Vulkan correctness inference.

## Result

**CORRECTNESS = {cstatus}**

- normalized exact pairs: {pairs}/18
- completed workload records: {len(cruns)}/36
- true mismatch records: {len(correctness.get('mismatches',[])) if correctness else 0}
- contract: generated token IDs only, prompt excluded, maximum 128, raw CLI total-token counts excluded
- frozen configuration: Vulkan0 Arc B570; Qwen3-8B/Qwen3-0.6B Q8_0; greedy; k=2; ctx 1024; batch 512; ubatch 128; full offload

Telemetry was collected as supporting instrumentation at the qualified B570 board boundary. It does not retroactively change preregistration v2's `power_measurement=false` declaration.
"""
    (repo/"reports/b570/B570_CORRECTNESS_GATE.md").write_text(report_c,encoding="utf-8")
    rows=[]
    if verification:
        for depth,paths in verification.get("depths",{}).items():
            for name,val in paths.items(): rows.append(f"| {depth} | {name} | {val['pp1']['median_ns']/1e6:.6f} | {val['pp2']['median_ns']/1e6:.6f} | {val['v2_ratio_of_medians']:.6f} |")
    report_v=f"""# B570 Verification Mechanism — Formal v2 Closeout

**Status: {verification.get('status') if verification else 'NOT RUN'}**. Under preregistration v2, V2 runs only after an exact correctness PASS and is a target-forward mechanism proxy, never end-to-end speedup.

| context n | path | PP1 median ms | PP2 median ms | V2 ratio |
|---:|---|---:|---:|---:|
{chr(10).join(rows) if rows else '| — | — | — | — | NOT RUN |'}

Primary gate value: `V2_exact(512) = {fmt(v512,6)}`. Secondary: `V2_exact(2048) = {fmt(v2048,6)}`. Each valid cell contains 20 repetitions; raw samples, means, standard deviations and CVs are preserved in the processed JSON. Cell-level telemetry covers the whole combined PP1/PP2 process and is diagnostic, not per-operation energy.
"""
    (repo/"reports/b570/B570_VERIFICATION_MECHANISM.md").write_text(report_v,encoding="utf-8")
    close=f"""# Arc B570 Backend-Control Platform Closeout

## Final disposition

- formal run: `{run_id}`
- overall status: `{outcome.get('overall_status')}`
- correctness: `{cstatus}`
- V2 exact 512: `{fmt(v512,6)}`
- V2 exact 2048: `{fmt(v2048,6)}`
- classification: **{classification}**
- HumanEval30: **{human}**

The B570 was added as a Vulkan backend-generalization control for the Intel Core i5-13400 / Arc B570 / DDR4-3200 / Windows 11 25H2 platform. Runtime was llama.cpp b10839 (`0cae43063`), Vulkan0, frozen Qwen3-8B and Qwen3-0.6B Q8_0 hashes, full offload, greedy decoding, k=2, ctx 1024, batch 512, ubatch 128, and a 128-generated-token contract.

## Preregistration history and stop rule

Qualification commit `385f3fc590e4b37d27d7ae6db9211aa7803c84ba` preceded replacement preregistration commit `59185f24793eb2b852be0821295d13c44ad97636`, which preceded this result. The v1 attempt failed because batch/context capacity and CLI token-boundary semantics made it invalid; it remains retained as **INVALID / CONFIGURATION-BLOCKED**, not a Vulkan numerical failure.

Preregistration v2 is controlling. Its stop rule permits only the six-prompt correctness gate followed, on exact PASS, by V2. It explicitly describes HumanEval30 as a separate later proposal and declares power measurement false. Therefore this unattended closeout did not run HumanEval30, even if the prompt's later-stage gate would otherwise allow it. PresentMon Card Power was collected per the newer operational request, but is classified as supporting telemetry rather than preregistered formal energy evidence.

## Energy boundary and limitations

The sensor boundary is Intel Arc B570 **GPU board energy**, `PM_METRIC_GPU_CARD_POWER` at 100 ms, integrated over exact QPC workload bounds. CPU package energy was unavailable, so no result is whole-system energy. Level Zero B570 energy was unsupported. Correctness-run supporting median J/token was `{fmt(statistics.median(bycond['baseline']) if bycond['baseline'] else None,6)}` baseline and `{fmt(statistics.median(bycond['vulkan_k2']) if bycond['vulkan_k2'] else None,6)}` speculative; these are not promoted to a preregistered energy comparison.

No CUDA/Vulkan/Metal causal equivalence is claimed. Results characterize only the tested runtime, models, driver, device and frozen settings. The B570 platform is **CLOSED** unless a later paper-review protocol explicitly reopens it.
"""
    (repo/"reports/b570/B570_PLATFORM_CLOSEOUT.md").write_text(close,encoding="utf-8")

    archive=repo/"artifacts/b570_backend_control"/run_id; archive.mkdir(parents=True,exist_ok=False)
    sources=[root/"manifest-preflight.json",root/"stage-outcome.json",processed/"correctness.json"]
    if verification: sources.append(processed/"verification.json")
    sources += sorted((root/"telemetry").glob("*.csv"))+sorted((root/"telemetry").glob("*.metadata.json"))
    entries=[]
    for src in sources:
        if not src.exists(): continue
        dst=archive/src.name if src.parent.name!="telemetry" else archive/"telemetry"/src.name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        if src.read_bytes()!=dst.read_bytes(): raise RuntimeError(f"archive byte mismatch: {src}")
        entries.append({"source_run_path":str(src.relative_to(repo)),"archived_path":str(dst.relative_to(repo)),"size":dst.stat().st_size,"sha256":sha(dst),"byte_identity":True,"experiment_run_id":run_id,"classification":"authoritative" if src.name in ("correctness.json","verification.json","manifest-preflight.json") else "supporting","runtime_commit":"0cae43063cf15170e91a2ff4d034da0ecef4a1b2","target_sha256":"408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6","draft_sha256":"9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031","backend_device":"Vulkan0 / Intel Arc B570"})
    archive_manifest={"schema":"heterospec.b570.archive.v1","run_id":run_id,"created_at":utc(),"files":entries,"derived_processed_outputs":["correctness.json"]+(["verification.json"] if verification else []),"exclusions":[{"path":"work/b570/formal-20260912-001606","reason":"INVALID / CONFIGURATION-BLOCKED"},{"type":"stdout/stderr","reason":"not promoted except retained locally; structured evidence and telemetry are sufficient"}]}
    write_json(archive/"manifest.json",archive_manifest)

    commits=[]
    run(["git","add","--","scripts/platform/b570","reports/b570"],repo)
    p=run(["git","commit","-m","experiment: complete B570 correctness and verification controls"],repo)
    if p.returncode==0: commits.append(run(["git","rev-parse","HEAD"],repo).stdout.strip())
    run(["git","add","--","artifacts/b570_backend_control"],repo)
    p=run(["git","commit","-m","archive: preserve B570 paper-critical provenance"],repo)
    if p.returncode==0: commits.append(run(["git","rev-parse","HEAD"],repo).stdout.strip())
    push=run(["git","push","origin","windows/b570-backend-control"],repo,timeout=180)
    push_status="PASS" if push.returncode==0 else "FAIL: "+push.stderr[-1000:]
    pr_url=None
    try:
        existing=run(["gh","pr","list","--head","windows/b570-backend-control","--base","main","--json","url","--jq",".[0].url"],repo,timeout=60)
        if existing.returncode==0 and existing.stdout.strip(): pr_url=existing.stdout.strip()
        else:
            pr=run(["gh","pr","create","--base","main","--head","windows/b570-backend-control","--title","Add Arc B570 backend-control results","--body","Preregistered Arc B570/Vulkan correctness and verification controls, qualified board-power telemetry, provenance archive, and platform closeout. Not merged."],repo,timeout=120)
            if pr.returncode==0: pr_url=pr.stdout.strip().splitlines()[-1]
    except Exception: pass
    final={"overall_status":outcome.get("overall_status"),"formal_run_id":run_id,"correctness":cstatus,"V2_512":v512,"V2_2048":v2048,"classification":classification,"humaneval30_status":human,"GM_speedup":None,"speedup_CI":None,"faster_prompts":None,"exact_pairs":pairs if correctness else None,"acceptance":statistics.fmean(acceptance_values) if acceptance_values else None,"board_J_per_token_baseline":statistics.median(bycond["baseline"]) if bycond["baseline"] else None,"board_J_per_token_spec":statistics.median(bycond["vulkan_k2"]) if bycond["vulkan_k2"] else None,"energy_efficiency_ratio":None,"energy_CI":None,"archive_status":"PASS","git_commit_SHAs":commits,"push_status":push_status,"PR_url":pr_url,"shutdown_scheduled":True,"completed_at":utc()}
    write_json(repo/"work/b570/FINAL_STATUS.json",final)
    (repo/"work/b570/FINAL_STATUS.txt").write_text(f"{run_id}: {final['overall_status']}; correctness={cstatus}; V2_512={v512}; HumanEval30={human}; archive=PASS; push={push_status}; shutdown scheduled.\n",encoding="utf-8")
    time.sleep(60)
    subprocess.run(["shutdown.exe","/s","/t","60","/c","HeteroSpec B570 formal experiment completed; results preserved."])

if __name__=="__main__": main()
