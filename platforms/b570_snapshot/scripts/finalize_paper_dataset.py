import os
from pathlib import Path
import numpy as np, pandas as pd
R=Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1])); A=R/'analysis'
base=pd.read_csv(A/'all_runs.csv')
parts=[]
for fn,pair,target in [('paper_power_8b_custom_12q_runs.csv','Qwen3-0.6B->Qwen3-8B','8B'),('paper_power_8b_native_12q_runs.csv','Qwen3-0.6B->Qwen3-8B','8B')]:
 d=pd.read_csv(A/fn); d['model_pair']=pair; d['target_size']=target; d['k']=np.where(d.config.str.contains('k1'),1,np.nan); d['valid']=d.exact_match.fillna(True); d['source_file']=fn; parts.append(d)
new=pd.concat(parts,ignore_index=True)
for c in base.columns:
 if c not in new:new[c]=np.nan
combined=pd.concat([base,new[base.columns]],ignore_index=True)
combined.to_csv(A/'all_runs.csv',index=False)

power=pd.read_csv(A/'all_power_1s.csv'); power['power_domain']='NVIDIA_RTX'; power['experiment']=power.get('experiment','')
intel=[]
for f in A.glob('paper_power_*_intel_power_1s.csv'):
 d=pd.read_csv(f); d=d.rename(columns={'cpu_pkg_avg_W':'power_W','cpu_pkg_peak_W':'power_peak_W'}); d['power_domain']='INTEL_CPU_PACKAGE'; d['source_file']=f.name; d['run_id']=''; intel.append(d)
cols=sorted(set(power.columns).union(*(set(x.columns) for x in intel)))
for d in [power,*intel]:
 for c in cols:
  if c not in d:d[c]=np.nan
pd.concat([power[cols],*(x[cols] for x in intel)],ignore_index=True).to_csv(A/'all_power_1s.csv',index=False)
print({'all_runs':len(combined),'all_power_1s':sum(1 for _ in open(A/'all_power_1s.csv',encoding='utf-8'))-1})
