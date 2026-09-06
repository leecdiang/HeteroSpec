import os
import json
from pathlib import Path
import pandas as pd

ROOT=Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
TRACE=ROOT/r"telemetry\paper_power_window_canary_20260907T000743\intel_socwatch.json"
RESULT=ROOT/r"logs\paper-power-canary-q469.json"
NVML=ROOT/r"telemetry\phase4_specbench_pilot_nvml_20260907T000754.csv"
CAPTURE_START=pd.Timestamp("2026-09-07T00:07:45.4669854+08:00").tz_convert("UTC")
events=json.loads(TRACE.read_text())
pkg=[e for e in events if e.get("name")=="PKG-PWR"]
t0=min(e["ts"] for e in pkg)
intel=pd.DataFrame({"timestamp":[CAPTURE_START+pd.to_timedelta((e["ts"]-t0)/1e6,unit="s") for e in pkg],
                    "cpu_pkg_W":[next(iter(e["args"].values()))/1000 for e in pkg]})
intel=intel[intel.cpu_pkg_W>0]
nv=pd.read_csv(NVML); nv["timestamp"]=pd.to_datetime(nv.timestamp,utc=True)
result=json.loads(RESULT.read_text())
rows=[]
for c in result["questions"][0]["configs"]:
 for t in c["turns"]:
  start=pd.Timestamp(t["timestamp_start"]); end=pd.Timestamp(t["timestamp_end"])
  ni=intel[(intel.timestamp>=start)&(intel.timestamp<=end)]
  ng=nv[nv.run_id==t["run_id"]]
  duration=(end-start).total_seconds()
  rows.append({"run_id":t["run_id"],"config":c["config"],"duration_s":duration,"output_tokens":t["output_tokens"],
   "cpu_samples":len(ni),"cpu_pkg_avg_W":ni.cpu_pkg_W.mean(),"cpu_pkg_peak_W":ni.cpu_pkg_W.max(),"cpu_pkg_energy_J":ni.cpu_pkg_W.mean()*duration,
   "rtx_samples":len(ng),"rtx_avg_W":ng.power_W.mean(),"rtx_peak_W":ng.power_W.max(),"rtx_energy_J":ng.power_W.mean()*duration,
   "rtx_J_per_token":ng.power_W.mean()*duration/t["output_tokens"]})
out=pd.DataFrame(rows); out.to_csv(ROOT/r"analysis\joint_power_canary_summary.csv",index=False)
print(out.to_string(index=False))
