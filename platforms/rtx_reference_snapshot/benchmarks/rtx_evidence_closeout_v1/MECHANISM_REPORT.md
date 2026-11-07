# 工作量与模型核验

全部已支付请求保留；主输出/费用资格与工作计数、模型覆盖独立判断。

实际proposal五种去向、两种接受率、周期进展/位置、target/draft caller与物理micrograph计数见 WORKLOAD_RECORDS.json，轻重模式核对见 HEAVY_COUNTER_AUDIT.json。物理行计数不等于硬件占用。

四观测模式逐题费用与完整raw一致性见 OBSERVER_OVERHEAD.json。单次差值为描述性配对，不能当精确观测因果开销，不从正式费用中扣除。

MODEL_TIMING_UNAVAILABLE：实际lite hooks只证明API排队和自然采样就绪，无法形成规定basis下完整请求wall的互斥完成跨度。component_ms、系数、GPU event费用、预测、MAPE、MAE、signed residual与break-even方向均不可用；覆盖分母与缺项在 MODEL_VALIDATION.json 全部保留。没有确认后重拟合。

缺失/不合格计数槽数：0。固定prompt/output bins、域/EOG/CAP及负例见 LENGTH_DOMAIN_STOP_RECORDS.json 和 RESULTS.json。

图中只展示实测完整费用和原生工作量；费用分项与预测散点留空并标明不可用。旧Qwen1.106与历史约1.035分别属于不同冻结/面板/计时，不声称本轮代码优化提升。
