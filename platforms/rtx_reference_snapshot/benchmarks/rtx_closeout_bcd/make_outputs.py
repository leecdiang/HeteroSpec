"""Derive user-facing closeout tables and report from audited retained evidence."""
import csv,statistics
from close_base import HERE,read,save,sha

OUT=HERE.parent.parent/'outputs'
PREFIX='HeteroSpec_RTX_闭环'
def csvwrite(name,rows):
    with (OUT/(PREFIX+name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def ratio(c,key):return c[key]['task_median_geomean_speedup']
def comparison_line(c):
    g=ratio(c,'generation');w=ratio(c,'wall')
    return f'| {c["numerator"]} / {c["denominator"]} | {g:.4f}x | {w:.4f}x | {"合格" if c["qualified"] else "诊断成本"} |'

def main():
    audit=read(HERE/'generated/POST_AUDIT.json');assert audit['status']=='PASS'
    b=read(HERE/'generated/B_RESULTS.json');c=read(HERE/'generated/C_RESULTS.json');d=read(HERE/'generated/D_RESULTS.json');exposure=read(HERE/'EXPOSURE_LEDGER.json')
    c2sel=read(HERE/'generated/C2_SELECTION.json');c2=read(HERE/'generated/C2_RESULTS.json') if c2sel['status']=='RUN' else None
    c4sel=read(HERE/'generated/C4_SELECTION.json');pilot=read(HERE/'generated/C4_PILOT_RESULTS.json')
    c4=read(HERE/'generated/C4_RESULTS.json') if c4sel['status']=='RUN' else None
    c4long=read(HERE/'generated/C4_LONG_RESULTS.json') if c4 else None
    matrix=[]
    for cfg in c['configurations']:
        for cohort,p in cfg['cohorts'].items():
            cost=next(x for x in cfg['costs'] if x['cohort']==cohort)
            matrix.append({'k':cfg['k'],'ub':cfg['ub'],'cap':cfg['cap'],'cohort':cohort,'tasks':len(p['tasks']),
              'scalar_reference_stable':p['qualification']['scalar_reference'],'matched_target_full_equal':p['qualification']['matched_target'],
              'speculation_full_equal':p['qualification']['selected_speculation'],'qualified_cost':cost['qualified'],'generation_speedup':ratio(cost,'generation'),'wall_speedup':ratio(cost,'wall'),
              'reference_actual_tokens_min':min(p['actual_reference_lengths'].values()),'reference_actual_tokens_max':max(p['actual_reference_lengths'].values())})
    csvwrite('_长度宽度矩阵',matrix)
    costs=[{'stage':'B',**x} for x in b['costs']]+[{'stage':'D',**d['panels']['d']['costs']}]
    if c2:costs += [{'stage':'C2',**x} for x in c2['costs']]
    if c4:costs += [{'stage':'C4',**x} for x in c4['costs']]
    csvwrite('_速度汇总',[{'stage':x['stage'],'candidate':x['numerator'],'baseline':x['denominator'],'qualified':x['qualified'],'generation_speedup':ratio(x,'generation'),
              'whole_request_speedup':ratio(x,'wall'),'practical_decode_gain':x['practical_decode_gain'],'generation_bootstrap_low':x['generation']['task_bootstrap_descriptive_95'][0],
              'generation_bootstrap_high':x['generation']['task_bootstrap_descriptive_95'][1],'faster_generation_repetitions':sum(v>1 for v in x['generation']['repeat_geomeans'])} for x in costs])
    flat=[]
    for x in costs:
        for t,g in x['generation']['task_ratios'].items():flat.append({'stage':x['stage'],'candidate':x['numerator'],'baseline':x['denominator'],'task':t,'qualified':x['qualified'],'generation_speedup':g,'whole_request_speedup':x['wall']['task_ratios'][t]})
    csvwrite('_逐任务速度',flat)
    if c2:csvwrite('_宽度确认输出',c2['details'])
    csvwrite('_固定UB资格',pilot['details'])
    if c4:
        csvwrite('_固定UB独立确认',c4['details'])
        csvwrite('_固定UB长输出',[{'cap':x['cap'],**r} for x in c4long['configurations'] for r in x['details']])
        csvwrite('_固定UB草稿统计',[{'condition':name,'full_reference_qualified':c4['qualification'][name],**x,
           'accepted_fraction':x['accepted']/x['drafted'] if x['drafted'] else None} for name,x in c4['draft_counts'].items()])
    proofs=d['reset_proof']['proofs'];resets=sum(x['proof']['request_prefill_resets'] for x in proofs)
    passing=[(x['k'],x['ub'],x['cap']) for x in c['configurations'] if x['qualification']['matched_target'] and x['qualification']['selected_speculation']]
    diagnostics=read(HERE/'generated/C_BOUNDARY_DIAGNOSTICS.json') if (HERE/'generated/C_BOUNDARY_DIAGNOSTICS.json').exists() else {'status':'NOT_NEEDED','paid_requests':0,'warmups':0}
    conclusion='本轮 RTX 的 B/C/D 验证已按冻结合同完成，可以对这组有限配置与任务作实验闭环。' if c['D_anchor_qualified'] and d['qualified'] else '本轮 RTX 的负面边界已记录；原配置未通过全部后续门槛，不能宣布其稳定无损闭环。'
    lines=['# HeteroSpec：RTX 剩余验证与有限闭环报告','',conclusion,'',
      '这轮延续论文 main e87291d、局部一致性诊断（PR #59）和范围消融（PR #60），没有重新从零研究投机解码。研究问题是：此前诊断得到的目标端约束，能否在新任务、更长输出、更宽验证调用和长驻请求下继续维持原生标量参考；若能，是否有进一步速度收益。B570 尚未运行。','',
      '术语：k 是每轮草稿长度上限；UB 是后端单次微批上限。两者是独立变量。mask3 仅约束目标模型的预填充和继续验证；mask15 约束目标与草稿两个模型的两个阶段。mask0 为原有普通路径。参考一致指完整 token 序列及结束类型一致，不等于代码功能正确。','',
      '绑定环境：NVIDIA GeForce RTX 5070 Ti Laptop GPU，驱动616.92；目标 Qwen3-8B-Q8_0、草稿 Qwen3-0.6B-Q8_0；llama.cpp b10839 发布 CUDA 运行库及绑定私有前端；FA off、全部层卸载至 CUDA0、上下文4096、单序列、24线程、贪婪采样与固定种子123、禁用提示缓存。模型、发布库、前端和源码身份在记录包中逐项保存并后审计。','',
      '## B：此前未执行任务的前瞻验证','',
      f'可用项目历史审计覆盖 {exposure["project_records"]:,} 条记录。HumanEval 原先剩余的 19 个任务均已执行，未用池为 0；因此在相同官方 sanitized MBPP 数据版本、描述模板与聊天包装上，排除旧任务、描述/标识命中、重复和含糊记录，从 {len(exposure["eligible_ranked"])} 个合格候选中按固定哈希顺序锁定 24 个。完整审计、候选与输入在任何新任务生成之前冻结。这里的“未执行”仅指可审计的项目历史，不涉及模型训练。','',
      '数据源：[官方 MBPP 固定版本](https://github.com/google-research/google-research/tree/e49bbfe381c9c0e564b937f1c4e163a2273c65cc/mbpp)。数据集代码答案和测试没有作为在线输入。纯词表分词为零次前向。','',
      '原四探针桥接 16/16 完整参考一致。B 为 24 任务 × 4 条件 × 4 平衡重复，共 384 次正式请求及 16 次排除热身；每轮标量参考都是实际付费生成。完整 token 数组、EOS/上限结束与重复稳定性均纳入资格检查。','',
      '| 条件 | 与独立标量参考全任务、全重复一致 |','|---|---|']
    lines += [f'| {name} | {"通过" if v else "失败"} |' for name,v in b['qualification'].items()]
    lines += ['', '| 候选 / 基线 | 生成阶段速度比 | 整请求速度比 | 输出资格 |','|---|---:|---:|---|']+[comparison_line(x) for x in b['costs']]
    lines += ['', '速度比定义为基线耗时 / 候选耗时，按每任务重复中位数求比再取几何平均。生成阶段计入该原生服务的草稿与验证过程；整请求包含实际预填充、生成和响应。加载、卸载与一次会话热身排除，但热身计入总执行数。固定种子任务重采样区间只作这组有限面板的描述，不是总体迁移置信区间。','',
      '目标范围方案在这批新任务上保持参考，同时相对匹配目标解码有加速。减少草稿约束相对全范围方案的额外生成收益仍未达到预先规定的 1.03x 门槛；不能把这一项写成已经验证的显著新解码加速。','',
      '## C：长度、宽度与实际计算图','',
      '新私有编译程序与前一版仅有一个源文件变化：把已有单 KV 序列查询布局的宽度检查从 4 扩到 8。模型、FA off、无 bias/sink、单序列限制及 CUDA 发布库均保持绑定。没有重写 CUDA 算术，也没有绕过多序列限制。新程序在全 24 个 B 任务上完成 48 次 UB4 桥接并复现 B 参考；四宽度的 16 次有记录检查验证了实际图宽度与目标/草稿、预填充/继续生成阶段。可进入某 CUDA 路径不等于已证明实际内核调度。','',
      '正式矩阵：哈希首 8 个 MBPP 新任务与 3 个已暴露 HumanEval 长输出补充，各自分开报告；k/UB 为 1/2、3/4、5/6、7/8，上限 128/256/512，3 模式、2 轮。共 792 次正式请求及 24 次排除热身。每一宽度、每一上限都实际重新生成标量参考。三个旧任务在上限 512 下的标量实际长度为 139、261、175，不能声称覆盖完整 512 token 解码。','',
      '| k / UB | 上限 | 新 MBPP：目标 / 投机 | 旧长输出：目标 / 投机 | 合并资格 |','|---|---:|---|---|---|']
    for cfg in c['configurations']:
        def marks(label):
            q=cfg['cohorts'][label]['qualification'];return ('通过' if q['matched_target'] else '失败')+' / '+('通过' if q['selected_speculation'] else '失败')
        lines.append(f'| {cfg["k"]} / {cfg["ub"]} | {cfg["cap"]} | {marks("primary_unused_MBPP")} | {marks("exposed_long_supplement")} | {"通过" if (cfg["k"],cfg["ub"],cfg["cap"]) in passing else "失败"} |')
    lines += ['', f'跨宽度标量参考稳定：{c["all_reference_cross_width_stable"]}。失败配置的完整输出与费用都保留，费用仅作诊断；没有更换参考或补上隐藏的标量修复。', '',f'边界诊断状态：{diagnostics["status"]}；另外实际支付 {diagnostics.get("paid_requests",0)} 次完整请求及 {diagnostics.get("warmups",0)} 次热身。机制解释以另存诊断记录的能力边界为限，不能仅从输出相同推出唯一算子原因。','']
    topology=read(HERE/'generated/C_TOPOLOGY_OUTPUT_COMPARISONS.json')
    assert sum(not x['original_reference_equal'] for x in topology)==4
    lines += ['正式 C 面板中，k5/UB6 与 k7/UB8 均在 MBPP/229 失败，三个上限、两次重复共12条投机请求偏离参考。另外，实际图检查的旧 HumanEval/18 在 UB6/8 下连目标单独解码也偏离原参考（69 token/EOS 对原72 token/EOS）；UB2/4 通过。HumanEval/31 在这些图检查中通过。这个旧探针负结果不能被正式11任务面板的目标控制通过所掩盖。','',
      '原 C 同时改变 k 和 UB，且 UB 也作用于预填充。因此它定位了组合配置边界，尚不能把失败归因于草稿长度 k 本身。最后的固定 UB 补充用于隔离这一变量，不撤回这些负结果。','']
    if c2:
        lines += ['## C 补充：独立确认更宽方案','',f'此补充在 k5/k7 首次输出之前冻结：仅按全部 C 正确性选最高合格宽度，未根据速度选择。选定 k={c2["selected_k"]} 后，在全部 24 个 B 任务及原 4 探针上以 4 条件、4 平衡重复独立执行 448 次请求及 16 次热身。其中 16 个 B 任务未用于 C 宽度选择；这是新配置的验证，不能重新称为未执行任务验证。普通同宽度投机是保留的对照。','',
          '| 条件 | 全 28 任务、全重复参考一致 |','|---|---|']+[f'| {name} | {"通过" if v else "失败"} |' for name,v in c2['qualification'].items()]
        lines += ['', '| 候选 / 基线 | 生成阶段速度比 | 整请求速度比 | 输出资格 |','|---|---:|---:|---|']+[comparison_line(x) for x in c2['costs']]
        lines += ['', '普通同宽度方案若参考不一致，其费用不作为有效无损加速基线。更宽方案若在这次全任务确认失败，C 的局部通过仍保留，但不能推荐该宽度为整个面板的合格方案。','']
    else:lines += ['条件式更宽速度确认没有启动：'+c2sel['reason']+'','']
    c3sel=read(HERE/'generated/C3_SELECTION.json')
    if c3sel['status']=='SKIPPED':lines += ['全范围修复确认也按预先规则跳过：'+c3sel['reason']+'','']
    if diagnostics['status']=='COMPLETE_QUALIFIED_LOCAL_CROSSINGS':
        lines += ['## 新任务宽度失败的自然状态诊断','',
         'MBPP/229 在 k5/UB6 的两个预定失败配置（上限128、256）各支付五条完整自然轨迹：独立标量、匹配目标、目标范围投机、全范围投机、普通同宽度投机。前两者与普通同宽度方案均为50 token/EOS；两个约束投机方案均为54 token/EOS，完整参考不一致。普通同宽度方案在这个任务上通过，不能推成全任务通过。','',
         '两条目标范围与普通自然轨迹在已提交47 token处仍有共同参考前缀，且待验证 token、位置、序列标记、logits掩码和逻辑KV位置完全相同。实际捕获各自的状态与克隆采样器，原输出不变；两份状态的提示KV不相同，72个KV张量中70个不同。两个上限命中同一任务、同一边界，不是两个独立任务。','',
         '独立诊断程序分别把两份真实过去状态放入普通/约束当前查询布局，保持同一实际UB6调用，支付每边界四次目标解码，共8次辅助解码。状态位模式往返一致、采样器契约匹配、每边界两个同路径sham（共四个）均复现各自原生验证决策，源状态、源采样器、未用旧logits和完整源轨迹保持不变。此处没有强制前缀或在线送入参考/草稿答案。','',
         '| 真实过去状态 | 当前普通查询布局 | 当前约束查询布局 |','|---|---|---|',
         '| 目标范围轨迹的状态 | EOS判断偏离参考 | EOS判断偏离参考 |',
         '| 普通轨迹的状态 | EOS判断匹配参考 | EOS判断匹配参考 |','',
         '在这个局部边界，当前布局切换没有改变离散决策，状态切换在两条当前路径上都改变了EOS决策。这证明了该边界的过去状态效应，并说明只在这里切换当前路径不足以修复。没有直接把UB4与UB6作自然调用交叉；该结果不是整个宽度失败的唯一算子根因证明，也不是全程反事实续写。','',
         '浮点记录补充了这一解释：在共同到达、首次分歧的第50个生成token处，EOS相对同一替代token的logit差，约束来源状态为 −0.09283/−0.62923，普通来源状态为 +0.99707/+1.48868（分别为当前普通/约束布局）。当前布局仍改变了数值：两份状态下logit最大绝对变化为0.44920和0.38070。因此不能声称当前路径对数值无影响；这里是状态与决策裕量共同决定排名的直接观察。该差值不是全词表前两名间隔、算子误差上界或可在线部署的校准证书。两个上限的结果一致。','',
         '可承接原论文的实用判断是：一次从头重执行得到参考，并不能证明在现有原生状态上切换当前验证路径能修复；检查应包含过去状态来源、当前调用形状和适用范围。宽度扩展必须重新验证这一组合，约束数量更多也不保证参考一致。这个结论在此新任务的有限边界上有直接状态交叉证据。','']
    lines += ['## C4：固定数值微批、隔离草稿长度','',
      '这是在原 B/C/D 和负边界诊断完成后的最后一项有限补充，新增方案在任何 C4 生成前冻结并提交到研究 PR。保持 UB=4 和 mask3，先在24个 B 任务与原4探针上测试 k3/5/7、上限128、两次正反序重复，共168次资格请求及6次热身。实际图需保持微查询宽度不超过4并保留多查询目标路径；资格运行开启记录与强制同步，其费用不用来选择速度。原 C2/C3 跳过结论保留。','',
      '| 草稿上限 k（UB固定4） | 全28任务、两次重复参考一致 |','|---|---|']+[f'| {k} | {"通过" if q else "失败"} |' for k,q in pilot['qualification'].items()]
    if c4:
        lines += ['',f'只按完整参考资格选择最高合格 k={c4["selected_k"]}，随后关闭记录，以4条件、4平衡重复独立支付448次计时请求和16次热身。相同28任务曾用于资格选择，这不是留出任务或新的未执行任务验证。普通同k/UB投机保留为对照；失败对照的成本只作诊断。','',
          '| 条件 | 全28任务、四次重复参考一致 |','|---|---|']+[f'| {name} | {"通过" if q else "失败"} |' for name,q in c4['qualification'].items()]
        lines += ['', '| 候选 / 基线 | 生成阶段速度比 | 整请求速度比 | 输出资格 |','|---|---:|---:|---|']+[comparison_line(x) for x in c4['costs']]
        lines += ['', '| 条件 | 实际草稿 token 数 | 实际接受草稿数 | 接受比例 |','|---|---:|---:|---:|']
        for name,x in c4['draft_counts'].items():
            fraction=f'{x["accepted"]/x["drafted"]:.2%}' if x['drafted'] else '不适用'
            lines.append(f'| {name} | {x["drafted"]} | {x["accepted"]} | {fraction} |')
        lines += ['', '计数来自实际原生草稿/接受记录，是本面板的汇总，不替代完整输出资格和付费速度比较。普通同宽度方案若失败，单独解释其计数与成本。','']
        lines += ['本轮 k3 与 k7 的草稿数分别为3528和5392，接受数分别为2772和3192；更长草稿增加了实际工作，但接受增长没有抵消成本。所有四轮 k7/k3 生成速度比均小于1。该描述支持本面板的效率拒绝，不证明所有长度/模型都应选k3。','']
        lines += ['有记录的资格会话（每组28任务加一次热身）中，k3/k5/k7 的目标继续验证调用数分别为305/232/199，记录到的微批计算图数却为305/463/397，两轮相同。更少的逻辑验证调用没有意味着更少的微批计算工作。这里计的是实际原生调用与图观察数，不是CUDA内核启动数；这些有强制同步的会话不参与速度统计。','']
        extra=next(x for x in c4['costs'] if x['denominator']=='anchor_speculation')
        lines += ['',f'相对原 k3 的预定额外收益门槛（参考一致、生成≥1.03x、整请求≥1x、至少3/4重复方向更快）：{"通过" if extra["practical_decode_gain"] else "未通过"}。不因成本结果再调参。','',
          f'明确的投入结论：本次 k7 的生成速度比 {ratio(extra,"generation"):.4f}x、整请求速度比 {ratio(extra,"wall"):.4f}x；'+('相对原k3更慢，固定微批的更大草稿方案在本面板没有形成新增加速，结束该配置方向投入。保留原k3/UB4作为已验证的效率锚点。' if ratio(extra,'generation')<1 and ratio(extra,'wall')<1 else '是否推进需同时满足完整参考、长输出和额外速度门槛；单纯参考通过不是速度改进。'),'',
          '最后独立支付原11任务在上限256/512的标量、匹配目标、选定投机三条件，两次重复，共132次请求及6次热身；所有标量重新实际生成，并与原 C 同上限标量检查一致。','',
          '| 上限 | 标量稳定 / 匹配目标 / 选定投机 | 合格生成速度比 / 整请求速度比 |','|---|---|---|']
        for cfg in c4long['configurations']:
            q=cfg['qualification'];cost=cfg['cost'];marks=' / '.join('通过' if q[m] else '失败' for m in ['scalar_reference','matched_target','wider_speculation'])
            lines.append(f'| {cfg["cap"]} | {marks} | {ratio(cost,"generation"):.4f}x / {ratio(cost,"wall"):.4f}x（{"合格" if cost["qualified"] else "诊断"}） |')
        lines += ['', '更高 k 的长驻独立阶段 D 尚未测试；D 的阶段重置结论只绑定原 k3。长度上限也不等于实际生成长度。C4 即使通过也只扩展本次有限面板的配置资格，不能说明普适最优宽度。','']
    else:lines += ['', '没有更高 k 通过全28任务资格，按预定规则跳过额外速度与长输出确认；全部失败保持原样，并结束 RTX 继续调参。'+c4sel['reason'],'']
    dc=d['panels']['d']['costs']
    lines += ['## D：长驻请求与阶段重置','',f'原 k3/UB4/上限128 配置的 C 锚点资格为 {c["D_anchor_qualified"]}。24 个 B 任务按两个固定哈希排列，每模式/轮使用一个长驻、禁用缓存的服务。先支付 96 次有记录请求加 4 次热身，观察到 {resets} 个目标端从位置零开始的预填充重置（包含热身）；另支付 96 次关闭记录的计时请求加 4 次热身。两批完整参考资格为 {d["qualified"]}。有记录运行的强制同步费用未进入正式加速统计。','',
      '| 候选 / 基线 | 生成阶段速度比 | 整请求速度比 | 输出资格 |','|---|---:|---:|---|',comparison_line(dc),'',
      '会话前后 GPU 观察在请求计时之外；首末半会话耗时只作描述，因任务不同，不能据此认定热漂移原因。长驻单请求串行不是多并发生产吞吐验证。','',
      '## 闭环范围与论文承接','',
      '可以陈述的是：在这组锁定硬件、模型、版本、采样、单序列、任务和配置上，诊断得到的目标预填充与继续验证约束具有新任务的有限验证，并已测出其长度/宽度及长驻执行边界。A 的最小范围只针对原探针，不是全任务、全平台的全局最小定理。','',
      '论文贡献应继续连接“此前的原生状态/当前调用诊断 → 具体约束范围 → 完整参考资格 → 实际成本与适用边界”。投机解码本身能加速属于已知事实；新增速度必须通过与原 k3 方案及普通同宽度方案的独立比较来判断。没有功能正确率、普适无损、唯一算子原因、生产吞吐或期刊录用承诺。','',
      '下一步 B570 应把平台作为显式变量：保持输入包装与模型身份，实际重新支付其自身原生标量参考，再验证方法能否确定该平台需要约束的角色/阶段和合格宽度。RTX 的 mask3 与参考 token 不能直接当成 B570 的答案。B570 和其他平台的执行不属于本记录包。','',
      '## 证据与复现','',f'本轮合计 {audit["panel_requests"]} 次正式/资格/诊断完整请求与 {audit["excluded_warmups"]} 次排除热身，共 {audit["all_complete_generation_requests"]} 次完整生成。其中常规B/C/D及桥接为 {audit["complete_generations_before_boundary_diagnostics"]} 次完整生成；额外边界诊断 {audit["boundary_paid_requests"]} 次完整请求与 {audit["boundary_warmups"]} 次热身、固定UB补充 {audit["fixed_ub_complete_generations"]} 次完整生成，均已包含在总数内。另有 {audit["paid_auxiliary_target_decode_calls"]} 次实际辅助目标解码，单独计费记数。来源与资产后审计 PASS；{audit["published_Dlls_checked"]} 个发布 DLL及原模型身份核验通过。全部失败和原始记录保留，含一次零模型执行的离线汇总索引错误及其修正。','',
      '新增研究 PR：[HeteroSpec #62](https://github.com/leecdiang/HeteroSpec/pull/62)。早期 PR 和论文文件由用户的整合流程管理，本研究 diff 只追加独立目录。','',
      '同目录文件：长度宽度矩阵、速度汇总、逐任务速度 CSV，以及随后生成的完整记录 ZIP 和 SHA256 校验。ZIP 使用内容寻址保存全新原始记录、精确私有源码/可执行程序、输入来源与 Git 历史；Phase1、Phase2A 两个已有记录包作为单独不可变依赖。解包后按记录的路径变量设置旧阶段根目录，再用 restore_runtime.py 核对并放置可执行程序与已安装发布 DLL。模型权重不在记录包内。','']
    (OUT/(PREFIX+'_实验报告.md')).write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    save(HERE/'generated/DELIVERABLE_IDENTITIES.json',{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name.startswith(PREFIX) and p.suffix in ['.md','.csv']})
    print('Derived closeout report and tables written.',flush=True)

if __name__=='__main__':main()
