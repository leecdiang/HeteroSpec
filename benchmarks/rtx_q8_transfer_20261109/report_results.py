"""Chinese result report; all preregistered arms/families and limitations retained."""
from pathlib import Path
import datetime,json
from admission import ROOT,HERE,put
from execute import WORK

def read(p):return json.loads(Path(p).read_bytes())
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows])+'\n'

def main():
    live=read(ROOT/'LIVE_RESULTS.json');same=read(ROOT/'SAME_WORK_RESULTS.json');ledger=read(ROOT/'CUMULATIVE_LEDGER.json');cost=read(ROOT/'cost-rechecked/COMPLETE_COSTS.json')
    rows=live['all_eight_arms'];by={r['arm']:r for r in rows}
    text='# RTX true-q8：原生 Windows 完整结果\n\n'
    text+='本轮完成完整资格、等工作量诊断和冻结八臂面板。q8 是真实物理验证宽度8；模型权重仍为固定 Q8_0。全部1024次正式 live 测量、128个 live primers，以及128次诊断测量、32个诊断 primers 均保留；没有删除不利格子、替换输入或 GPU 重跑。\n\n'
    text+='主要结果（k7相对k3服务时间，正数更慢）：'+'；'.join(f"{c['name']} {c['change_pct']:+.3f}%" for c in live['primary'])+'。四格同工作量q8算子的聚合点估计均较两次q4更省时；这与live宽度收益是两个不同估计目标，不能相互替代。完整成组区间和所有不利结果如下。\n\n'
    text+='## 环境、版本与资格\n\n'
    text+='RTX5070Ti Laptop，UUID GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd，12227MiB，驱动616.92；原生 Windows11 10.0.26300，Core Ultra9 275HX，24线程。接电，保持原 Windows平衡电源方案；未改驱动、功耗、系统安全设置。采样不能证明恒定频率或精确峰值。\n\n'
    text+='Qwen3-8B/0.6B Q8_0、C1024、F16 K/V、noFA；候选 target UB32/reserve8，draft prefill UB4/reserve1。k3/k7共用 reserve8。原 Windows R 保持 UB1/reserve1，原始源码、二进制和数值模块未改。数值核心沿用 #195 的两套 Windows 静态库，共享同一已绑定 CUDA 后端；新前端实际编译依赖1126项，父构建每套4986项输入复核通过。实际加载模块逐次记录并核对。\n\n'
    text+='资格消耗463/512请求，212866预留行：四个开发来源的自然重/轻捕获、cap128/32与cap1、所有请求完整词表向量、每个已提交边界 active KV/frontier、独立 pending/rollback/stop 重构、所有受控拒绝位次、全接受/bonus与correction续转、cap/EOG、reset、原生负例和 proposal tape 完整向量所有权/重放桥接均通过。严格逐位比较，无容差放宽。该有限资格不等于普遍无损或任务答案正确。\n\n'
    text+='真实宽度由 native process_ubatch 物理计数和 GPU 投影形状共同绑定，未把 caller8 当证明。LOCAL保持单次物理8行，注意力仍按协议局部分组；whole在真实 extent 边界可执行1+k等切分，未将这些跨界调用一概称为单次q8。全部请求输出均拥有完整151936维F32向量；第二次q4前复制第一批输出并在清空临时存储后复核。\n\n'
    text+='## 等工作量目标诊断\n\n'
    text+='固定四个开发来源，原始标量延续足够构造全部状态；短来源的边界为256，704-token长来源的边界为768。相同初始KV/frontier、相同八个token、全部八行输出与同一末态；无draft调用。恢复/准备在两边主计时外，必要输出物化在两边主计时内。128测量+32 primers，四次配对顺序AB、BA、BA、AB。\n\n'
    text+=table(['投影','几何','两次q4合计秒','单次q8合计秒','q8变化'],[[r['projection'],r['geometry'],f"{r['q4pair_total_s']:.6f}",f"{r['q8_total_s']:.6f}",f"{r['change_pct']:+.3f}%"] for r in same['tables']])+'\n'
    text+='四个格子为固定来源上的描述性结果，单来源反向格子保留在 SAME_WORK_RESULTS.json。不能由此直接推出 live k7 收益，也不能把主机时钟当作 kernel 时间。\n\n'
    text+='## 八臂 live 全表\n\n'
    text+='16个前瞻冻结项目内未见输出来源：8 code、8 math；cap96、prompt≤192。排除 #195/#209 正式来源并完成 #62 暴露审查，不声称训练未见。8个完整 Williams顺序块、64个长驻worker，每worker2个primers后运行16个隔离请求。每臂128次正式测量。所有端点与同期独立 Windows R 一致；R仅为正确性oracle，未作为计时M控制。\n\n'
    text+=table(['臂','服务合计秒','均值秒','target行','draft行','未消费提案','CAP/EOG'],[[r['label'],f"{r['service_total_s']:.6f}",f"{r['mean_service_s']:.6f}",r['target_physical_rows'],r['draft_physical_rows'],r['tail_unconsumed'],f"{r['cap_hits']}/{r['eog_stops']}"] for r in rows])+'\n'
    text+='## 四个预注册宽度主比较\n\n'
    text+='总服务时间之比 k7/k3；正百分数表示更慢。以16根输入为cluster重采样10000次，所有配对臂和8个顺序块一起保留，PCG64 seed20261109。四比较族 Bonferroni 98.75%双侧percentile区间，未将1024条测量当作1024个独立样本。\n\n'
    def contrasts(values):return table(['比较','变化','98.75%区间','不利根数/16'],[[r['name'],f"{r['change_pct']:+.3f}%",f"[{r['adjusted_interval_change_pct'][0]:+.3f}%, {r['adjusted_interval_change_pct'][1]:+.3f}%]",r['adverse_roots']] for r in values])
    text+=contrasts(live['primary'])+'\n'
    text+='## 独立次要机制比较族\n\n'+contrasts(live['secondary'])+'\n'
    text+='四个次要区间均包含零变化，未分辨稳定的packed或LOCAL收益；这不是等价性证明。各臂均104次cap停止、24次EOG停止，对应13个cap根和3个EOG根各重复8次，全部保留。\n\n'
    text+='![全部预注册比较与族内98.75%区间](WIDTH_EFFECTS.png)\n\n'
    text+='## 工作量与阶段成本\n\n'
    text+=table(['臂','cycles','提案','接受','不匹配拒绝','未消费尾部','VERIFY秒','draft秒','未归因residual秒'],[[r['label'],r['cycles'],r['proposed'],r['accepted'],r['rejected_incorrect_proposals'],r['tail_unconsumed'],f"{r['target_verify_s']:.6f}",f"{r['draft_sync_s']+r['draft_propose_s']:.6f}",f"{r['unassigned_residual_s']:.6f}"] for r in rows])+'\n'
    text+=table(['臂','接受/全部提案','接受/已检查','VERIFY物理行','target prefill秒','draft prefill秒','plan秒','owned-copy秒','setup秒'],[[r['label'],f"{r['accepted_over_all_proposed']*100:.3f}%",f"{r['accepted_over_inspected']*100:.3f}%",r['verify_physical_rows'],f"{r['target_prefill_s']:.6f}",f"{r['draft_prefill_s']:.6f}",f"{r['planning_s']:.6f}",f"{r['owned_output_copy_s']:.6f}",f"{r['setup_s']:.6f}"] for r in rows])+'\n'
    text+='提案=已接受+被比较且错误拒绝+未消费尾部。完整 prefill、同步、物化、reset/setup、加载、primers、首次完成结果、burst、worker、wrapper、资源采样见 COMPLETE_COSTS.json 和原始记录。inclusive时钟重叠，不能相加；residual 未归因，不能命名为日志或kernel开销。profiling=0，未测CUDA kernel/CUDA graph/API细分。\n\n'
    text+='各cut/projection的工作计数一致：k3→k7，cycles3504→2296（−34.47%），提案10512→16072（+52.89%），VERIFY物理行14016→18368（+31.05%），未消费尾部1448→5664（+291.16%）。已检查提案接受比例87.47%→87.93%，但接受/全部提案75.42%→56.94%。这符合额外提案与验证工作抵消批处理节省的解释；四来源算子诊断与正式cohort不同，不能定量相减或据此宣称唯一因果机制。\n\n'
    text+='2816个GPU功耗采样；最低全设备可用显存约2.98GiB，最低可用RAM约16.40GiB，最高温度73°C、GPU功耗140.2W。一次空闲采样的驱动查询返回46260MHz这一明显异常graphics clock，原样保留于live-s5-p0-a5资源记录，并在cost-rechecked/COMPLETE_COSTS.json补注；首版成本文件同样保留。未删除任何计时数据，也不据此推断实际频率。\n\n'
    text+='## 按session与domain的描述性敏感性\n\n'
    text+=table(['宽度比较']+[str(i) for i in range(8)],[[c['name']]+[f"{(by[c['numerator_arm']]['session_service_s'][str(i)]/by[c['denominator_arm']]['session_service_s'][str(i)]-1)*100:+.2f}%" for i in range(8)] for c in live['primary']])+'\n'
    text+=table(['宽度比较','code','math'],[[c['name']]+[f"{(by[c['numerator_arm']]['domain_service_s'][d]/by[c['denominator_arm']]['domain_service_s'][d]-1)*100:+.2f}%" for d in ('code','math')] for c in live['primary']])+'\n'
    text+='## 账本、失败与证据范围\n\n'
    text+=f"本轮新增{ledger['new_requests']}/2048请求、{ledger['new_reserved_rows']:,}预留行；继承RTX自身904请求/557528行后，累计 **{ledger['cumulative_requests']}/3072请求、{ledger['cumulative_reserved_rows']:,}/4000000行**。没有借用A5000余额，没有返还失败预留，没有自动跨阶段借用。profiling0、closure新GPU0。早期协调/审查墙钟未完整计量，明确为null；已记录子集不是完整工程总耗时。\n\n"
    text+='首次正式worker原生18请求完成后，Python后置mask读者误把caller-global行号再加偏移；已封存失败源码、冻结job和全部文件哈希，离线重核18请求并原样复用，0 GPU重跑。所有64 worker仍为同一原生前端V2和原顺序；运行间隙保留在账本与session表。另一次稀疏路径暴露读者读到0文件的无效结果已保留并替换为对 #62 固定提交39文件的完整审查；没有据此生成正式参考或计时。#210全文补读在初批资格之后、全部正式输出之前，作为事前审查顺序偏差单列；没有由此做数值/优化变更。\n\n'
    text+='冻结过程限制：设计先固定，具体资格源/任务清单按阶段递增冻结，并非所有后续资格fixture字节都在第一条资格输出前一次性发布。完整C/D源、输入、顺序、精确job/row清单和统计脚本在任何干净诊断/正式面板输出前已发布并完整回读；不得把此前分阶段准备表述为更严格的全局一次性事前冻结。\n\n'
    text+='## 可信度、限制与论文意义\n\n'
    text+='可信部分：真实native宽度、全向量/active KV有限资格、同工作量诊断、完整固定八臂和成组区间。限制：单台GPU/当前Windows实现，16个短提示来源、cap96，8个顺序块不是8个平台/8天；2s内存/功耗采样不是保证峰值，固定电源方案不等于恒频；一次后置读者修复间隙；没有kernel profiling和同期计时M。\n\n'
    text+='本轮可以回答此冻结配置下物理宽度成本及k7/k3的操作边界，并用实际cycles/rows/提案尾部和阶段时钟约束解释。不能把接受率当速度、用旧target-only数据宣称新M优越性，或把RTX与A5000在OS/CPU/驱动/来源/horizon/构建差异下的结果直接归因GPU架构。若要架构归因，需另行预注册同输入、同horizon与匹配构建的研究；本轮不自动扩展。负结果可结题。\n\n'
    text+='归档完整字节回读、从归档重算全部固定统计及GitHub回读见 ARCHIVE_READBACK.json、STATISTICS_RECOMPUTED.json、PUBLIC_READBACK.json。公开文字/哈希回读证明证据一致性，不是另一台机器的新数值资格。原始完整CAS归档及恢复目录留在本地，权重未归档。未合并PR、发布Release、删除数据、修改历史基线或论文，未运行32B/B570。\n'
    (HERE/'RESULT.md').write_text(text,encoding='utf8')
    print('Wrote complete Chinese report with all8 arms and both4-contrast families',flush=True)

if __name__=='__main__':main()
