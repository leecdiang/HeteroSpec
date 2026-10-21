from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
r=Path(__file__).parent
a=json.loads((r/"ANALYSIS.json").read_text())
plt.rcParams.update({"font.size":10,"svg.fonttype":"none","axes.spines.top":False,"axes.spines.right":False})
fig,axs=plt.subplots(1,2,figsize=(11.5,4.3),layout="constrained")
ids=[x["input_id"]for x in a["per_input"]]
offsets=[-.18,-.06,.06,.18]
for i,name in enumerate(ids):
    p=[x for x in a["paired_blocks"]if x["input_id"]==name]
    for j,x in enumerate(p):
        axs[0].scatter(i+offsets[j],100*(x["service_QB_over_dualPQ"]-1),s=30,color="#126a9b",label="QB / dual-PQ, paired session"if i==j==0 else None)
        axs[0].scatter(i+offsets[j],100*(x["service_PQA_over_PQB"]-1),s=25,marker="x",color="#888888",label="PQ_A / PQ_B control"if i==j==0 else None)
        axs[1].scatter(i+offsets[j],x["service_QB_over_R"],s=30,color="#126a9b")
    avg=a["per_input"][i]
    axs[0].scatter(i,100*(avg["service_QB_over_dualPQ"]-1),marker="D",s=55,color="#b34f00",zorder=5,label="Per-input geometric mean"if i==0 else None)
    axs[1].scatter(i,avg["service_QB_over_R"],marker="D",s=55,color="#b34f00",zorder=5)
axs[0].axhline(0,color="#444444",lw=.8)
axs[0].axhline(-2,color="#999999",lw=.8,linestyle="--",label="2% practical screen")
axs[1].axhline(1,color="#444444",lw=.8)
axs[0].set_title("Layout effect and identical-code control")
axs[0].set_ylabel("Service cost difference (%) • lower is better")
axs[1].set_title("Speculative request vs target-only")
axs[1].set_ylabel("QB / target-only service ratio")
for ax in axs:
    ax.set_xticks(range(4),[x.replace("HumanEval/","HE/")for x in ids])
    ax.grid(axis="y",alpha=.2)
axs[0].legend(fontsize=8,loc="best")
fig.suptitle("B570: four reference-qualified inputs, four process sessions\nFresh-context service after registered warmup; fixed panel, no population confidence interval",fontsize=12)
for suffix in ("png","svg","pdf"):
    fig.savefig(r/f"REQUEST_COST_PANEL.{suffix}",dpi=180)
print("Wrote PNG/SVG/PDF from all16 paired blocks.")
