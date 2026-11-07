from pathlib import Path
import json
r=Path(__file__).parent;c=Path("C:/hs/b570-draft-cpu-20261020")
old=json.loads((c/"BUDGET_LEDGER.json").read_text(encoding="utf-8-sig"))
assert len(old["sessions"])==8 and old["status"]=="PROCESS_COMPLETED"
total=old["all_history_cumulative_seconds"]
pr={"study":"B570_DRAFT_PREFILL_SUBMISSION_V1","uuid":"e1225a47-6e66-4460-965f-2b705268c3a1",
"reference_parent":"PR134/51febaddcf49bb18565e568cf964a6e5c78876c9",
"intervention":"Draft prefill: one llama_decode API batch for prompt instead of one API call per token; n_ubatch remains1, n_batch512, threads8, last-prompt output flag only. Target/verification/proposal/state/DLLs unchanged. This is not multiquery arithmetic or the threads1 candidate.",
"source_basis":"llama_kv_cache::init_batch splits into ubatches at configured1; prepare simulates then restores cell metadata; each process_ubatch applies current token and recomputes physical key extent. Backend retains ordered execution/dependencies. Mandatory byte gate verifies this reasoning rather than assuming it.",
"qualification":{"inputs":"All four PR134 inputs,64 cap/EOG","requests":4,"reference":"346 original target/draft raw logits byte exact plus full endpoint/state","geometry":"Draft PREFILL Qcur callbacks must observe q1; no extra readback; observer absent from cost"},
"cost":{"inputs":["HumanEval/38","HumanEval/115"],"selection":"Fixed short CAP and long EOG representatives before candidate execution; no claim four-input performance confirmation",
"processes":3,"arms":["BASE_A","BASE_B","BULK1"],"warmup_requests":9,"measured_requests":18,
"orders":[["BASE_A","BASE_B","BULK1"],["BASE_B","BULK1","BASE_A"],["BULK1","BASE_A","BASE_B"]],
"input_order":"Two inputs swap by session parity; each input sees each arm order once",
"window":"Full fresh-context service incl both prefills, generation, host work, state/sync/teardown; excludes shared model load and postrequest comparisons/disk",
"controls":"BASE_A/B identical original QB threads8. Candidate also threads8. No new R arm; no new draft-vs-target-only claim."},
"analysis":{"primary":"Equal-input geometric mean of paired BULK1 / mean(BASE_A,BASE_B) service ratios, over3 sessions",
"screen":"All historical bytes pass; reduction>max(2percent,largest per-input aggregate absolute A/A imbalance), candidate lower in all3 session aggregates",
"scope":"Two exposed inputs,one machine/date,bounded software screen; no CI, no outlier deletion, no generality claim"},
"stop":"First native/support/reference failure stops this candidate; no timing of failed candidate. Preserve raw and failure.",
"execution":{"new_cap_seconds":1800,"old_cumulative_seconds":total,"qualification_deadline":180,"timing_deadline":300,"reserved_max":1690,"no_actor_RTL_CPU8":True}}
(r/"PREREGISTRATION.json").write_text(json.dumps(pr,indent=2))
s=(c/"RUN.ps1").read_text().replace("C:/hs/b570-draft-cpu-20261020","C:/hs/b570-draft-prefill-submit-20261020")
s=s.replace("C:/hs/b570-formal-request-20261020/BUDGET_LEDGER.json","C:/hs/b570-draft-cpu-20261020/BUDGET_LEDGER.json")
s=s.replace("1817.8040152",repr(total)).replace("B570_DRAFT_CPU_POLICY_V1","B570_DRAFT_PREFILL_SUBMISSION_V1")
s=s.replace("ValidateRange(0,7)","ValidateRange(0,6)").replace("3600","1800").replace("else{600}","else{300}").replace("build/Release/draft_cpu.exe","build/Release/prefill_submit.exe")
(r/"RUN.ps1").write_text(s)
s=(c/"recheck.py").read_text().replace('assert x["draft_cpu_threads"]==1','assert x["draft_prefill_api_calls"]==1 and x["draft_prefill_q_observed"]==1 and x["draft_microbatch_limit"]==1')
s=s.replace("draft_cpu_threads=1","draft_prefill_api_calls=1,physical_prefill_q=x['draft_prefill_q_observed']")
(r/"recheck.py").write_text(s)
s=(c/"freeze.py").read_text().replace('"draft_cpu.cpp"','"prefill_submit.cpp"')
(r/"freeze.py").write_text(s)
print("Registered independent submission-batching study; prior accounting preserved:",total)
