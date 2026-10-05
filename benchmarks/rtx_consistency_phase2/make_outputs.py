"""Generate Phase 2 user artifacts from audited complete records, after measurement."""
import csv,json,shutil,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from base import HERE,read,save

OUT=HERE.parent.parent/'outputs'
LABELS={'mask3':'仅目标模型约束','mask15':'全部约束','target3':'匹配的目标单独解码'}

def main():
    a1=read(HERE/'generated/analysis/A1_RESULTS.json');a2=read(HERE/'generated/analysis/A2_RESULTS.json')
    a3=read(HERE/'generated/analysis/A3_RESULTS.json');audit=read(HERE/'generated/analysis/POST_AUDIT.json')
    assert audit['status']=='PASS' and all(x['qualifies'] for x in a3['conditions'])
    OUT.mkdir(exist_ok=True)
    for source,name in [('A1_OUTPUT_GATE.csv','16组合消融.csv'),('a3_TASK_COSTS.csv','逐任务速度.csv')]:
        shutil.copyfile(HERE/'generated/analysis'/source,OUT/('HeteroSpec_RTX_第二阶段_'+name))
    rows=[]
    for c in a3['costs']:
        rows.append({k:c[k] for k in ['candidate','baseline','request_speedup_gm','generation_speedup_gm','faster_request_tasks','faster_generation_tasks']})
    with (OUT/'HeteroSpec_RTX_第二阶段_速度汇总.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    conditions=a1['conditions'];tasks=list(conditions[0]['task_matches'])
    scopes=[[int(bool(c['mask']&b)) for b in [1,2,4,8]] for c in conditions]
    matrix=[[int(c['task_matches'][t]) for t in tasks] for c in conditions]
    fig,(ax,bx)=plt.subplots(1,2,figsize=(9,8),gridspec_kw={'width_ratios':[1,1.3]},layout='constrained')
    ax.imshow(scopes,cmap=ListedColormap(['#f0f2f5','#4361a4']),vmin=0,vmax=1,aspect='auto')
    bx.imshow(matrix,cmap=ListedColormap(['#d36b64','#409682']),vmin=0,vmax=1,aspect='auto')
    for a,title in [(ax,'Enabled attention scopes'),(bx,'Full original-output agreement')]:
        a.set_title(title,pad=14);a.set_yticks(range(16),[str(c['mask']) for c in conditions]);a.set_ylabel('Process-fixed mask')
        a.set_xticks(range(4));a.set_xticks([x-.5 for x in range(5)],minor=True);a.set_yticks([x-.5 for x in range(17)],minor=True)
        a.grid(which='minor',color='white',linewidth=1.5);a.tick_params(which='minor',bottom=False,left=False)
        for i in range(16):
            for j in range(4):a.text(j,i,('on' if scopes[i][j] else 'off') if a is ax else ('PASS' if matrix[i][j] else 'FAIL'),ha='center',va='center',color='white' if (a is bx or scopes[i][j]) else '#4c5666',fontsize=9)
    ax.set_xticklabels(['Target\nprefill','Target\ncontinue','Draft\nprefill','Draft\ncontinue'])
    bx.set_xticklabels([t.replace('HumanEval/','HE/') for t in tasks])
    fig.suptitle('RTX: complete four-scope factorial (16 masks × 4 tasks × 2 repeats)',fontsize=13)
    fig.supxlabel('All repeats stable. Minimal passing mask within this finite panel: 3. Timings are diagnostic only.',fontsize=9)
    for ext in ['png','svg']:fig.savefig(OUT/('HeteroSpec_RTX_第二阶段_约束范围.'+ext),dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(9.5,5.8),layout='constrained');xx=list(range(3));width=.31
    g=[c['generation_speedup_gm'] for c in a3['costs']];w=[c['request_speedup_gm'] for c in a3['costs']]
    intervals=[c['descriptive_task_bootstrap_95pct'] for c in a3['costs']]
    bars=ax.bar([x-width/2 for x in xx],g,width,label='Generation (draft + verify)',color='#4361a4')
    ax.errorbar([x-width/2 for x in xx],g,yerr=[[v-ab[0] for v,ab in zip(g,intervals)],[ab[1]-v for v,ab in zip(g,intervals)]],fmt='none',color='#243451',capsize=4)
    wall=ax.bar([x+width/2 for x in xx],w,width,label='Whole resident request',color='#409682')
    for b in list(bars)+list(wall):ax.text(b.get_x()+b.get_width()/2,b.get_height()+.013,f'{b.get_height():.3f}×',ha='center',va='bottom',fontsize=10)
    ax.axhline(1,color='#6b7280',linestyle='--',linewidth=1);ax.set_ylabel('Baseline time / candidate time (higher is faster)')
    ax.set_xticks(xx,['Target scopes only\nvs all scopes','Target scopes only\nvs matched target','All scopes\nvs matched target'])
    ax.set_ylim(0,max(max(g),max(w),max(i[1] for i in intervals))+.16);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    ax.set_title('Output-qualified RTX cost: 19 exposed tasks, 6 cyclic repetitions',pad=14);ax.legend(loc='upper left',frameon=False)
    fig.supxlabel('Task-median geometric means; error bars: descriptive task bootstrap for generation, not transfer intervals.',fontsize=9)
    for ext in ['png','svg']:fig.savefig(OUT/('HeteroSpec_RTX_第二阶段_成本对照.'+ext),dpi=180)
    plt.close(fig)
    rr=read(HERE/'runs/a3/RECORDS.json');acceptance={}
    for condition in ['mask3','mask15']:
        cr=[r for r in rr if r['condition']==condition]
        acceptance[condition]={'requests':len(cr),'drafted':sum(r['response']['timings']['draft_n'] for r in cr),
            'accepted':sum(r['response']['timings']['draft_n_accepted'] for r in cr)}
    differences=[]
    for t in read(HERE/'runs/a3/MANIFEST.json')['tasks']:
        counts={c:sorted({(r['response']['timings']['draft_n'],r['response']['timings']['draft_n_accepted']) for r in rr if r['task']==t and r['condition']==c}) for c in ['mask3','mask15']}
        if counts['mask3']!=counts['mask15']:differences.append({'task':t,'counts':counts})
    save(HERE/'generated/analysis/A3_ACCEPTANCE_SUMMARY.json',{'conditions':acceptance,'task_count_differences':differences,
        'limit':'Aggregate draft/accept counts do not prove identity of unrecorded proposal token arrays or kernel dispatch.'})
    primary=a3['costs'][0]
    verdict=('缩小约束通过了预先固定的额外效率门槛，可以作为后续迁移测试候选。' if a3['scope_efficiency_advance'] else
             '缩小约束保持了完整输出，但没有通过预先固定的额外decode效率门槛；整次请求的改善作为本组观察保留，不能据此宣称获得了可靠的新decode加速。')
    table=['| 比较 | 生成阶段加速 | 整次请求加速 | 生成更快的任务 | 请求更快的任务 |','|---|---:|---:|---:|---:|']
    for c in a3['costs']:table.append(f"| {LABELS[c['candidate']]} / {LABELS[c['baseline']]} | {c['generation_speedup_gm']:.6f}× | {c['request_speedup_gm']:.6f}× | {c['faster_generation_tasks']}/19 | {c['faster_request_tasks']}/19 |")
    repeats='、'.join(f'{x:.6f}' for x in primary['repeat_generation_speedups'])
    report=f'''# HeteroSpec RTX 第二阶段首批结果

## 当前判断

RTX 第一阶段已经在固定数值配置下闭环，可以继续推进。本轮先冻结整体方案，再完成实现检查、完整消融、原19任务资格检查和六轮成本比较。后续未用任务、长度/宽度边界和持续运行仍待各自清单冻结后开展。

{verdict}

## 本轮得到的范围结论

四个开关是目标模型prefill、目标模型continuation、草稿模型prefill、草稿模型continuation，对应位1/2/4/8。16种组合×四原探针×两轮，共128次完整输出检查；所有组合的输出和终止边界在两轮中稳定。通过集合为3、7、11、15，有限集合内唯一按包含关系最小的组合为3，即只约束目标模型的两个阶段。

原/15和/31在全部16种组合上都通过。/25在任一目标阶段启用后通过；/18需要两个目标阶段同时启用。草稿阶段开关不改变本组通过图案。这个结果是有限任务、固定k3/UB4/cap128和固定改造家族下的观察，不是普遍最小约束定理，也不能据此证明attention是唯一根因。

这些探针来自论文的原干预实验，但本轮计算合同为k3/UB4；/15在这里全通过，不会推翻或替换原来UB2/UB1干预下的/15效应。不同合同的状态与计算几何不能直接混为一个结果。

按运行前固定的规则选组合3，没有按耗时或接受率选候选。随后在全部19个已有任务上检验仅目标约束、全部约束及匹配目标单独解码，每种两轮38/38，共114/114符合原始完整参考。19任务都已用于历史研究，这一步不称为保留测试。

## 正式成本与完整输出

正式成本为三条件×19任务×六轮=342次完整请求，每条件114/114均符合原始参考；每种条件在每个执行顺序位置出现两次，任务顺序轮换。另18次预热排除。使用各任务六轮耗时中位数比值的几何平均，比例越大越快。

{chr(10).join(table)}

仅目标约束/全部约束的六个逐轮生成阶段比例为：{repeats}。本批任务的描述性重抽样95%区间为[{primary['descriptive_task_bootstrap_95pct'][0]:.6f}, {primary['descriptive_task_bootstrap_95pct'][1]:.6f}]；该区间只描述这19个暴露任务，不支持任务总体或跨平台迁移推断。

预先门槛要求完整输出一致、相对全部约束生成加速至少1.03×、整次请求至少1.00×、至少4/6轮方向为快。结论严格按这些条件判定，没有看结果再放宽阈值。#59的历史1.25644866×生成、1.07745052×请求结果保留；本轮数值来自新的均衡运行，不能与历史时间直接拼成一个比值。

生成阶段计时包括起草和验证的实际经过时间；整次请求还包括prefill、清理和响应。驻留加载、关闭、预热排除并单独列账。候选和目标单独解码使用相同目标计算与prefill路径。每次请求缓存命中为0，完整ID数组和EOS/128上限均检查，没有答案或录制proposal作为在线输入。

草稿工作量也并非完全相同：HumanEval/148的每次起草/接受数量由全部约束的90/81变为仅目标约束的93/80，但最终完整目标输出保持原参考。其他18任务的这两项计数相同。未记录的proposal token数组不能由计数证明相同；也没有单算子计时来确定请求改善的唯一来源。

## 与论文主线的连接

本轮把“原生干预结果的诊断”推进到一个可检验的工程选择：在当前条件下，一致性约束可以集中到目标模型及其状态构造和后续验证，草稿模型的同类约束并非维持这些参考输出所必需。是否节省时间必须另行测量，不能从约束更少直接推导。

具有迁移潜力的论断需要写成有条件的假设：当验证器及其状态构造满足选定的一致性合同，草稿路径可保留更自由的计算；随后用固定配方在未用任务和新计算几何上检验充分性与失败边界。本轮提供范围证据和成本证据；B/C/D尚未完成，因此不把假设写成已证明的通用原则。

## 后续按门槛铺开

先根据本轮判定冻结后续主候选，完成历史暴露审计，再锁定B的24 HumanEval+24 MBPP任务和完整输入身份，之后才生成付费标量参考。B通过后，C固定8任务，测试输出上限128/256/512与k/容量四组；更宽投影/FFN路径须单独资格检查。D最后验证两个请求顺序循环。任何新任务偏差或边界失败均保留，不通过调参和替换任务维持成功率。

就本轮数据而言，不建议继续把主要预算投到草稿约束的细碎删减：额外生成收益只有约0.36%，描述性区间跨过1。优先投入B的迁移资格，再在C研究能否在保持目标参考的条件下扩大验证宽度、获得更大效率收益。#59已有的加速仍是依据，缩小范围先作为诊断发现，不替代成熟结论。

四探针/19任务的范围结果尚不能证明未用任务充分性；128输出上限不代表所有任务完整到EOS；单请求不代表多槽吞吐；完整token一致不代表代码功能正确。CUDA实际kernel派发尚未用独立跟踪证明。成本是在当前Windows驻留服务环境下测量，后台图形活动和跨日漂移无法由边界采样完全排除，逐轮结果和均衡顺序用于暴露这一限制。

## 身份与完整记录

模型/发布版CUDA/FA-off/ctx4096/单槽/greedy seed123/提示格式保持原合同。模型权重、33个发布版DLL、原生程序及第一阶段源代码与二进制在事后复核中保持不变。新私有实现把模型角色与阶段开关写入计算图及复用资格；启用采集的资格检查验证了真实多query节点，正式计时关闭采集。

实现资格检查8次旧/新完整CLI、8次选择性驻留请求；A1 128次、A2 114次、A3 342次，共{audit['cli_complete_trajectories']+audit['resident_qualification_requests']+audit['panel_measured_requests']}次检查/测量，另{audit['excluded_warmups']}次排除预热，总计{audit['all_complete_generation_requests']}次生成请求。A1未通过参考的组合完整保留；一次缺少头文件的编译准备失败发生在零次模型运行之前，已保留。没有静默重跑。

原生代码冻结与各阶段源提交：实现/工程与A1 {a1['source_commit']}；A2 {a2['source_commit']}；正式成本 {a3['source_commit']}。这些是隔离实验仓库提交，不是论文仓库提交。论文基础为main e87291d，第一阶段为[PR #59](https://github.com/leecdiang/HeteroSpec/pull/59)。

本地“第二阶段完整记录”包保存本轮全部原始记录、源代码、私有CLI/server、失败记录、计算图证据及冻结Git历史，逐对象SHA256与ZIP校验。依赖的第一阶段完整记录包保留原文件与SHA256，不重复嵌入。GitHub提交源程序、方案、派生汇总与身份记录；模型权重、运行库、原始遥测不进入GitHub。B/C/D仅为已设计阶段，未执行。
'''
    (OUT/'HeteroSpec_RTX_第二阶段_首批结果.md').write_text(report,encoding='utf-8',newline='\n')
    print(json.dumps({'artifacts':'Phase2 report, 3 CSV, 2 PNG/SVG figures','scope_efficiency_advance':a3['scope_efficiency_advance'],'requests':audit['all_complete_generation_requests']}),flush=True)

if __name__=='__main__':main()
