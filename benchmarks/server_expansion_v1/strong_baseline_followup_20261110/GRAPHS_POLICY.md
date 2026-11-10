# CUDA Graphs：有界共同可行性与事前单一政策

状态：设计、未实现、未执行。**需要先登记是否激活，不是新增必跑实验或GPU授权。** graphs-off三臂比较内部有效，但只覆盖该部署，不能直接升级成最佳部署结论。

## 1. F0之前的选择

`graph_assessment_mode` 只能为：

- `off_only`（默认）：共同关闭graph。留下未研究合法capture/replay的限制；无需做为了“通过计划”而新增的GPU检查。
- `assess_common_on`（建议有明确资源与授权时采用）：按下面有限S1G核验共同可行性，随后按固定规则选**一个**共同政策。必须在任何S2/S3 clean性能输出前完成。原始R自身政策不变。

选择mode、输入、source/config/ELF、fixture、检查器、全部分支成本及共同政策规则均在F0冻结。不能先看S2或S3效果再决定是否评估on，也不能用先前heavy observer超时否定clean on。旧尝试保留为历史，不等于当前clean可行性证据。

## 2. 有限S1G（最多18候选逻辑操作）

采用已暴露开发输入的两个固定clean-path fixture：覆盖实际q1 decode及q32 prefill/合法尾列和布局；冻结具体输入/state、完整请求输出、变形规则。每fixture、每臂3次操作：

1. fresh进程中的首次合法capture；
2. 相同签名、恢复相同初始state后的replay；
3. 固定、语义合法的shape/active-length变化或reset，检验应有的invalidation/recapture及结果。

2 fixtures ×3臂 ×3操作 =**18候选操作，6 fresh workers**。并非18全部成本：独立R重复、逐列gold、初始化失败、negative、必要bridge等另计，并在原S1+S2候选256上限中逐项保留；不是额外免费18次。若后端需要额外模型warmup才能capture/replay，它们也逐次收费，不能隐藏成免费初始化；在任何模型输出前重新登记足够的完整候选清单/上限，否则不启动S1G。若两个fixture不能覆盖当前capture cache-key的关键分支，同样停止这个可选检查或在模型输出前修订完整范围/预算，不降低门禁。

native记录实际capture/replay/recapture次数、cache-key字段、stream、固定input/output指针及持有期、workspace ownership、shape/stride、物理dispatch与模块。每操作由未链接candidate补丁的同设备scalar R生成匹配完整gold/active-state要求；逐元素与完整state按既有严格合同检查。仅设置enable开关但没发生真实replay的臂不能判共同on可行。clone/reset后复用错误地址、遗漏invalidation或提前返回均失败。heavy/clean观察者桥接必须存在，不能把只有observer能工作的图当clean能力。

这只是有限feature/数值可行性检查，**不是on全模型资格，也不是on/off性能矩阵**。保存caller成本用于预算、完整日志与错误，但不根据臂间性能或C收益选政策；无额外on/off性能主张。

## 3. 事前决定规则

输出 `GRAPH_POLICY_DECISION.json`（当前只规定schema，实际文件待实现）：

```
mode, source_sha, probe_manifest_sha, per_arm_status,
actual_replay_and_invalidation_evidence, numerical_check_evidence,
on_full_qualification_manifest_and_cost, selected_policy,
fallback_reason, decision_time_utc, first_clean_request_id
```

- `off_only` → 三臂off。
- `assess_common_on` 且三个臂全部feature/gold/state通过，完整on资格在F0已登记的预算/窗口内可完成 → **选择on作为候选共同政策并完成S1全资格**。若完整on资格失败，按F0预先登记的off回退分支重新核验off完整资格；无法在原预算/窗口内完成则停止timing，不追补样本。
- 任一臂不支持、实际无复用、数值失败、证据缺失或完整on资格资源不够 → 记录具体失败/缺口，只有off三臂完整资格独立通过且其分支资源预先登记时才能用off。选择依据是合法性与资源，而不是速度排序。数值错误影响共同算术而非仅graph路径时，所有timing停止，不能借off回退隐藏共享错误。

最终政策决定及其完整资格须先于F1、首个S2 warmup与任何新根输出；一次决定贯穿S2/S3。若无法完成on，报告“当前注册条件未共同合格/未完成”，不写“on不可能”。如果资格/资源迫使停止，不能拿半套on与旧off拼比较。

任何后续政策改变需新协议与source epoch、所有受影响资格/输入/时钟/统计重冻结、独立预算，旧数据不得混池。为控制范围，此修订**不同时追加小型on/off敏感性计时**。第二卡复测沿用已经选定的共同政策；若不支持则记录复测无法完成，不独自换off再宣称复现了on。
