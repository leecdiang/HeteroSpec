import os
import argparse, json, re
from pathlib import Path
import numpy as np
import pandas as pd

p=argparse.ArgumentParser(); p.add_argument('--session',required=True); p.add_argument('--result',required=True); p.add_argument('--capture-log',required=True); p.add_argument('--label',required=True); a=p.parse_args()
root=Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1])); session=Path(a.session); result=json.loads(Path(a.result).read_text(encoding='utf-8'))
text=Path(a.capture_log).read_text(encoding='utf-8',errors='ignore')
capture_start=pd.Timestamp(re.search(r'capture_start=([^\r\n]+)',text).group(1)).tz_convert('UTC')
events=json.loads((session/'intel_socwatch.json').read_text(encoding='utf-8'))
pkg=[e for e in events if e.get('name')=='PKG-PWR']; t0=min(e['ts'] for e in pkg)
intel=pd.DataFrame({'timestamp':[capture_start+pd.to_timedelta((e['ts']-t0)/1e6,unit='s') for e in pkg],
 'cpu_pkg_W':[next(iter(e['args'].values()))/1000 for e in pkg]})
intel=intel[intel.cpu_pkg_W>0].set_index('timestamp').sort_index()
bins=intel.resample('1s').cpu_pkg_W.agg(['mean','max','count']).reset_index().rename(columns={'mean':'cpu_pkg_avg_W','max':'cpu_pkg_peak_W','count':'raw_samples'})
bins['experiment']=a.label; bins['alignment']='trace_first_sample_mapped_to_capture_start'
bins.to_csv(root/'analysis'/f'{a.label}_intel_power_1s.csv',index=False)
nv=pd.read_csv(result['nvml_csv']); nv['timestamp']=pd.to_datetime(nv.timestamp,utc=True)
rows=[]
for q in result['questions']:
 for c in q['configs']:
  for t in c['turns']:
   start=pd.Timestamp(t['timestamp_start']); end=pd.Timestamp(t['timestamp_end']); dur=(end-start).total_seconds()
   ni=intel[(intel.index>=start)&(intel.index<=end)].cpu_pkg_W; ng=nv[nv.run_id==t['run_id']]
   rounds=t.get('rounds') or []; offered=sum(x.get('offered',0) for x in rounds); accepted=sum(x.get('accepted',0) for x in rounds)
   rows.append({'run_id':t['run_id'],'experiment':a.label,'prompt_id':q['question_id'],'task':q['category'],'config':c['config'],
    'input_tokens':t['input_tokens'],'output_tokens':t['output_tokens'],'completion_ms':dur*1000,'tok_s':t['output_tokens']/dur,
    'acceptance':accepted/offered if offered else np.nan,'draft_tokens':offered,'accepted_tokens':accepted,'verification_rounds':len(rounds),
    'draft_ms':sum(x.get('draft_ms',0) for x in rounds) or np.nan,'verify_ms':sum(x.get('target_ms',0) for x in rounds) or np.nan,
    'cpu_samples':len(ni),'cpu_pkg_avg_W':ni.mean(),'cpu_pkg_peak_W':ni.max(),'cpu_pkg_energy_J':ni.mean()*dur,
    'rtx_samples':len(ng),'rtx_avg_W':ng.power_W.mean(),'rtx_peak_W':ng.power_W.max(),'rtx_energy_J':ng.power_W.mean()*dur,
    'rtx_J_per_token':ng.power_W.mean()*dur/t['output_tokens'],'rtx_peak_vram_MB':ng.vram_used_MB.max(),'exact_match':c.get('exact_match_to_B0'),
    'intel_time_alignment':'trace_first_sample_mapped_to_capture_start'})
out=pd.DataFrame(rows); out.to_csv(root/'analysis'/f'{a.label}_runs.csv',index=False)
print(out.groupby('config').agg(runs=('run_id','count'),tok_s=('tok_s','mean'),cpu_W=('cpu_pkg_avg_W','mean'),rtx_W=('rtx_avg_W','mean'),rtx_J_tok=('rtx_J_per_token','mean')).to_string())
