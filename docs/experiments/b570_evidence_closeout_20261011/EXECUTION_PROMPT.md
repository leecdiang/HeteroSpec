# B570 执行端完整提示词

**“完成 PR90”是本文件的简写：完成实现、真实平台实验、独立核验和结果 Draft PR；不是仅 review、合并或运行 CPU tests。先读 [FINAL_REVIEW.md](FINAL_REVIEW.md)，并执行本 PR 最新 HEAD。**

请在真实 Intel Arc B570 主机持续完成 HeteroSpec 最终驻留边界、修复成本与盈亏平衡补全，并创建独立结果 Draft PR。

仓库：https://github.com/leecdiang/HeteroSpec
执行设计：https://github.com/leecdiang/HeteroSpec/pull/90
设计分支：codex/b570-evidence-closeout-plan-20261011
已绑定原结果：#88 / 4db9bc501fa01c76db50721e7d11e9a0d1e53782

我已授权本主机执行协议内有界实验、实现必要的新控制/计数/观测层、保留完整档案和创建结果Draft PR。请完成到可核验结果或停止报告，不停在计划。不要合并、修改论文/release，不启动Q8或新精度/k搜索。

1. 先核对 #90 最新实际HEAD/base/#88与工作树，完整读取 docs/experiments/b570_evidence_closeout_20261011/ 中 README、FINAL_REVIEW、ASSESSMENT、CLAIM_EVIDENCE、PROTOCOL、MECHANISM_PROTOCOL、DESIGN、ASSETS、SOURCE_BINDINGS、MINIMUM_EXCLUSIONS、EVIDENCE_AUDIT、RECORD_SCHEMA、CPU_VALIDATION与本文件。采用最新含机制扩展的设计字节，新建结果分支接在实际#90 HEAD；#88已停止账本不重开。
2. 实际Git/CAS恢复#88所有必要source/binary/DLL和模型hash；保留完整旧字节与未认证来源。固定Llama target Q6_K / draft Q4_K_M / k1、ctx1024、F16 KV、FAoff、greedy seed123、threads10、draftUB1、logical512、prompt<=768、cap128。五arms R_stock普通UB128、R_prod普通UB512、M_match、N_k1、C_k1依DESIGN；repair continuation物理UB1、capacity4不能变成RTX query-batch并行或为了快而缩容量。
3. 先运行trace_preflight.ps1只读盘点。新load前冻结F0P并实际push/remote逐字节读回。在最多6个zero-forward load/trace单元、60分钟诊断内取得真实工具运行、B570 LUID/PID与模型weights/KV allocation关联；零forward不得有hidden warmup。无权限/工具、loss或无法关联时保存具体错误，不自动提权、停他人trace、改驱动/电源或循环安装。
4. P0无法取得物理证据时记RESIDENCY_PROOF_UNAVAILABLE，结束继续追trace，不能把UNKNOWN写成PASS。它不阻止输出/实际费用研究：实际same-worker signed headroom>=512MiB、全部weights/KV GPU放置日志、无已知分配失败/offload/相关paging或eviction才可forward；真实资源失败仍停止。冻结F0A并remote读回；核心工程256（含最多6探针与核心warmup/失败/修复）+独立profiling128=384，owned8小时、outer7天，不借旧预算。
5. 在counts正式通道的工程对照中，五arms×12曝光题×2重复支付稳定完整Q6参考。核验完整raw IDs/EOG/length/terminal/stop、actualUB/capacity、phase/reset/verify/rollback、cap边界、768最长prompt。关闭#88重型compute callbacks/full KV readback后的新通道必须完整输出对照且source差异可核验。独立工程trace若可用，由decoder解码ETL/分配映射，按原严格条件核验实际范围；其成功不能外推正式worker。CPU结构receipt不能代替真实证据；缺proof记录UNKNOWN，运行门槛照常验证。
6. 原生资格与主费用优先。固定6曝光题（3MBPP+3GSM8K）、四profile arms×baseline/counts/lite/heavy共96测量槽，加32个加载/预热/失败余量，共独立128 profiling paid预算。分别报告counts-baseline、lite-counts扰动；ETW只在独立heavy工程驻留观察开启。正式固定counts、关闭phase elapsed/heavy/实验ETW/新增同步，真实剩余开销照常计费，不扣除估算开销。
7. 记录精确定义Acceptance分母/proposal去向/每周期实际进展；draft prefill/proposal/catch-up调用与行数；target verification/replay/fallback逻辑宽度、实际物理UB1工作；phase binding/rollback/sampling/sync/channel及prompt/output/停止/固定长度桶。没有GPU完成计时就null，enqueue跨度或R/N、N/C不同输出的费用差不当純修复算子税。
8. 用6曝光题的有效lite互斥wall成本校准本平台/本Q6运行时的冻结Break-Even模型。参数不得来自RTX、旧358H或新确认；没有有效完成span则冻结MODEL_TIMING_UNAVAILABLE及原因，继续原生证据收尾，不改算术路径或扩预算追成功。按MECHANISM_PROTOCOL检验零draft分项的条件性预测时保留已观察work/进展，不能称普适上界。
9. 全历史审计后按奇数description桶固定新12MBPP+12GSM8K，与RTX正式新题分离。F0B封存source/model/DLL/观测/独立decoder、五arm与计数、全部输入/native IDs、排程/统计及校准模型字节，实际remote读回先于formal warmup。固定R_prod与C，不因已知负工程收益另选候选。
10. 运行与原生资格通过则完成1200formal+50warm五arm五轮两连续会话。实际费用报告request_qualified_ratio；工程ETL不能替代正式worker证明，缺少正式同范围证据时严格resident qualified_ratio仍null。正式retry0、不补槽、不换题、不裁raw后缀、不因负收益取消已准入C。无关N输出失败不抹去完整R/M/C比较。
11. closeout.py analyse生成comparison-specific资格、null与费用；mechanism.py analyse用冻结参数与新题work验证MAE/MAPE、matched/prod盈亏方向、全部域/长度/停止分层、残差和未覆盖形状。模型为执行后work的条件性解释，不是online selector。无法解释或预测负收益都如实报告，不重新拟合。跨平台精度/实现/计时不同，不能把RTX Qwen1.106与历史约1.035当优化提升。
12. 交付独立 benchmarks/b570_evidence_closeout_v1：完整raw、实际取得的ETL/decoder/分配映射及缺项原因、全部ledger/source/binary/worker生命周期、workload/校准/模型/验证JSON、MECHANISM_REPORT、成本分解与预测–实测图、物理证明范围及负例/停止原因。完成真实独立CPU复算、local与认证Git档案恢复/读回后创建结果Draft PR，base为实际#90分支。物理UNKNOWN、模型不通过和性能负收益分开报告；只有真实资源/源码/输出/预算阻断才按范围停止。F0B前预估完整确认余量，普通会话中断可恢复未启动槽；已启动槽不可重跑。结果不承诺正收益。

CPU命令模板（不启动GPU）：
```bash
python scripts/platform/b570_evidence_closeout_v1/closeout.py --design docs/experiments/b570_evidence_closeout_20261011/DESIGN.json validate
python -m unittest discover -s scripts/platform/b570_evidence_closeout_v1 -p 'test_*.py'
python scripts/platform/b570_evidence_closeout_v1/mechanism.py --design docs/experiments/b570_evidence_closeout_20261011/DESIGN.json calibrate --calibration <MODEL_CALIBRATION.json> --out <BREAK_EVEN_MODEL.json>
python scripts/platform/b570_evidence_closeout_v1/closeout.py --design docs/experiments/b570_evidence_closeout_20261011/DESIGN.json schedule --inputs <new_confirmation_inputs.json> --out <new_formal_plan.json>
python scripts/platform/b570_evidence_closeout_v1/mechanism.py --design docs/experiments/b570_evidence_closeout_20261011/DESIGN.json analyse --plan <new_formal_plan.json> --inputs <new_confirmation_inputs.json> --records <formal_records.json> --freeze <F0B.json> --model <BREAK_EVEN_MODEL.json> --out <MODEL_VALIDATION.json>
```
有与正式worker对应的独立物理证明时才另外传 --residency；工程receipt独立存档，不能传入冒充正式证据。占位必须填真实数据与封存信息；缺模型或proof时使用协议明确的缺项状态，不因此取消合格主费用确认，不制造证书或曲线。持续执行到交付或停止线。
