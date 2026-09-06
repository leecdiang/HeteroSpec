import os
from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt
R=Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1])); A=R/'analysis'; F=R/'reports'/'figures'; F.mkdir(parents=True,exist_ok=True)
custom=pd.read_csv(A/'paper_power_8b_custom_12q_runs.csv'); native=pd.read_csv(A/'paper_power_8b_native_12q_runs.csv')
groups=[]
for label,df,cfg in [('RTX baseline',custom,'B0'),('CPU→RTX custom',custom,'SPEC-k1'),('RTX→RTX native',native,'C-RTX-assisted-k1')]:
 x=df[df.config==cfg]; groups.append({'config':label,'tok_s':x.tok_s.mean(),'rtx_W':x.rtx_avg_W.mean(),'cpu_W':x.cpu_pkg_avg_W.mean(),'rtx_J_tok':x.rtx_J_per_token.mean(),'cpu_J_tok':(x.cpu_pkg_energy_J/x.output_tokens).mean()})
g=pd.DataFrame(groups); g.to_csv(A/'paper_power_summary.csv',index=False)
fig,axs=plt.subplots(1,3,figsize=(12,4)); colors=['#4e79a7','#e15759','#59a14f']
for ax,col,title in zip(axs,['tok_s','rtx_W','rtx_J_tok'],['Throughput','RTX average power','RTX energy per token']): ax.bar(g.config,g[col],color=colors); ax.set_title(title); ax.set_ylabel({'tok_s':'tok/s','rtx_W':'W','rtx_J_tok':'J/token'}[col]); ax.tick_params(axis='x',rotation=20)
fig.tight_layout(); fig.savefig(F/'figure5_power_energy.png',dpi=220); fig.savefig(F/'figure5_power_energy.pdf'); plt.close(fig)
sym=pd.DataFrame([['CPU',32,95.67],['CPU',64,94.41],['CPU',128,93.08],['GPU.0',32,67.27],['GPU.0',64,66.44],['GPU.0',128,64.82],['NPU',32,31.46],['NPU',64,31.46],['NPU',128,31.45]],columns=['device','input_tokens','tok_s'])
fig,ax=plt.subplots(figsize=(7,4.3))
for dev,x in sym.groupby('device'): ax.plot(x.input_tokens,x.tok_s,'o-',label=dev)
ax.set(xticks=[32,64,128],xlabel='Input tokens (same symmetric INT4 artifact)',ylabel='Output tok/s',title='Intel draft-device characterization'); ax.legend(); fig.tight_layout(); fig.savefig(F/'figure7_draft_device_characterization.png',dpi=220); fig.savefig(F/'figure7_draft_device_characterization.pdf'); plt.close(fig)
print(g.to_string(index=False))
