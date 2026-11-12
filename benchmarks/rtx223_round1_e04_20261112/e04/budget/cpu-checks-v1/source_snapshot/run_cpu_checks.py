"""Only new e04 planner/fault-injection tests; never old suites or GPU work."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
OUT=HERE/(sys.argv[1] if len(sys.argv)>1 else "cpu-checks-v1")
OUT.mkdir(exist_ok=False)
runs=[]
for flags,name in (([],"ordinary"),(["-O"],"optimized")):
    argv=[sys.executable,"-B",*flags,"-m","unittest","discover","-s",str(HERE),"-p","test_lifecycle_budget.py","-v"]
    env=os.environ.copy();env["HS_E04_KEEP_ROOT"]=str(OUT/"raw"/name)
    r=subprocess.run(argv,cwd=HERE,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (OUT/(name+".log")).write_bytes(r.stdout)
    count=re.findall(rb"Ran (\d+) tests?",r.stdout)
    runs.append({"argv":argv,"exit_code":r.returncode,"tests":int(count[-1]) if count else None,
                 "log_sha256":hashlib.sha256(r.stdout).hexdigest()})
receipt={"schema":"heterospec.e04.lifecycle-planner.cpu-checks.v1","utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "scope":"CPU_MOCK_ONLY_NOT_NATIVE_KERNEL_INTERCEPTION","runs":runs,"all_pass":all(r["exit_code"]==0 for r in runs),
         "sources":{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ("lifecycle_budget.py","test_lifecycle_budget.py","run_cpu_checks.py")},
         "old_suites_repeated":False,"numeric_DLL_loads":0,"CUDA_calls":0,"model_requests":0,"target_draft_rows":0,
         "GPU_launches":0,"physical_GPU_observations":"NOT_RUN","production_gate":"BLOCKED_EMPTY_TRUSTED_PROOF_REGISTRY",
         "canonical_production_ledger_writes":0}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2),encoding="utf8")
print(json.dumps(receipt))
if not receipt["all_pass"]: raise SystemExit(1)
