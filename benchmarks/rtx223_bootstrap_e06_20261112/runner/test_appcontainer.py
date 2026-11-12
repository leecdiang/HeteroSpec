"""Independent CPU-only AppContainer and model-path-denial smoke; no profile or ACL changes."""
import datetime as dt
import json
from pathlib import Path
import sys

import runpy
HERE=Path(__file__).resolve().parent
h=runpy.run_path(str(HERE/"test_runner.py"))
r=h["r"]
w=r.win

def run(root):
    root.mkdir(parents=True,exist_ok=False)
    targets=r.protected_models()
    manifest=json.loads((HERE.parent/"build/DEPLOYMENT.json").read_bytes())
    image_paths=[Path(x["path"]) for x in manifest["modules"].values()]
    smoke={"scope":"CPU_APPCONTAINER_ONLY","runner_context":r.runner_context(),"package":r.PACKAGE,
           "observed_utc":w.utc(),"cpu_probe_sha256":h["DIGEST"],"protected_model_paths":len(targets),
           "readable_image_count":None,"principal_model_read_denied":False,
           "job_active_limit":1,"pass":False,"management_library_loads":0,"numerical_DLL_loads":0}
    log=r.Journal(root,{"scope":"CPU_APPCONTAINER_ONLY"})
    job=w.AtomicJob()
    try:
        h["yes"](r.code_digest(h["FAKE"].read_bytes())==h["DIGEST"],"CPU image identity")
        result=r.execute(job,log,h["MockObserver"](),[h["FAKE"]],h["FAKE"].parent,h["fixture_env"](),
                         "cpu-fake",work=5,hard=8,package=r.PACKAGE,protected=targets,readable_images=image_paths)
        smoke["pass"]=result=="COMPLETE" and job.active()==0
        if smoke["pass"]:
            smoke.update(principal_model_read_denied=True,readable_image_count=len(image_paths))
    except Exception as exc:
        smoke["error"]=str(exc)
    finally:
        job.close()
        log.close()
        (root/"APPCONTAINER_CPU.json").write_text(json.dumps(smoke,indent=2)+"\n",encoding="utf8")
    print(json.dumps(smoke,indent=2))
    return 0 if smoke["pass"] else 1

if __name__=="__main__":
    if len(sys.argv)!=2 or not sys.argv[1].isdecimal():
        raise SystemExit("use an unused numeric run ID")
    sys.exit(run(HERE/"cpu-checks"/("acl-"+sys.argv[1])))

