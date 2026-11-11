from pathlib import Path
r=Path(__file__).parent;p=Path("C:/hs/b570-formal-request-20261020")
s=(p/"stage_analysis.py").read_text(encoding="utf-8").replace("PQ_A","BASE_A").replace("PQ_B","BASE_B").replace("QB","DRAFT1").replace("target_verify_PQ","target_verify_BASE")
s=s.replace('(r/"STAGE_SUMMARY.json").write_text', '''out["draft_prefill_BASE_seconds"]=statistics.mean(out["arms"][x]["phases"]["draft_PREFILL"]for x in ("BASE_A","BASE_B"))
out["draft_prefill_DRAFT1_seconds"]=out["arms"]["DRAFT1"]["phases"]["draft_PREFILL"]
out["draft_prefill_reduction"]=1-out["draft_prefill_DRAFT1_seconds"]/out["draft_prefill_BASE_seconds"]
(r/"STAGE_SUMMARY.json").write_text''')
(r/"stage_analysis.py").write_text(s,encoding="utf-8")
s=(p/"plot_results.py").read_text(encoding="utf-8").replace("PQA_over_PQB","BASEA_over_BASEB").replace("PQ_A","BASE_A").replace("PQ_B","BASE_B").replace("QB","DRAFT1").replace("dualPQ","dualBASE").replace("dual-PQ","dual-BASE")
s=s.replace("Layout effect and identical-code control","Draft CPU policy and identical-code control")
s=s.replace("Speculative request vs target-only","Candidate request vs target-only")
s=s.replace("B570: four reference-qualified inputs, four process sessions","B570 draft CPU threads 8 to 1: fixed-input reference-qualified costs")
(r/"plot_results.py").write_text(s,encoding="utf-8")
s=(p/"package.py").read_text(encoding="utf-8").replace("b570_formal_request_v1","b570_draft_cpu_policy_v1")
(r/"package.py").write_text(s,encoding="utf-8")
s=(p/"verify_delivery.py").read_text(encoding="utf-8").replace("PQ_A","BASE_A").replace("PQ_B","BASE_B").replace("QB","DRAFT1").replace("dualPQ","dualBASE").replace("401.2123575","1817.8040152")
s=s.replace('ref["requests"][0 if x["label"]=="R"else 1]','ref["requests"][0 if x["label"]=="R"else 2]')
(r/"verify_delivery.py").write_text(s,encoding="utf-8")
print("Prepared phase summary, figure and archive generators")
