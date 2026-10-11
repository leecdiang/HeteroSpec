"""Report all predeclared comparisons; retain incomplete and negative results."""
from common import *
def main():
    a=read(PUB/'RESULTS.json');lines=['# HeteroSpec RTX 三家族连续会话实验','',f'按 PR #83 `{DESIGN_SHA}` 执行独立新研究。正式计划3456次，完成{a["completed"]}次。实际日期见逐请求 UTC 记录；笔记本屏幕在本研究任何 forward 前切到核显，推理使用 RTX 5070 Ti Laptop。','', '本研究遵照事前快跑修订，采用每家族两个连续独立会话、每会话四轮，并不具备六个独立日期。下表为完整原生输出资格通过时的描述性倍数；跨日置信区间和稳定收益判定均未测试。','', '| 家族 | 完整稳定 R | M3/C3_K3 | R/C3_K3 | R/M3 |','|---|---|---:|---:|---:|']
    def ratio(v):return 'null（资格未通过）' if v is None else f'{v:.6f}×'
    for family,f in a['families'].items():
        comparisons={r['comparison']:r for r in f['comparisons']};lines.append('| '+family+' | '+('是' if f['stable_complete_R'] else '否')+' | '+' | '.join(ratio(comparisons[c]['qualified_ratio']) for c in ['M3/C3_K3','R/C3_K3','R/M3'])+' |')
    lines+=['','主比较固定为 Llama M3/C3_K3。M3 为相同 targetUB4/mask3 的目标路径对照；R 为普通 greedy/UB1。唯一主计时包含完整 resident HTTP 提交、接收和 JSON 解析；加载和 synthetic warmup 分开计账。','', '## 全部条件与敏感性结果','']
    for family,f in a['families'].items():
        lines += [f'### {family}','', '| 条件 | 完成/计划 | 资格 | 与实付 R 分歧 |','|---|---:|---|---:|']
        for c,q in f['qualification'].items():lines.append(f'| {c} | {q["completed"]}/{q["planned"]} | {q["status"]} | {q["mismatch_count"]} |')
        lines += ['', '| 比较 | 合格描述性倍数 | 两会话倍数 | MBPP | GSM8K | 回归任务数 |','|---|---:|---|---:|---:|---:|']
        for c in f['comparisons']:lines.append('| '+c['comparison']+' | '+ratio(c['qualified_ratio'])+' | '+', '.join(ratio(v) for v in c['session_ratios'])+' | '+ratio(c['domain_qualified_ratios']['MBPP'])+' | '+ratio(c['domain_qualified_ratios']['GSM8K'])+' | '+str(len(c['regressions']))+' |')
        lines+=['']
    lines+=['## 记录和复算','', '所有192个计划槽位均为各条件资格分母。只按完整 runtime-native IDs、length/terminal/stop reason 比较所有实际 paid R；原始 suffix、FAILED/STARTED/MISSING 全部保留，不截断取合格、不补跑正式槽位。无关 N/k1 条件缺失不会消除已经完整的 R/M3/C3_K3 比较。','', '每任务/条件/会话先取四轮绝对 HTTP 费用中位数，再平均24个任务的 log ratio，最后平均两会话。每域、每会话和回归任务均记录在 RESULTS.json。k1/k2 全部报告，没有改选主配置或将请求数当独立日期样本。','', '全量 offload、F16 KV、ctx1024、FA off、single seq、threads24；请求 logical batch2048 被未改动原生 runtime 限制为有效1024。targetUB1/4，draftUB1。三家族共用发布数值 DLL，完整 SHA256 绑定。Llama target/draft 使用目标模板同一套 IDs；conversion 只认证公开发布字节/revision，未认证官方原始 checkpoint 转换血缘。','', '工程阶段实际 proposal/accept/reject/bonus/correction、verify宽度、rollback、head shapes、scope/reset、graph reuse 与 capture-on/off 对照见 ENGINEERING_RESULTS.json。逐 phase GPU timer 不充分时明确留空；capture 同步开销不当作正式费用，也不声称唯一算子因果。','', 'RAW_EVIDENCE.zip 为 CPU 复算包；完整私有源码/程序在单独 author archive，模型和数值 DLL 外置按 hash 绑定。独立本地恢复与实际认证远端读回的 CPU 复算凭证分别见 RESTORE_LOCAL.json、RESTORE_REMOTE.json。旧 PR #80/#82 结果不改写，未修改论文、release，也未合并 PR。','']
    text='\n'.join(lines);p=PUB/'RESULTS.md';assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n');out=REPO.parent.parent/'outputs/HeteroSpec_RTX_三家族同日实验_报告.md';assert not out.exists();out.write_text(text,encoding='utf-8',newline='\n')
    print('REPORT WRITTEN',out,flush=True)
if __name__=='__main__':main()
