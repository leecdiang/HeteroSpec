from pathlib import Path
r=Path(__file__).parent;p=Path("C:/hs/b570-formal-request-20261020")
s=(p/"analyze_timing.py").read_text().replace("PQA_over_PQB","BASEA_over_BASEB").replace("PQ_A","BASE_A").replace("PQ_B","BASE_B").replace("QB","DRAFT1").replace("dualPQ","dualBASE")
s=s.replace('ref=read(r/f"qual-{i}/result.json")["requests"][0 if x["label"]=="R"else 1]',
    'ref=read(Path("C:/hs/b570-formal-request-20261020")/f"qual-{i}/result.json")["requests"][0 if x["label"]=="R"else 2]')
s=s.replace('if x["label"]!="R":assert x["cycles"]==ref["cycles"]',
    'if x["label"]!="R":assert x["cycles"]==ref["cycles"]\n        assert x["draft_cpu_threads"]==(1 if x["label"]=="DRAFT1"else 8)')
assert 'else 2]'in s
(r/"analyze_timing.py").write_text(s)
print("Prepared preregistered estimator with original PR134 reference")
