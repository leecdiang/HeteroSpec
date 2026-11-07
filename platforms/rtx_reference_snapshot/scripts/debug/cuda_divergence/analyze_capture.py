#!/usr/bin/env python3
import csv, hashlib, json, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
src=ROOT/"logs/cuda-divergence-logits-server.json"
data=json.loads(src.read_text(encoding="utf-8")); rows=[]; summary=[]
for rep in (1,2,3):
    group=[r for r in data["runs"] if r["run_id"]==rep]; base=next(r for r in group if r["path"]=="baseline")
    for run in group:
        first=next((i for i,(a,b) in enumerate(zip(base["tokens"],run["tokens"])) if a!=b),None)
        prefix=base["tokens"][:65]==run["tokens"][:65]
        focus=run["positions"][65]; top=focus["top"]
        score={x["token_id"]:x["log_probability"] for x in top}
        delta=score.get(2790)-score.get(2629) if 2790 in score and 2629 in score else None
        margin=top[0]["log_probability"]-top[1]["log_probability"]
        summary.append({"run_id":rep,"path":run["path"],"api_completion_index":65,"legacy_capture_index":190,"prefix_exact_before_index":prefix,"first_divergence_index":first,"argmax_token":run["tokens"][65],"log_score_2790":score.get(2790),"log_score_2629":score.get(2629),"delta_2790_minus_2629":delta,"top1_top2_margin":margin})
        for api_idx in range(63,67):
            pos=run["positions"][api_idx]; candidates=pos["top"][:5]; scores={x["token_id"]:x["log_probability"] for x in pos["top"]}
            for rank,c in enumerate(candidates,1):
                rows.append({"prompt_id":"HumanEval/106","run_id":rep,"path":run["path"],"completion_index":api_idx+125,"api_generated_index":api_idx,"token_rank":rank,"token_id":c["token_id"],"logit":c["log_probability"],"score_type":"log_probability; logits up to a position-wise additive constant","argmax_token":run["tokens"][api_idx],"top1_token":candidates[0]["token_id"],"top2_token":candidates[1]["token_id"],"top1_top2_margin":candidates[0]["log_probability"]-candidates[1]["log_probability"],"logit_2790":scores.get(2790,""),"logit_2629":scores.get(2629,""),"delta_2790_minus_2629":scores.get(2790,0)-scores.get(2629,0) if 2790 in scores and 2629 in scores else "","prefix_exact_before_index":prefix if api_idx==65 else base["tokens"][:api_idx]==run["tokens"][:api_idx],"first_divergence_index":first if first is not None else ""})
out=ROOT/"reports/5070ti/CUDA_DIVERGENCE_LOGITS.csv"; out.parent.mkdir(parents=True,exist_ok=True)
with out.open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
patch=ROOT/"scripts/debug/cuda_divergence/server-context-logprobs.patch"
result={"schema":"heterospec.cuda_divergence_diagnosis.v1","source":str(src.relative_to(ROOT)),"formal_runtime_commit":"0cae43063","debug_base_commit":"0cae43063","instrumentation_patch_sha256":hashlib.sha256(patch.read_bytes()).hexdigest(),"coordinate_mapping":"legacy captured index = API generated index + 125 for this frozen prompt/rendering; legacy 190 = API 65","runs":summary,"all_prefixes_exact_through_api_index_64":all(x["prefix_exact_before_index"] for x in summary),"all_sign_flips_stable":all(x["delta_2790_minus_2629"]<0 for x in summary if x["path"]=="batched_ub2") and all(x["delta_2790_minus_2629"]>0 for x in summary if x["path"]!="batched_ub2")}
(ROOT/"reports/5070ti/CUDA_DIVERGENCE_LOGITS_SUMMARY.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
