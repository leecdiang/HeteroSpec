"""Static summary of exact task-level RTX bridge comparisons; no fitted quantities."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'ps.fonttype':42})
fig=plt.figure(figsize=(6.75,2.05));ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,6.75);ax.set_ylim(0,2.05);ax.axis('off')
ink='#222222';blue='#4C6E9E';gray='#777777'
ax.text(.02,1.87,'Matched RTX bridge: reference agreement',fontsize=10,fontweight='bold',color=ink)
cols=[1.72,2.32,2.92]
for x,c in zip(cols,['N0','N1','U2']):ax.text(x+.19,1.56,c,ha='center',fontweight='bold',color=ink)
rows=[('16 controls',[1,1,1]),('HumanEval/15',[0,1,1]),('HumanEval/25',[1,0,0]),('HumanEval/18',[0,0,0])]
for i,(lab,vals) in enumerate(rows):
 y=1.27-i*.29;ax.text(.04,y+.035,lab,va='center',color=ink)
 for x,v in zip(cols,vals):
  ax.add_patch(Rectangle((x,y-.045),.38,.16,facecolor=blue if v else 'white',edgecolor=blue if v else gray,linewidth=.8))
ax.plot([3.67,3.67],[.28,1.8],color='#D9DDE3',lw=.9)
ax.text(3.94,1.65,'Complete-output comparisons',fontweight='bold',fontsize=10,color=ink)
ax.text(3.94,1.20,'U2 = N1',color=ink);ax.text(6.55,1.20,'19 / 19 tasks',ha='right',fontweight='bold',color=blue)
ax.text(3.94,.84,'U2 = N0',color=ink);ax.text(6.55,.84,'17 / 19 tasks',ha='right',color=ink)
ax.text(3.94,.43,'Three stable observations per task',fontsize=8,color=gray)
ax.add_patch(Rectangle((.04,.06),.2,.12,facecolor=blue,edgecolor=blue));ax.text(.31,.12,'Reference match',va='center',fontsize=8,color=ink)
ax.add_patch(Rectangle((1.83,.06),.2,.12,facecolor='white',edgecolor=gray));ax.text(2.10,.12,'Reference mismatch',va='center',fontsize=8,color=ink)
fig.savefig(ROOT/'figures/integration_v011/bridge_summary.pdf',metadata={'Creator':'Matplotlib','Author':'','Title':'Matched RTX bridge comparisons','CreationDate':None,'ModDate':None})
fig.savefig(ROOT/'figures/integration_v011/bridge_summary.png',dpi=220)
