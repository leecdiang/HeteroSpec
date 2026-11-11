# RTX closeout：真实平台结果

设计 #89 / `e2d5dcbc224c086d1d6804de8ed925182bfa1404`，继承 #84 / `59b0f87a7011dad15f5e1146591ae83d9556d0e7`。本次正式计划3600槽，已支付输出与费用按完整原生数组逐项核验；cap128、五轮中位数、两连续会话等权。负结果和不合格比较均保留。

工程选出的普通 UB：`{'Qwen': 1, 'SmolLM2': 512, 'Llama': 512}`。只按12个旧曝光题×2次完整保持参考的工程费用选择，未看新确认结果。

|家族|比较|合格请求费用比|
|---|---|---|
|Qwen|R_prod/C3|1.569566275855531|
|Qwen|M3/C3|1.1349240341315152|
|Qwen|R/C3|1.5699772960883824|
|Qwen|M0/M3|未合格 / 缺项|
|Qwen|R/M0|未合格 / 缺项|
|Qwen|R/M3|1.3833324952799908|
|Qwen|R_prod/M3|1.3829703386770023|
|SmolLM2|R_prod/C3|未合格 / 缺项|
|SmolLM2|M3/C3|0.6073886093892048|
|SmolLM2|R/C3|0.8771743203302574|
|SmolLM2|M0/M3|未合格 / 缺项|
|SmolLM2|R/M0|未合格 / 缺项|
|SmolLM2|R/M3|1.4441731484104576|
|SmolLM2|R_prod/M3|未合格 / 缺项|
|Llama|R_prod/C3|未合格 / 缺项|
|Llama|M3/C3|1.0722272787268143|
|Llama|R/C3|1.6094676913804737|
|Llama|M0/M3|未合格 / 缺项|
|Llama|R/M0|未合格 / 缺项|
|Llama|R/M3|1.501050871687941|
|Llama|R_prod/M3|未合格 / 缺项|

比值>1表示候选请求费用更低。R_prod/C3用于普通部署基线比较，M3/C3用于目标路径匹配的增量draft收益。完整域、任务、会话和退化项见 RESULTS.json；不据此按域在线分流。

分阶段盈亏模型：MODEL_TIMING_UNAVAILABLE。72个真实lite请求已保留enqueue与自然采样就绪标记；异步完成与重叠不能证明规定的互斥完成wall分解。没有增加同步，没有编造系数，也没有用新确认费用拟合。轻量原生计数、四模式输出核验和配对观测扰动另见机制报告。

公开转换文件的完整字节已认证；官方checkpoint转换血缘仍未认证。其他私有主机、不可达历史和预训练内容未观测，不宣称全局未见任务。跨日期置信区间、能源、多请求吞吐不属于本次证据。

完整记录、源码和计数语义、实际命令/模块/内存日志、已支付失败、原始ID与生命周期收录于 RAW_EVIDENCE 分片档案与本地作者档案。独立CPU及实际本地/远端档案恢复核验收据随结果保留。

档案恢复：按照 RAW_EVIDENCE_PARTS.json 顺序连接分片，逐片、完整 ZIP 与 INDEX 内每个文件的 SHA256 全部核验。此修复只处理已完成实验的交付大小上限，未重新推理或修改固定计划。

## 不合格比较与全部退化项

比值小于1表示候选更慢；不合格诊断比值不能作为合格加速结论。资格只覆盖冻结 counts 通道中的请求费用和完整原生输出，物理驻留与运营内存资格在 RESULTS.json 中保留 null，不扩张为这些结论。

### Qwen

- M0 未通过完整原生输出资格：50 / 240 槽不一致；题目：GSM8K/test/141, GSM8K/test/443, GSM8K/test/562, GSM8K/test/660, GSM8K/test/722。
- M0/M3：合格比值 不可用；完整费用诊断比值 0.968456；退化题：MBPP/56, MBPP/473, MBPP/450, MBPP/476, MBPP/140, MBPP/123, MBPP/79, MBPP/401, MBPP/255, MBPP/413, MBPP/99, GSM8K/test/854, GSM8K/test/141, GSM8K/test/574, GSM8K/test/660, GSM8K/test/111, GSM8K/test/1308, GSM8K/test/443, GSM8K/test/120, GSM8K/test/722, GSM8K/test/724, GSM8K/test/322, GSM8K/test/562。
- R/M0：合格比值 不可用；完整费用诊断比值 1.428390；退化题：无。

### SmolLM2

- M0 未通过完整原生输出资格：140 / 240 槽不一致；题目：GSM8K/test/111, GSM8K/test/120, GSM8K/test/1308, GSM8K/test/141, GSM8K/test/322, GSM8K/test/562, GSM8K/test/574, GSM8K/test/660, GSM8K/test/724, GSM8K/test/854, MBPP/123, MBPP/401, MBPP/418, MBPP/450。
- R_prod 未通过完整原生输出资格：140 / 240 槽不一致；题目：GSM8K/test/111, GSM8K/test/1308, GSM8K/test/141, GSM8K/test/322, GSM8K/test/562, GSM8K/test/660, GSM8K/test/724, GSM8K/test/854, MBPP/123, MBPP/255, MBPP/401, MBPP/418, MBPP/450, MBPP/473。
- R_prod/C3：合格比值 不可用；完整费用诊断比值 0.512333；退化题：MBPP/56, MBPP/418, MBPP/450, MBPP/476, MBPP/140, MBPP/123, MBPP/79, MBPP/401, MBPP/255, MBPP/413, MBPP/99, GSM8K/test/854, GSM8K/test/141, GSM8K/test/574, GSM8K/test/660, GSM8K/test/111, GSM8K/test/1308, GSM8K/test/443, GSM8K/test/120, GSM8K/test/722, GSM8K/test/724, GSM8K/test/322, GSM8K/test/562。
- M3/C3：合格比值 0.607389；完整费用诊断比值 0.607389；退化题：MBPP/56, MBPP/418, MBPP/473, MBPP/450, MBPP/476, MBPP/140, MBPP/123, MBPP/79, MBPP/401, MBPP/255, MBPP/413, MBPP/99, GSM8K/test/854, GSM8K/test/141, GSM8K/test/574, GSM8K/test/660, GSM8K/test/111, GSM8K/test/1308, GSM8K/test/443, GSM8K/test/120, GSM8K/test/722, GSM8K/test/724, GSM8K/test/322, GSM8K/test/562。
- R/C3：合格比值 0.877174；完整费用诊断比值 0.877174；退化题：MBPP/56, MBPP/418, MBPP/473, MBPP/450, MBPP/140, MBPP/123, MBPP/401, MBPP/413, GSM8K/test/854, GSM8K/test/141, GSM8K/test/574, GSM8K/test/660, GSM8K/test/111, GSM8K/test/1308, GSM8K/test/443, GSM8K/test/120, GSM8K/test/722, GSM8K/test/724, GSM8K/test/322, GSM8K/test/562。
- M0/M3：合格比值 不可用；完整费用诊断比值 0.948603；退化题：MBPP/56, MBPP/418, MBPP/473, MBPP/450, MBPP/476, MBPP/140, MBPP/123, MBPP/79, MBPP/401, MBPP/255, MBPP/413, MBPP/99, GSM8K/test/854, GSM8K/test/141, GSM8K/test/574, GSM8K/test/660, GSM8K/test/111, GSM8K/test/1308, GSM8K/test/443, GSM8K/test/120, GSM8K/test/722, GSM8K/test/724, GSM8K/test/562。
- R/M0：合格比值 不可用；完整费用诊断比值 1.522421；退化题：无。
- R_prod/M3：合格比值 不可用；完整费用诊断比值 0.843502；退化题：MBPP/56, MBPP/418, MBPP/450, MBPP/476, MBPP/140, MBPP/123, MBPP/79, MBPP/401, MBPP/255, MBPP/413, MBPP/99, GSM8K/test/854, GSM8K/test/141, GSM8K/test/574, GSM8K/test/660, GSM8K/test/111, GSM8K/test/1308, GSM8K/test/443, GSM8K/test/120, GSM8K/test/722, GSM8K/test/724, GSM8K/test/322, GSM8K/test/562。

### Llama

- M0 未通过完整原生输出资格：90 / 240 槽不一致；题目：GSM8K/test/120, GSM8K/test/1308, GSM8K/test/322, GSM8K/test/443, GSM8K/test/574, GSM8K/test/724, MBPP/255, MBPP/450, MBPP/56。
- R_prod 未通过完整原生输出资格：80 / 240 槽不一致；题目：GSM8K/test/1308, GSM8K/test/443, GSM8K/test/562, GSM8K/test/574, MBPP/123, MBPP/255, MBPP/401, MBPP/56。
- R_prod/C3：合格比值 不可用；完整费用诊断比值 0.842790；退化题：MBPP/56, MBPP/418, MBPP/476, MBPP/79, MBPP/255, MBPP/413, MBPP/99, GSM8K/test/854, GSM8K/test/574, GSM8K/test/111, GSM8K/test/443, GSM8K/test/722, GSM8K/test/724, GSM8K/test/322, GSM8K/test/562。
- M3/C3：合格比值 1.072227；完整费用诊断比值 1.072227；退化题：MBPP/418, MBPP/476, MBPP/79, MBPP/99。
- M0/M3：合格比值 不可用；完整费用诊断比值 0.936943；退化题：MBPP/56, MBPP/418, MBPP/476, MBPP/140, MBPP/123, MBPP/79, MBPP/401, MBPP/255, GSM8K/test/854, GSM8K/test/141, GSM8K/test/574, GSM8K/test/660, GSM8K/test/111, GSM8K/test/1308, GSM8K/test/443, GSM8K/test/722, GSM8K/test/724, GSM8K/test/322, GSM8K/test/562。
- R/M0：合格比值 不可用；完整费用诊断比值 1.602073；退化题：无。
- R_prod/M3：合格比值 不可用；完整费用诊断比值 0.786018；退化题：MBPP/56, MBPP/418, MBPP/473, MBPP/476, MBPP/140, MBPP/123, MBPP/79, MBPP/401, MBPP/255, MBPP/413, MBPP/99, GSM8K/test/854, GSM8K/test/141, GSM8K/test/574, GSM8K/test/660, GSM8K/test/111, GSM8K/test/1308, GSM8K/test/443, GSM8K/test/120, GSM8K/test/722, GSM8K/test/724, GSM8K/test/322, GSM8K/test/562。
