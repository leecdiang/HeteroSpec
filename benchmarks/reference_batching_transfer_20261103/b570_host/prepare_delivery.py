"""Snapshot the completed evidence and specialize the previous delivery format."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path("I:/HeteroSpec/b570-qwen-transfer-20261103")
REPO=Path(__file__).resolve().parents[3]
PR163="10a70566ce01ab707dbdcc57d8270c1434088f07"
LLAMA=Path("I:/HeteroSpec/b570-llama-20261102")
OLD=Path("C:/hs/b570-producer-consumer-20261028")
def read(p):
    return json.loads(p.read_text(encoding="utf-8"))
def write(p,x):
    with p.open("x",encoding="utf-8") as f:json.dump(x,f,indent=2);f.write("\n")
def sha(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
def previous(name):
    return subprocess.check_output(["git","show",PR163+":scripts/experiments/b570_llama_execution_v1/"+name],cwd=REPO).decode("utf-8")
def unique_replace(s,a,b):
    assert s.count(a)==1
    return s.replace(a,b,1)
def prepare():
    assert read(ROOT/"COST.json")["status"]=="ALL_120_FIXED_PAIRS_RECONSTRUCTED"
    assert not Path("C:/hs/b570-llama-exclusive.lock").exists()
    repro=ROOT/"repro";repro.mkdir()
    shutil.copytree(REPO/"scripts/b570_qwen_transfer",repro/"b570_qwen_transfer",ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO/"src/reference_batching",repro/"reference_batching",ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(Path(__file__).with_name("recompute.py"),repro/"recompute.py")
    shutil.copyfile(Path(__file__),repro/"prepare_delivery.py")
    kit=Path("C:/hs/b570-llama-results/scripts/experiments/b570_llama_companion_v1")
    for name in ("CMakeLists.txt","worker.cpp","companion_scope.cpp","companion_scope.hpp","cycle.hpp"):
        p=repro/"llama_companion"/name;p.parent.mkdir(exist_ok=True);shutil.copyfile(kit/name,p)
    shutil.copyfile(LLAMA/"oracle-01/supervisor.py",repro/"supervisor.py")
    exposure=repro/"exposure";exposure.mkdir()
    for src in (LLAMA/"EXPOSURE_AUDIT-00.json",LLAMA/"research/EXPOSURE.jsonl",LLAMA/"UNSEEN_PANEL-00.json",LLAMA/"natural-source-00/SOURCES.json",OLD/"selection-final/TOKENIZATION.json"):
        shutil.copyfile(src,exposure/src.name)
    imports=ROOT/"historical/import-libraries";imports.mkdir()
    lib=Path("C:/hs/b570-native-reproduction-20261026/build/runtime")
    for p in (lib/"src/Release/llama.lib",lib/"ggml/src/Release/ggml-base.lib",lib/"ggml/src/Release/ggml.lib"):shutil.copyfile(p,imports/p.name)
    archive=unique_replace(previous("object_archive.py"),"if 'build' in parts:","if 'build' in parts or parts[0] in ('build-00','build-01'):")
    archive=unique_replace(archive,"('.dll','.exe','.log','.json','.cmd')","('.dll','.exe','.lib','.log','.json','.cmd')")
    archive=archive.replace("b570-llama-native-evidence","b570-qwen-transfer-native-evidence")
    (repro/"object_archive.py").write_text(archive,encoding="utf-8",newline="\n")
    publisher=previous("publish_delivery.py").replace("B570 Llama companion native evidence","B570 Qwen structural transfer evidence").replace("Independent B570 PR163","Independent B570 PR165")
    publisher=unique_replace(publisher,"'independent_qualification.py','independent_cost.py','independent_ledger.py'","'recompute.py'")
    publisher=unique_replace(publisher,"from recover_exposure_index import SafeRedirect","from recover_release import SafeRedirect")
    (repro/"publish_delivery.py").write_text(publisher,encoding="utf-8",newline="\n")
    redirect=subprocess.check_output(["git","show",PR163+":scripts/experiments/b570_llama_companion_v1/recover_release.py"],cwd=REPO)
    (repro/"recover_release.py").write_bytes(redirect)
    attempts=[]
    for p in sorted((ROOT/"units").rglob("SUPERVISOR.json")):
        s=read(p);native=read(p.parent/"native/result.json");assert s["job_accounting"]["active_processes"]==0
        requests=len(native.get("requests",native.get("records",[])))
        teacher=native.get("probe_runs",[])
        attempts.append(dict(unit=p.parent.relative_to(ROOT).as_posix(),status=native["status"],process_seconds=s["charged_seconds"],completed_requests=requests,teacher_forced_sequences=len(teacher),probe_pairs=sum(len(x["calls"]) for x in teacher),receipt_sha256=sha(p)))
    write(ROOT/"CUMULATIVE.json",dict(attempts=attempts,completed_model_requests=sum(x["completed_requests"] for x in attempts),native_process_seconds=sum(x["process_seconds"] for x in attempts),failed_units=[x["unit"] for x in attempts if x["status"]=="STOPPED_FIRST_FAILURE"],teacher_forced_sequences=sum(x["teacher_forced_sequences"] for x in attempts),open=[]))
    write(repro/"SNAPSHOT.json",dict(freeze=sha(ROOT/"FREEZE.json"),source_commit=read(ROOT/"FREEZE.json")["source_commit"],files=[dict(path=p.relative_to(repro).as_posix(),sha256=sha(p)) for p in sorted(repro.rglob("*")) if p.is_file()]))
if __name__=="__main__":prepare()

