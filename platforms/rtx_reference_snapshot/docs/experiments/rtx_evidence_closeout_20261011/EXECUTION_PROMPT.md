# RTX 执行端完整提示词

**“完成 PR89”是本文件的简写：完成实现、真实平台实验、独立核验和结果 Draft PR；不是仅 review、合并或运行 CPU tests。先读 [FINAL_REVIEW.md](FINAL_REVIEW.md)，并执行本 PR 最新 HEAD。**

请在真实 RTX 5070 Ti Laptop 主机持续完成 HeteroSpec 最终证据补全，并创建独立结果 Draft PR。

仓库：https://github.com/leecdiang/HeteroSpec
执行设计：https://github.com/leecdiang/HeteroSpec/pull/89
设计分支：codex/rtx-evidence-closeout-plan-20261011
已绑定原结果：#84 / 59b0f87a7011dad15f5e1146591ae83d9556d0e7

我已授权本主机执行这个有界实验、实现必要的新控制/计数层、保存完整科学档案和创建结果 Draft PR。请完成到可核验结果或协议停止报告，不停在计划。不要合并、修改论文/release或启动本范围外模型搜索。

1. 先核对 #89 实际最新 HEAD、base、#84 来源与工作树，完整读取 docs/experiments/rtx_evidence_closeout_20261011/ 中 README、FINAL_REVIEW、ASSESSMENT、CLAIM_EVIDENCE、PROTOCOL、MECHANISM_PROTOCOL、DESIGN、ASSETS、SOURCE_BINDINGS、MINIMUM_EXCLUSIONS、EVIDENCE_AUDIT、PRIOR_WORKLOAD_AUDIT、RECORD_SCHEMA、CPU_VALIDATION 和本文件。以实际读取字节执行；设计HEAD若更新要用最新内容，不能沿用先前未含机制扩展的commit。原始结果与冻结均只读，新建结果分支接在实际 #89 HEAD 上。
2. 实际恢复 #84 的完整作者 source/binary/DLL/CAS 和模型字节，核验哈希、native IDs/EOG、模板、加载GPU/UB/capacity与原计时。此设计的CPU复算没有替你恢复完整raw archive，也没有编译native。保留来源未认证项，不凭报告宣布恢复完成。
3. 保持三家族 Qwen/SmolLM2/Llama、绑定Q8文件、k3、ctx1024、F16 KV、FAoff、greedy seed123、threads24、draftUB1、batch requested2048/effective1024、prompt<=768、cap128。建立独立 single-writer ledger/worker/controller，所有失败、加载、预热和实现修复收费，正式 retry0。新数值路径不调参。
4. 新forward前封存 F0A（源码/完整依赖/设计、曝光工程与校准输入、观测、计时、预算），commit/push并实际认证Git blob逐字节读回。工程每家族核心360+profiling128=488，总1464；owned进程16小时，outer7天。不依赖Codex/OpenAI API轮询。
5. 核心工程费用使用与正式相同的counts通道。按固定 ordinary UB1/4/32/128/512×12曝光题×2重复，支付稳定UB1参考并选择完整保持参考输出的R_prod；只按工程费用选择并冻结，不看新确认速度。验证 R/M0/M3/R_prod/C3、工程N，以及实际phase/reset/graph/cap/EOG/rollback/最长输入。资格按比较独立，保留失败条件和全部负成本。
6. 机制解释是本轮必做的有界尝试：按DESIGN中6个旧曝光任务（3MBPP+3GSM8K）与 R/R_prod/M3/C3 四arm，执行固定 baseline/counts/lite/heavy 四模式，共96测量槽/家族，另有32个加载/预热/失败余量，计入独立profiling128，不挤占核心360。核验四模式完整raw输出与计数语义，报告counts-baseline与lite-counts扰动；heavy形状/同步时间不得用于正式费用拟合，不新增同步把enqueue时间变GPU时间。
7. 精确记录Acceptance两种分母、proposal五种去向、每周期接受前缀/实际进展、draft prefill/proposal/catch-up调用及行数、target prefill/verify/replay/fallback调用宽度及实际物理工作、rollback/sampling/sync/channel成本，以及prompt/output IDs、EOG/CAP和固定长度桶。原生计数先审计映射，不把所有未接受proposal叫拒绝。
8. 用6曝光任务的有效lite互斥完成wall分项校准MECHANISM_PROTOCOL指定的一阶Break-Even模型，按family/arm拟合，禁止按域或新题重新拟合。工程阶段冻结MODEL_CALIBRATION和BREAK_EVEN_MODEL；没有可用完成span则冻结MODEL_TIMING_UNAVAILABLE及原因，仍收尾原生资格/成本，不扩预算追成功。它是利用执行后work的条件性解释模型，不是online选择器。
9. 全可访问历史按ID与描述排除后，按原偶数description桶准备新12MBPP+12GSM8K题；最小排除表不能代替全历史审计。共同F0B封存R_prod、全部输入/native IDs、source/runtime/计数/观测/排程/统计和模型字节，并实际remote读回，先于任何新确认warmup/forward。不能为Smol变快换题/改k/改草稿。
10. 运行全部5arms×24题×5轮×2连续会话×3家族=3600formal+150warm，位置平衡和顺序由schedule生成。正式固定counts，只保留轻量整数计数和完整请求起止计时，关闭分项elapsed/heavy/实验ETW/新增同步。记录真实费用，不扣除估计观测开销；模型残差另解释lite→counts转移。合格Smol即使负收益也完成确认，不补槽、不覆盖、不裁输出、不根据域在线routing。
11. closeout.py analyse独立核验完整raw资格与双基线成本；mechanism.py analyse只用新题work和冻结参数验证预测、MAPE/MAE、signed residual、matched/prod break-even方向、域/长度/停止分层。按全任务/会话分母展示未覆盖形状、缺计数、近盈亏边界和模型否证，不用新确认wall调系数。Qwen新1.106与历史约1.035只能列来源/设计差异，不宣称优化提升。
12. 交付独立 benchmarks/rtx_evidence_closeout_v1 的完整raw arrays/ledger、源码/binary/模型绑定、所有ordinary候选、phase/counter证据、WORKLOAD_RECORDS、校准/模型/验证JSON、MECHANISM_REPORT和分解图/预测–实测散点，以及中文结果、全部负例/停止原因。真实独立CPU复算、本地和认证Git科学档案恢复/读回完成后创建结果Draft PR，base为本次实际#89分支。F0B前记录按真实工程耗时预估的确认余量；预算/源码/资格阻断时提交具体停止报告，不能临时重选方案。普通会话中断可从持久账本继续未启动槽，已启动槽不重跑。

CPU命令模板（不启动GPU）：
```bash
python scripts/platform/rtx_evidence_closeout_v1/closeout.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json validate
python -m unittest discover -s scripts/platform/rtx_evidence_closeout_v1 -p 'test_*.py'
python scripts/platform/rtx_evidence_closeout_v1/closeout.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json select-ordinary --rows <exposed_ordinary_rows.json> --out <selected_ordinary.json>
python scripts/platform/rtx_evidence_closeout_v1/mechanism.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json calibrate --calibration <MODEL_CALIBRATION.json> --out <BREAK_EVEN_MODEL.json>
python scripts/platform/rtx_evidence_closeout_v1/closeout.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json schedule --inputs <new_confirmation_inputs.json> --ordinary <selected_ordinary.json> --out <new_formal_plan.json>
python scripts/platform/rtx_evidence_closeout_v1/mechanism.py --design docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json analyse --plan <new_formal_plan.json> --inputs <new_confirmation_inputs.json> --records <formal_records.json> --freeze <F0B.json> --model <BREAK_EVEN_MODEL.json> --out <MODEL_VALIDATION.json>
```
所有尖括号都是接口占位；填写真实导出与封存信息，不制造数据。持续执行到上述交付完成或协议停止线。
