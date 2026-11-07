"""Independent probe entrypoint linked to the unmodified PR166 static archives."""
import json
import shutil
import subprocess
import time
from build import BASE, HERE, OUT
ROOT=OUT.parent/"oracle01"
ROOT.mkdir(exist_ok=True)
for f in (BASE/"bin").glob("*.dll"):
    if not (ROOT/f.name).exists(): shutil.copy2(f, ROOT/f.name)
for row in json.loads((BASE/"COMMANDS.json").read_bytes()):
    if row["label"] not in ("worker","link"): continue
    cmd=[s.replace(str(BASE/"worker.cpp"),str(HERE/"probe.cpp")).replace(str(BASE/"worker.obj"),str(ROOT/"oracle.obj")).replace(str(BASE/"bin/rtx-scope-transfer.exe"),str(ROOT/"probe.exe")) for s in row["argv"]]
    if row["label"]=="worker": cmd.insert(2,"-DTPDS_ORACLE")
    with (ROOT/f'{row["label"]}-{time.time_ns()}.log').open("xb") as log:
        subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)

