"""Write an outcome-focused report from independent qualification artifacts."""
from common import *
import csv

def display(value):
    if value is None:return 'null'
    if isinstance(value,float):return f'{value:.6f}'
    if isinstance(value,list):return '['+', '.join(display(x) for x in value)+']'
    return str(value)
def main():
    s=read(PUB/'S_QUALIFICATION.json');f=read(PUB/'SmolLM2_QUALIFICATION.json') if (PUB/'SmolLM2_QUALIFICATION.json').exists() else None;q=read(PUB/'Qwen_QUALIFICATION.json') if (PUB/'Qwen_QUALIFICATION.json').exists() else None;dis=read(PUB/'F_DISCOVERY.json') if (PUB/'F_DISCOVERY.json').exists() else None
    lines=['# RTX 同日补充实验记录','',f'原设计：[PR #79](https://github.com/leecdiang/HeteroSpec/pull/79)，固定设计 SHA `0e1949eaf1289f96e2ffaa83babb3b22c8c3e322`。结果：[Draft PR #80](https://github.com/leecdiang/HeteroSpec/pull/80)。','',f'按作者“越快越好、调整日期安排”的要求，S 改为 2026-10-10 同日两组独立会话，四轮、四条件、24 个原任务，共 {s["formal_completed"]}/768 次正式请求和 {s["warmups"]} 次 warmup。原六日期/十二会话不执行，跨日期稳定性和原六日置信区间未测试。','', '## 原配置复测 S','',f'状态：`{s["status"]}`。参考输出跨八次付费生成稳定：{s["stable_reference"]}。四条件各192次，完整原生 token 数组、EOS/cap、prompt、cached-token=0 核验通过；以下资格表以实际核验为准。','', '| 条件 | 完成请求 | 完整输出合格 | 分歧请求 |','|---|---:|---|---:|']
    for c,a in s['qualification'].items():lines.append(f'| {c} | {a["completed"]} | {a["qualified"]} | {a["mismatch_count"]} |')
    ratio=s['primary_request_ratio'];lines += ['',f'主比较 M/C3 的统一 resident HTTP request 加速比：**{ratio:.6f}×**（约 {(1-1/ratio)*100:.2f}% 请求延迟下降）。' if ratio else '主比较未通过完整资格，合格加速比为 null。',f'两组会话的主比较分别为 `{s["primary_session_ratios"]}`。点估计从每会话/任务/条件四轮绝对时间中位数构造24任务 log ratios，再平均两会话 log effects；不把768请求当独立样本，不给跨日期区间。','', '## 第二家族 F 与外部方法 E','', 'Llama 优先资产的官方访问返回401；按事前顺序选择 SmolLM2-1.7B-Instruct /135M-Instruct Q8_0。49152完整原生词表、special/EOG、官方 tokenizer 和 chat template 核验通过；两个发布者转换 revision、整文件 hash 固定，原始官方权重的完整转换 lineage 未认证。','', '新增确认集从完整审计的176个合格候选按预定 SHA256 排序取24个。审计覆盖全部可访问 PR/分支、本机目录及归档逻辑对象，并解码发布 transport wrapper、补扫 Windows 长路径。纯下载/候选池/分词记录不冒充模型执行；不可访问异地主机原始材料的限制保留。名单在新家族任何 forward 前锁定。']
    if dis:lines += ['', f'F discovery 完成 {dis["requests"]}/504 请求，测试16个 speculative masks 和4个 matched target controls，各12个已曝光输入、两次重复。R稳定：{dis["stable_R"]}；固定 C3 合格：{dis["fixed_C3_qualified"]}；native N0 合格：{dis["native_N0_qualified"]}。按输出资格、bit count、integer mask 选择 `{dis["selected_mask_output_only"]}`，费用未参与选择。',f'自然边界诊断：`{read(PUB/"F_NATURAL_DIAGNOSTICS.json")["status"]}`；不使用未来 proposal 强制对齐，不推出唯一 kernel 根因。']
    for model,result in [('Qwen',q),('SmolLM2',f)]:
        lines += ['',f'### {model} 确认矩阵','']
        if result is None:lines += ['未形成正式矩阵；对应工程失败/阻断记录保留，不能声称该外部缺口已补齐。'];continue
        lines += [f'{result["completed"]}/{result["planned"]} 次正式请求，warmup {result["warmups"]}；R跨所有轮次稳定：{result["stable_R"]}。', '', '| 条件 | 请求数 | 完整输出合格 | 分歧请求 | 状态 |','|---|---:|---|---:|---|']
        for c,a in result['qualification'].items():lines.append(f'| {c} | {a["completed"]} | {a["qualified"]} | {a["mismatch_count"]} | {a["status"]} |')
        lines += ['', '| 比较 | 合格 request 加速比 | 描述性24-task bootstrap 95% |','|---|---:|---|']
        for a in result['comparisons']:lines.append(f'| {a["comparison"]} | {display(a["qualified_ratio"])} | {display(a["qualified_descriptive_95pct_task_bootstrap"])} |')
        if model=='SmolLM2':lines += ['', 'F 和第二家族 E 共用这组确切 run IDs，按一次矩阵计费；两份结论不构成两份独立样本。']
    lines += ['', 'E 是 `LLM42_DVR_GGML_W32` 单请求 GGML/CUDA adaptation：共享同一 target 权重，fast UB4、verifier UB32，实际固定32-query调用；causal padding、correction/bonus、rollback 及付费 verifier-KV 复制在工程请求中验证，正式计时关闭 graph/decision traces 和 synthetic controls。它不使用 HeteroSpec mask3，也不是原 SGLang/H100 系统速度复现。', '', '每模型48个 exposed/synthetic 工程请求验证了32-query shape、padding不影响真实前缀、0/15/30位置回滚、状态精确复制、reset、cap/EOG。显式 synthetic verified-EOG 决策注入保留原生未注入 predictions，并且仅验证停止分支，不冒充自然模型选择或一致 continuation。工程有效、repeat-stable 与 ordinary R 全数组相等是独立 gate；E/R不相等时状态为 COMPLETE_CONTRACT_MISMATCH，合格 speedup/CI 为 null，并非原论文错误。', '', '## 计费、复核与范围','', '所有比较使用提交到完整 HTTP响应接收/JSON解析的统一 client perf_counter；prefill、全部在线 proposal/verify/padding、采样、KV同步/替换/rollback 和响应工作均计费。加载、teardown、规定 warmup 独立记录。E/native generation timer 边界不同，相关 generation 比较为 null。F/E各任务各条件跨 rounds 的绝对时间取中位数；10000次 paired task bootstrap，NumPy PCG64 seed20261010、type7，仅描述性。', '', '正式请求没有自动补跑、问题任务删除、passing-subset收益或参考多数票。完整 native IDs 直到首EOG包含它或cap128；功能准确率、能耗和并发吞吐没有测量。S不与F/E或历史数据池化。', '', 'S工程桥接最初在 design HEAD 上运行了尚未commit的代码；这些字节与第一提交5b3121b相同，属于工程记录。正式S在b454b72远端冻结验证后开始。旧源码/归档/论文未修改。S部分时段同时进行了CPU曝光审计和构建；GPU推理始终串行，所有预定主机准入规则通过。','', '完整数组、timers、slot ledgers、命令、native graph/state工程证明和独立CPU verifier存入内容寻址记录。`EVIDENCE_MANIFEST.json` 给出 Git 可访问的有限科学原始档案和作者本机完整source/build档案、SHA256及明确排除项；`RESTORE_CHECK.json`记录实际新目录恢复与独立重算结果。权重、发布DLL、凭证不提交Git。`REPRODUCE.md`给出恢复方法。', '', f'报告生成UTC：{now()}。']
    if f and f['status']=='INCOMPLETE':
        explanation=['', '**SmolLM2 矩阵不完整：**最后一轮 Csel/E32 两个 block 出现 `PermissionError(13)`，12个槽位无完整记录（原账本保留2个STARTED、10个MISSING_BLOCK_FAILURE）。Csel完成164/168，E32完成160/168；R/M3/C3/Msel各168次全部完成且无输出分歧。冻结的全矩阵规则使所有SmolLM2正式资格和speedup/CI为null；这不表示C3的168次数组发生了分歧。','', 'C3的完整计时记录给出的 **诊断** M3/C3=0.647699（24任务均变慢），未显示相对匹配目标的增量收益；R/C3诊断值0.987490。两者不升级为合格速度结论。原生N的42次分歧、Csel已完成请求中的26次分歧、E32已完成请求中的27次分歧均保留；Csel/E32完整重复稳定性因缺项未确立。','', '`OPERATION_FAILURE.json`保存原始错误、12个槽位和真实Windows I/O复现。普通文件读取可以阻断atomic replace；本次monitor普通读取可能参与冲突，但原错误缺stack/filename，具体锁拥有者不能确证。结合终止STARTED状态和runner控制流，错误发生在请求前账本落盘处属于推断。仅在scratch文件上验证了metadata rename的有限重试，未修改冻结实现或重新发送正式请求。后续修复/确认需独立新研究，原记录保留。','']
        index=lines.index('## 计费、复核与范围');lines[index:index]=explanation
    if (PUB/'EXECUTION_ACCOUNTING.json').exists():
        account=read(PUB/'EXECUTION_ACCOUNTING.json');count_lines=['', '### 执行次数与时间分账','', f'正式请求唯一计数 {account["formal_requests_unique"]}，工程/发现/自然诊断请求 {account["nonformal_requests_unique"]}，warmup {account["warmups"]}；合计 {account["all_full_http_requests_including_warmups"]} 次完整 HTTP 请求。第二家族 F/E 共享矩阵只计一次。','', '| 阶段 | 计划/完成请求 | 运行失败或缺失 | warmup | 完成请求 client秒总和 | resident进程秒总和 |','|---|---:|---:|---:|---:|---:|']
        for a in account['stages']:count_lines.append(f'| {a["stage"]} | {a["planned_requests"]}/{a["completed_requests"]} | {a["failed_or_missing"]} | {a["warmups"]} | {a["client_request_seconds_sum"]:.3f} | {a["resident_process_lifetimes_seconds_sum"]:.3f} |')
        count_lines += ['', '“运行失败”不包括完整但输出不一致的科学阴性，分歧全部见资格表。client总和不包括warmup；resident寿命包括加载、warmup、请求、teardown，既不等于CUDA active-kernel时间，也不包括S进程之间的冷却。起止UTC、含间隔的执行span、每条原始hash见 `EXECUTION_ACCOUNTING.json`。本轮没有独立CUDA active时间或能耗测量；E请求内全部fast/verify调用已经计入HTTP费用。自然诊断仅一个discovery分歧任务触发两次donor请求，辅助decode为0。','']
        index=lines.index('## 计费、复核与范围')+1;lines[index:index]=count_lines
    host=read(PUB/'ASSET_CHECK.json')['host']
    lines[4:4]=[f'平台：`{host["gpu"]}`；`{host["windows"]}`；单 GPU resident 请求，全部 Transformer 层 offload 到 CUDA0，FA 关闭、F16 KV、context4096、CPU线程24、AC供电。电源计划为原“平衡”，未设置 power override；风扇策略不可得，未固定或测量运行TGP。此结果描述这台 Laptop 主机和固定资产，不代表所有 RTX 型号。','']
    lines += ['', '补充核对范围：所有模型、数值DLL和native程序事后hash与冻结身份相同。普通服务器verbosity3没有记录逐层offload/memory，capture-off计时日志有实际CUDA graph执行消息；capture-on诊断不提供这些graph-reuse日志。E原日志直接记录完整offload。另对原S Qwen、新Qwen、新Smol相同assets/binary/load参数加verbose进行零前向加载检查，分别记录37/37+29/29、37/37+29/29、25/25+31/31层。此事后检查不是对每次正式启动逐层日志的追补；完整原日志保留在作者档案。见 `POSTCHECKS.json` / `POST_LOAD_OFFLOAD.json`。','']
    session_rows=list(csv.DictReader((PUB/'S_SESSIONS.csv').open(encoding='utf-8')))
    block=['', '### S 各会话比较与退化任务','', '| 会话 | 比较 | 合格 request 加速比 | 24任务中变慢数 |','|---|---|---:|---:|']
    for a in session_rows:block.append(f'| {a["session"]} | {a["comparison"]} | {display(float(a["qualified_ratio"])) if a["qualified_ratio"] else "null"} | {a["task_regressions"]} |')
    block += ['', '全部八轮效果见 `S_ROUNDS.csv`；每会话、任务、比较的两侧绝对中位数与 generation 次要指标见 `S_TASKS.csv`。F/E 每任务各条件的绝对中位数、min/max 见 `Qwen_TASKS.csv` 和 `SmolLM2_TASKS.csv`，失败输出条件也保留费用。','']
    index=lines.index('## 第二家族 F 与外部方法 E');lines[index:index]=block
    text='\n'.join(lines)+'\n';(PUB/'REPORT.md').write_text(text,encoding='utf-8');outputs=REPO.parent.parent/'outputs';outputs.mkdir(exist_ok=True);(outputs/'HeteroSpec_RTX_同日补充实验报告.md').write_text(text,encoding='utf-8');print('REPORT WRITTEN',flush=True)
if __name__=='__main__':main()
