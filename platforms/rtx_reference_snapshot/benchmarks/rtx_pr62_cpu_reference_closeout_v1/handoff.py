"""Generate paper handoff/reports and static scientific SVG/PDF figures from CPU tables."""
import csv, json, math, platform
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).parent
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def put(p,s):(ROOT/p).write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
def main():
    summary=read('COST_SUMMARY.json');counts=read('COUNTS.json');verify=read('INDEPENDENT_VERIFICATION.json');ss=summary['comparisons']
    get=lambda b,c,t:next(x for x in ss if x['baseline']==b and x['candidate']==c and x['timer']==t)
    sc='target_scopes';r='scalar_reference';m='matched_target';g=get(r,sc,'generation');w=get(r,sc,'whole');mg=get(m,sc,'generation');mw=get(m,sc,'whole')
    header='|Baseline / candidate|Timer|Task-median GM|Descriptive95% interval|Faster/slower tasks|Round GM1/2/3/4|\n|---|---|---:|---|---|---|\n'
    fulltable=header+''.join(f"|{s['baseline']} / {s['candidate']}|{s['timer']}|{s['task_median_gm']:.9f}|[{s['descriptive_task_bootstrap_95_linear'][0]:.6f}, {s['descriptive_task_bootstrap_95_linear'][1]:.6f}]|{s['faster_tasks']}/{s['slower_tasks']}|"+'/'.join(f"{v['gm']:.6f}" for v in s['rounds'])+'|\n' for s in ss)
    primarytable=header+''.join(f"|{s['baseline']} / {s['candidate']}|{s['timer']}|{s['task_median_gm']:.9f}|[{s['descriptive_task_bootstrap_95_linear'][0]:.6f}, {s['descriptive_task_bootstrap_95_linear'][1]:.6f}]|{s['faster_tasks']}/{s['slower_tasks']}|"+'/'.join(f"{v['gm']:.6f}" for v in s['rounds'])+'|\n' for s in ss if s['primary'])
    paragraph=f"On an NVIDIA RTX 5070 Ti Laptop GPU with the frozen Qwen3-8B/0.6B Q8_0 CUDA configuration (greedy seed123, FA off, context4096, k3/UB4, cap128), the target-prefill-and-continuation attention constraint matched the complete saved scalar-reference response arrays and endpoints on all24 MBPP tasks in four repetitions. A post-hoc CPU reconstruction of the same384 measured requests, excluding16 warmups, found task-median geometric-mean speed ratios of {g['task_median_gm']:.5f} for the original server generation timer and {w['task_median_gm']:.5f} for resident whole-request latency against the measured ordinary UB1 scalar reference. Descriptive task-bootstrap95% intervals were [{g['descriptive_task_bootstrap_95_linear'][0]:.5f}, {g['descriptive_task_bootstrap_95_linear'][1]:.5f}] and [{w['descriptive_task_bootstrap_95_linear'][0]:.5f}, {w['descriptive_task_bootstrap_95_linear'][1]:.5f}], respectively; all four round geometric means were above one. Against the constrained draft-free matched target, the corresponding ratios were {mg['task_median_gm']:.5f} and {mw['task_median_gm']:.5f}, with a whole-request reversal in round2 ({mw['rounds'][1]['gm']:.5f}). The draft-free constrained target itself achieved R/matched ratios of1.00076 generation and1.68256 whole request. Consequently, the larger scalar-baseline request improvement combines numerical-path/prefill differences with speculation and cannot be attributed entirely to speculative verification. The panel is now exposed; reference lengths were11–128 tokens, and the result is neither a population guarantee nor a comparison against every ordinary decoder. No new model execution was performed."
    handoff=f'''# Paper evidence handoff: ordinary scalar-reference gap closed

Status: **READY_FOR_BOUNDED_MANUSCRIPT_RECONSTRUCTION**. This means the specific PR62 B strong-baseline gap is closed with authenticated raw CPU analysis and the late-study evidence can enter a separate manuscript reconstruction. It does not mean the whole manuscript has been integrated, compiled, externally reviewed or accepted. Preserve explicit evidence limits.

## Same-panel cost result

{primarytable}
Speed is baseline_ms/candidate_ms; >1 means candidate faster.24 task clusters, four paid repeats per path; distinct balanced resident processes within the same campaign, not simultaneous same-process measurements. See RAW_COSTS, TASK_COST_PAIRS and ROUND_COST_PAIRS for all absolute costs and reversals. The 10000-draw seed20261008 linear-quantile intervals are descriptive; historical4000-draw seed20261005 intervals are separately reproduced, not replaced.

## English result paragraph

{paragraph}

## What can be written

- Full saved response-array/endpoint qualification of allfour paths:96/96 requests per condition; stable reference24/24 tasks. No new recropping, functional-code claim or fuller unrecorded-stream certification.
- This measured constrained speculative path beats the measured ordinary UB1 reference on the frozen B panel in both timers, with allfour round directions positive.22/24 generation and24/24 whole-task median ratios are above1; the two generation slow tasks are retained.
- Matched-target speculative gain remains1.16924/1.03507. Generation is positive in allrounds; whole-request round2 is0.94022. Do not write every round/task gained against matched target.
- R/matched whole1.68256, generation1.00076 (descriptive interval straddles1). This prevents attributing the full1.74157 whole gain to speculation and prevents a unique component-cost explanation.
- RTX local qualification/scope ablation and C4's wider-k negative efficiency, and B570's scoped repair without ordinary-reference gain, remain evidence in their own contracts.

## What must be narrowed or excluded

The scalar comparison is appended post-hoc to already exposed records, not a new measurement or holdout. Ordinary R is the measured private qualified frontend with mask0/UB1/no draft, not globally optimal ordinary decode. Generation excludes first-sample/prompt time and some final bookkeeping; whole request excludes model load, warmup and shutdown. Single-client resident latency is not concurrency/throughput/energy. No universal losslessness, automatic constraint discovery, global minimal scope, unique kernel root cause, certified error bound, cross-model validity or calibrated publication probability follows.

## Claim mapping and manuscript order

CLAIM_EVIDENCE_MATRIX.csv binds exact commits, raw/derived scope, baselines, exposure and limits. Recommended order: problem and output contract → natural historical-state/current-path crosses → RTX local attention transformation and role/phase ablation → qualified cost against both ordinary R and matched target → width/history-state counterexamples → finite B570 transfer → M4/358H source-specific applicability boundaries. Put much of the early research history in the appendix.

The working empirical main line is: **historical numerical state and the current execution path jointly influence reference outputs; local numerical constraints alter the useful verification-parallelism space, whose value requires both output qualification and actual paid cost.** These are finite system findings, not a proven universal speculative algorithm. General acceleration from speculative decoding was already known; the new evidence concerns a qualified concrete constraint instance, natural-state diagnosis and measured operating boundaries.

## B570 and cross-platform scope

PR65 head8783cb1… is read at its frozen public source, not newly raw-audited here. Preserve its endpoint contract/raw-suffix distinction and strong-baseline negative result: R/candidate generation0.2825875535, whole0.2012895932 on15 complete paired tasks. E stays119/120 and PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED, with the missing old-N1 slot not imputed; B570_GPU_NEXT_ACTION=STOP. CPU audit completion does not make its original E matrix COMPLETE. This RTX handoff closes the deferred RTX raw-cost item without editing PR65.

CUDA/Vulkan provide finite transfer of the diagnostic design, not the same repair implementation/parameters/reference. The late mechanism evidence still concentrates in one Qwen3 model family. M4/358H retain their original source-specific contracts/timers/qualification; no comparable late state-cross evidence is asserted merely because costs exist.

## C4 evidence boundaries

PR62 C4 diagnostics include warmup in calls/micrographs; drafted/accepted and timing belong to a separate formal session. Keep305→199 caller calls and305→397 micrograph observations in the diagnostic scope, and3528→5392 drafted/2772→3192 accepted with0.829442 generation/0.889868 whole k7-vs-k3 in the formal scope. No cross-session divisions or attribution of all latency to a single counter are valid.

## Next authorized boundary

Next stage is evidence integration, manuscript reconstruction, compilation and reviewer-oriented audit. This CPU task does not perform that rewrite and does not request another equivalent closeout or new GPU campaign. PR61 v0.11 at4f343596… remains a baseline missing the late evidence.
'''
    put('PAPER_HANDOFF.md',handoff)
    with (ROOT/'CONDITION_TASK_MEDIANS.csv').open() as f:med=list(csv.DictReader(f))
    absolute='|Condition|Median across24 task medians: generation ms|Whole ms|\n|---|---:|---:|\n'
    for c in [r,m,sc,'all_scopes']:
        vals=lambda t:float(np.median([float(v['median_ms']) for v in med if v['condition']==c and v['timer']==t]))
        absolute+=f"|{c}|{vals('generation'):.6f}|{vals('whole'):.6f}|\n"
    with (ROOT/'TASK_COST_PAIRS.csv').open() as f:tp=list(csv.DictReader(f))
    slow=[p['task'] for p in tp if p['baseline']==r and p['candidate']==sc and p['timer']=='generation' and float(p['speedup_baseline_over_candidate'])<1]
    report=f'''# RTX普通参考成本闭环：CPU复算报告

本轮完成普通参考强基线缺口。固定target_scopes候选相对普通标量R，生成**1.170124448×**、整请求**1.741569262×**；四轮GM方向均更快。相对matched target仍为1.169237971×／1.035071366×，整请求第二轮0.940220031×明确保留。这是有限面板正向结果，不能把1.7416×全部解释为投机验证贡献。

新增模型请求、target/draft forward、warmup均为**0**。没有启动native程序、runner、服务器、profiling或runtime恢复，没有修改模型/运行库/驱动/论文或旧PR。此次只读取原归档与已恢复B记录，编写并执行CPU分析。

## 证据与资格

原ZIP122395102bytes，SHA25688ff7d52da4815dee11d7232e36b292fd77fe18a414e01aca41e860cdd4cade5；全ZIP CRC通过。10151logical files/6542objects身份符合。B_RECORDS SHA256a6e562625f229fd38eed31a9492bb04db269f78355391ab41cf31c6d2dce6bd4。读取并核验498个B及计时来源相关文件，未重新审计C/D raw。打包源码250058d…、B运行源码7b8c6fb…、公共PR62头8dfa60a…分别保留。Phase2依赖ZIP的身份与所读计时源码匹配。

384/384正式请求，16/16原warmup排除；四条件每个96/96完整保存数组及endpoint资格通过，24/24参考跨四轮稳定。每条独立raw与RECORDS聚合一致、唯一键和轮转顺序一致；输入/程序/source身份、cache_n=0、无truncation及参数一致。参考实际11–128token，23EOS/1cap；完整response数组不代表未记录的内部样本流。原bridge16请求/4warmup未混入成本。

## 主要成本比较

{primarytable}
全部比值为baseline/candidate，>1候选更快；先每题每条件四个绝对ms取中位数，再比值，再24题等权几何平均。相对普通R的生成慢任务为{', '.join(slow)}，保留不删；其余22更快，整请求24均更快。matched目标整请求17更快/7更慢且有第二轮反向。绝对费用见下表，表中跨任务中位数用于描述，不是比值GM的分子分母。

{absolute}
主候选固定为target_scopes，未按新结果切换mask。历史practical_decode_gain规则（generation≥1.03、whole≥1、至少3/4轮generation>1）在R及matched两比较通过；该历史门槛不把事后追加的R比较变成前瞻实验，也不是部署保证。

## 解释范围

R/matched整请求1.68256×而生成1.00076×（描述区间跨1）。R使用全局UB1，matched使用mask3/UB4；其prefill等执行路径也不同。因此总整请求改善包含路径改变与投机，不能由GM差推导attention、draft、KV或同步的费用比例。逐题48项与两个GM乘法恒等式均通过，它们只是算术核查。

generation采用原predicted_ms，首样本/预填充及部分末尾记账不在此字段；whole采用收到并解析resident HTTP响应的host wall_ms，模型加载/热身/退出另属边界。B未启用条件式hs::move状态移植；相关代码存在不等于本次承担其费用。详见SOURCE_TIMER_AUDIT。四轮各四个独立resident进程，不是同一进程同时测四模式。未认证环境完全平稳或生产并发性能。

## 描述统计与独立验证

固定20261008、PCG64、10000次任务聚类bootstrap、linear/type7分位数；先合并重复再重采样24题。这是已暴露面板的描述区间，不是跨模型/任务总体保证。旧20261005/4000/sorted99与3899规则另算，旧三组比较的点值、各轮与区间均复现。新parser不导入旧runner或资格/成本函数；第二复算器直接从raw重建数组、键、绝对费用、配对与分位数。{verify['positive_and_negative_checks']}项检查通过，六负例（缺重复、重复键、倒置比值、错单位、不合格输出、非有限成本）全部拒绝。前期CPU实现错误完整保留在ANALYSIS_REPAIRS，未改变原数据或删除失败。

## 论文交接

结论分支：**FINITE_PANEL_GAIN_AGAINST_ORDINARY_AND_MATCHED**，同时保留matched整请求轮次混合与计时限制。可写RTX具体局部方案的完整参考合格加速、自然状态/当前路径有限诊断，以及数值资格与实际工作量需要共同验证。不能写普适无损、全局最优、唯一kernel原因、功能正确率或跨平台普遍加速。

PR65的B570 E119/120、强R负结果与GPU_NEXT_ACTION=STOP保持原样，本轮只是补齐其deferred RTX raw item。C4更宽k的成本负结果保持各自会话分母。接下来可以进入全稿证据整合、重构、编译与审稿，**本任务没有改写论文**。PAPER_HANDOFF含英文段落、主张映射与全稿顺序。

## 次要比较（全部保留）

{fulltable}
原科学输入/归档的post-audit通过，图表SVG/PDF另提供PNG查看。所有新分析源码、小型派生表与交接仅添加独立研究目录，Draft PR不合并。交付身份由后续DELIVERY_RECEIPT记录。
'''
    put('REPORT.zh-CN.md',report)
    claims=[
      ('RTX B output qualification','WRITE','PR62 8dfa60a; B_RECORDS a6e5626; QUALIFICATION_RECOMPUTED.csv','384 formal;96/path;24 stable tasks','none','now exposed','complete saved response.tokens/endpoint only'),
      ('RTX ordinary-R gain','WRITE_SCOPED','COST_SUMMARY primary R/target_scopes','all paths qualified','ordinary scalar UB1/mask0/no draft','post-hoc exposed24','1.170124 gen/1.741569 whole; four rounds positive;not global fastest ordinary'),
      ('RTX matched-target gain','WRITE_WITH_REVERSAL','PR62 8dfa60a; COST_SUMMARY','96 candidate and96 target','matched mask3 UB4','exposed24','1.169238/1.035071; whole round2=.940220'),
      ('Full whole gain is speculative contribution','DO_NOT_WRITE','SOURCE_TIMER_AUDIT; R/matched','same output contract','R/matched1.000758 gen/1.682560 whole','exposed24','path/prefill differences; no isolated component timing'),
      ('Globally minimal mask3','DO_NOT_WRITE','PR60 ba7f0ae','finite four-probe16-mask family','source-specific costs','exposed','only tested-family inclusion minimality'),
      ('State/current-path dependence','WRITE_SCOPED','PR59 b0dfa0f; PR62 8dfa60a; PR64 6842120','own-path shams;natural-state controls','not cost result','limited tasks/same model family','local decision/score evidence;not unique operator/full repair'),
      ('B570 deployment speedup vs ordinary','DO_NOT_WRITE','PR65 8783cb1 PAPER_HANDOFF/DECISION','E119/120;R/matched/candidate30 each','R/candidate.282588gen/.201290whole','15 accessible-project unused at old freeze;now exposed','endpoint not full raw suffix; STOP GPU'),
      ('B570 matrix COMPLETE','DO_NOT_WRITE','PR64 6842120;PR65 8783cb1','119/120','14 complete oldN1 pairs vs15 R pairs','already executed','missing oldN1 MBPP400 round1 preserved'),
      ('Wider speculation improves efficiency','DO_NOT_WRITE','PR62 C4_RESULTS at8dfa60a','qualified k7 but gateFAIL','k3 anchor;k7/k3.829442gen/.889868whole','28 reused exposed','diagnostic warmup counts separate from formal work'),
      ('Cross-platform mechanism universally transfers','NARROW','PR59/62/64/65 exact heads','CUDA/Vulkan finite controls','never pool speed','different references and suffixes','diagnostic design only;one Qwen3 family'),
      ('M4/358H late state-cross equivalent','DO_NOT_WRITE','main e87291d;PR61 4f34359 baseline','use existing source-specific contracts','source-specific timers','historical','no late comparable cross here'),
      ('Novel automatic numerical repair algorithm','DO_NOT_WRITE','late study boundaries','manual bounded constraint family','measured instances only','no new holdout','empirical system evidence;not universal algorithm')]
    with (ROOT/'CLAIM_EVIDENCE_MATRIX.csv').open('w',encoding='utf-8',newline='') as f:
        exact=read('EXACT_SOURCES.json');bound=[]
        for claim in claims:
            parts=list(claim)
            for tag,sha in exact.items():
                if tag.startswith('PR'):parts[2]=parts[2].replace(tag+' '+sha[:7],tag+' '+sha)
            parts[2]=parts[2].replace('main e87291d','main '+exact['main']);bound.append(parts)
        writer=csv.writer(f);writer.writerow(['claim','disposition','exact_source','qualification','cost_baseline','exposure','limit']);writer.writerows(bound)
    decision={'analysis_status':'COMPLETE_CPU_REFERENCE_CLOSEOUT','branch':'FINITE_PANEL_GAIN_AGAINST_ORDINARY_AND_MATCHED','paper_status':'READY_FOR_BOUNDED_MANUSCRIPT_RECONSTRUCTION','ordinary_reference_generation':g['task_median_gm'],'ordinary_reference_whole':w['task_median_gm'],'matched_generation':mg['task_median_gm'],'matched_whole':mw['task_median_gm'],'matched_whole_round2':mw['rounds'][1]['gm'],'ordinary_historical_practical_decode_gain':True,'matched_historical_practical_decode_gain':True,'post_hoc':True,'all_prior_PRs_unmerged':True,'B570_GPU_NEXT_ACTION':'STOP','RTX_GPU_NEXT_ACTION':'STOP_FOR_THIS_CLOSEOUT','new_model_requests':0,'new_target_draft_forwards':0,'new_warmups':0,'manuscript_modified':False,'remaining_stage':'whole-manuscript evidence integration, reconstruction, compile and review; not another same CPU closeout'}
    put('DECISION.json',json.dumps(decision,indent=2))
    put('NEXT_STAGE.md','# Next stage\n\nProceed to bounded whole-manuscript evidence integration and reconstruction using PAPER_HANDOFF and exact-source claims. Preserve B570 incomplete E/negative strong baseline and RTX C/C4 boundaries. Compile and review the integrated manuscript separately. No additional model requests are needed to obtain a preferred sign, and no duplicate CPU closeout is requested. This stage did not rewrite the manuscript. Keep allPRs unmerged.')
    put('README.md','# RTX PR62 ordinary-reference CPU closeout\n\nRead REPORT.zh-CN.md, PAPER_HANDOFF.md, DECISION.json and SOURCE_TIMER_AUDIT.md. New model requests/forwards/warmups=0. Same frozen24-task B panel:384 formal/16 excluded warmups, raw qualification independently reconstructed. New files only.\n\nReproduce using REPRODUCE.md with the identity-bound previous local archives and restored B experiment. The small public tables are CPU-derived data; old model/native arrays/telemetry and binaries stay in immutable local archives. PROTOCOL is post-hoc, not a new preregistration. Preparation repairs and checkpoints are retained.\n\nFigures show baseline/candidate speed; >1 candidate faster. Claims remain within the measured UB1 ordinary reference and matched-target paths; no universal losslessness or production gain is certified.')
    plot(tp,ss)
    put('SOFTWARE.json',json.dumps({'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__,'plot_fonts':'DejaVu Sans; SVG glyph paths/PDF embedded TrueType','no_model_execution':True},indent=2))
    print('Handoff, report, claim map and SVG/PDF/PNG figures generated.')

def plot(tp,ss):
    figdir=ROOT/'figures';figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'svg.fonttype':'path'})
    tasks=list(dict.fromkeys(p['task'] for p in tp));yy=np.arange(24)
    fig,axes=plt.subplots(1,2,figsize=(12.8,9.8),sharey=True)
    for ax,timer in zip(axes,['generation','whole']):
        vals=[]
        for base,offset,color,marker,label in [('scalar_reference',-.13,'#185abd','o','Ordinary scalar R / candidate'),('matched_target',.13,'#d06b15','s','Matched target / candidate')]:
            vv=[float(next(p['speedup_baseline_over_candidate'] for p in tp if p['task']==t and p['baseline']==base and p['candidate']=='target_scopes' and p['timer']==timer)) for t in tasks];vals+=vv;ax.scatter(vv,yy+offset,s=32,c=color,marker=marker,label=label,zorder=3)
        ax.axvline(1,color='#555',lw=1.2,ls='--');ax.set_yticks(yy,tasks);ax.set_ylim(23.6,-.6);ax.set_xlim(min(.9,min(vals))-.08,max(1.1,max(vals))+.1);ax.grid(axis='x',alpha=.25);ax.set_xlabel('Speed ratio: baseline ms / candidate ms (>1 faster)');ax.set_title('Server generation timer' if timer=='generation' else 'Resident whole-request latency',pad=12)
    fig.suptitle('RTX frozen B panel: target_scopes candidate versus both baselines',y=.97,fontsize=14)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.048),ncol=2,frameon=False)
    fig.text(.5,.018,'24 exposed MBPP tasks; four repeats collapsed to condition medians per task. No new model execution.',ha='center',fontsize=9)
    fig.subplots_adjust(top=.9,bottom=.14,left=.105,right=.98,wspace=.14)
    for ext in ['svg','pdf','png']:fig.savefig(figdir/f'task_speed_pairs.{ext}',dpi=170)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12.8,4.8),sharey=True)
    pairs=[('scalar_reference','target_scopes','R / candidate'),('matched_target','target_scopes','Matched / candidate'),('scalar_reference','matched_target','R / matched')]
    for ax,timer in zip(axes,['generation','whole']):
        for i,(base,cand,label) in enumerate(pairs):
            s=next(v for v in ss if v['baseline']==base and v['candidate']==cand and v['timer']==timer);lo,hi=s['descriptive_task_bootstrap_95_linear'];point=s['task_median_gm'];ax.errorbar(point,i,xerr=[[point-lo],[hi-point]],fmt='o',color='#185abd',capsize=4,zorder=4);ax.scatter([v['gm'] for v in s['rounds']],[i+.17]*4,s=40,marker='x',color='#bd5420',zorder=3);ax.text(.52,i+.43,f'{point:.4f} [{lo:.4f}, {hi:.4f}]',transform=ax.get_yaxis_transform(),ha='center',fontsize=8)
        ax.set_yticks(range(3),[v[2] for v in pairs]);ax.set_ylim(2.7,-.5);ax.axvline(1,ls='--',color='#555');ax.grid(axis='x',alpha=.25);ax.set_xlabel('Baseline / candidate speed ratio');ax.set_title('Generation' if timer=='generation' else 'Whole request')
    fig.suptitle('Task-median GM with descriptive 95% intervals; crosses show all four round GMs',fontsize=12)
    fig.text(.5,.012,'Bootstrap: 24 task clusters, seed20261008, 10000 resamples, linear quantiles. Matched whole-request round2 reverses.',ha='center',fontsize=9)
    fig.subplots_adjust(top=.82,bottom=.17,left=.14,right=.98,wspace=.13)
    for ext in ['svg','pdf','png']:fig.savefig(figdir/f'aggregate_and_rounds.{ext}',dpi=170)
    plt.close(fig)
if __name__=='__main__':main()
