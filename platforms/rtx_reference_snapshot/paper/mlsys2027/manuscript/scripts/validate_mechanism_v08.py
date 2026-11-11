"""Offline manuscript v0.8 checks. Does not execute models or rewrite closed evidence."""
from pathlib import Path
import hashlib, json, re, subprocess
from pypdf import PdfReader

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
E = HERE.parent / "evidence"
B = ROOT / "benchmarks/b570_mechanism_v08"
checks = []

def check(name, condition):
    assert condition, name
    checks.append(name)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

close = read(B / "CLOSEOUT_REPORT.json")
analysis = read(B / "VALIDATION_ANALYSIS.json")
independent = read(B / "INDEPENDENT_VALIDATION.json")
portable = read(B / "PORTABLE_VALIDATION.json")
extracted = read(B / "EXTRACTED_ARCHIVE_VALIDATION.json")
freeze = read(B / "hypothesis_freeze.json")
check("H1 selected", close["selected_mechanism"] == "H1" and freeze["status"] == "H1_SELECTED")
check("harness 90/90", close["harness_qualification"] == "PASS 90/90")
check("discovery 36/36", close["discovery_predictor_agreement"] == "36/36")
check("24 reserved prompts", close["reserved_prompts"] == 24 and len(close["reserved_set"]) == 24)
check("144 reference/predictor executions", close["predictor_reference_executions"] == 144)
check("72 frozen prediction arrays", close["reserved_prediction_commit"] == "c99aaf2082ffff46741bef6f69dd96b4654d4c08" and close["live_serialized_executions"] == 72)
check("72/72 complete sequences", analysis["status"] == "MECHANISM_PREDICTION_VALIDATED" and (analysis["exact_sequences"], analysis["denominator"]) == (72, 72))
check("24/24 prompt classification", (analysis["prompt_classification_matches"], analysis["prompt_denominator"]) == (24, 24))
check("12/12 divergence indices", (analysis["first_divergence_exact_pairs"], analysis["actual_mismatching_pairs"]) == (12, 12))
check("4/4 divergent prompts", (analysis["first_divergence_exact_prompts"], analysis["actual_mismatching_prompts"]) == (4, 4))
q = analysis["qualification_prediction"]
check("reserved predicted/actual 60/72 BLOCKED", (q["predicted_reference_exact_pairs"],q["actual_reference_exact_pairs"],q["denominator"]) == (60,60,72) and "BLOCKED" in q["predicted_status"] and "BLOCKED" in q["actual_status"])
check("freeze chronology and no retuning", close["hypothesis_freeze_commit"] == "313069ce5ac10d4d31849f515c912cad29ac7360" and not any(close[k] for k in ("parameters_changed_after_hypothesis_freeze","reserved_inference_before_hypothesis_freeze","predictions_changed_after_outcome_start")))
check("exposure audit", close["exposure_audit"] == {"exposed":31,"eligible":133,"errors":0})
check("independent validator 5681", independent["status"] == "PASS" and independent["checks_passed"] == 5681)
check("portable and extracted archive receipts", portable["status"] == "PASS" and extracted["status"] == "PASS")
check("no performance/energy runs", not close["performance_experiment"] and not close["energy_experiment"])
divergent = {"HumanEval/134":88,"HumanEval/42":73,"HumanEval/145":103,"HumanEval/138":93}
found = {}
for pair in analysis["pairs"]:
    actual = pair["actual_relative_to_reference"]
    pred = pair["predicted_relative_to_reference"]
    check("pair prediction " + pair["task_id"] + "/" + str(pair["repetition"]), pair["primary"]["exact"] and actual == pred)
    if not actual["exact"]: found[pair["task_id"]] = actual["first_divergence_index"]
check("four divergence fingerprints", found == divergent)

sources = {p.name:p.read_text() for p in (HERE / "sections").glob("*.tex")}
check("abstract reports 72", "predicts all 72 serialized output sequences" in (HERE/"main.tex").read_text())
check("Section 5 H1 chronology", all(x in sources["05_diagnoses.tex"] for x in ("36/36", "72/72", "24/24", "12/12", "60/72", "before any live serialized outcome")))
check("negative Guard retained", "Guard had higher latency on this comparison" in sources["07_runtime_codesign.tex"])
check("B570 mechanism scoped", "neither identifies a specific kernel" in sources["09_limitations.tex"])
check("old Figure 3 bytes", subprocess.check_output(["git","hash-object",str(HERE/"figures/presentation_v07/pdf/verification.pdf")]).decode().strip() == "9318a7d27f06c243c734a188fb1261a8ce00a5cc")

pdfs = {}
for name, expected in (("manuscript",11),("appendix",6),("hardware-only",10)):
    path = HERE/"output"/(name+"-v0.8.pdf")
    r = PdfReader(path); text = "\n".join(p.extract_text() or "" for p in r.pages)
    check(name+" pages", len(r.pages) == expected)
    check(name+" anonymous", "Anonymous" in str(r.metadata) and not re.search(r"leecdiang|/Users/|C:\\|D:\\|HeteroSpec",text+str(r.metadata),re.I))
    check(name+" no unresolved", "??" not in text)
    fonts = subprocess.check_output(["pdffonts",str(path)],text=True)
    check(name+" embedded fonts", all(line.split()[-3] == "yes" for line in fonts.splitlines()[2:] if line.strip()))
    pdfs[name] = {"pages":len(r.pages),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
for name in ("main","appendix","hardware-only-v0.8"):
    log=HERE/"build"/(name+".log")
    check(name+" TeX log", log.exists() and not re.search(r"Overfull|undefined references|Citation .* undefined|LaTeX Error",log.read_text(errors="replace")))
aux=(HERE/"build/main.aux").read_text()
check("ten body pages", re.search(r"\\newlabel\{maintextend\}\{\{[^}]*\}\{10\}",aux) is not None)

historical = {"numerical":228,"runtime":136,"M4_paired_secondary":638,"direct_ID_integration":2459,"Figure_3":67}
check("v0.7 numerical receipt", read(E/"NUMERICAL_QA_V07.json")["count"] == historical["numerical"])
runtime = read(E/"RUNTIME_QA_V07.json")
check("v0.7 runtime receipt", runtime["existing_runtime_checks"]+runtime["new_secondary_checks"] == historical["runtime"])
check("v0.7 secondary receipt", read(E/"DIRECT_ID_M4_SECONDARY_REPLAY_V07.json")["check_count"] == historical["M4_paired_secondary"])
v07=read(E/"DIRECT_ID_INTEGRATION_QA_V07.json")
check("v0.7 direct-ID and Figure 3 receipts", (v07["check_count"],v07["figure"]["check_count"]) == (2459,67))

receipt={"status":"PASS","checks_run":len(checks),"checks":checks,"historical_receipts_verified_not_rerun":historical,"archive_verifier_not_rerun":"The 87 MB content-addressed archive was unavailable through the GitHub connector; checked its committed independent/portable receipts, not a fresh archive replay.","pdfs":pdfs,"main_body_pages":10,"new_inference":False,"closed_evidence_modified":False}
(E/"MECHANISM_INTEGRATION_QA_V08.json").write_text(json.dumps(receipt,indent=2)+"\n")
print("v0.8 offline checks PASS:",len(checks))
