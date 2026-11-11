# RTX 第一阶段：归因与实际部署成本

基线结果：PR190 `a28f3474acac793d07b6e6f462cb70bbccfa6ceb`。
强算子控制：PR186 `e8f1ea5aaa35789216801dd971b17e7d5e9f090f`。
数值R仍采用对应当前C1024部署的冻结原执行，不改变旧PR中的身份。

## R0：无GPU准备

1. 从当前保存的逐请求记录汇总 planning/output-copy/prefill/continuation 的成本和物理切分密度；不把kernel activity数当作耗时。
2. 检查现有 source staging，抽出一个公共接口：cut_scope=whole/local，projection=loop4/packed。新建独立候选，不覆盖原工件。
3. 统一编译、优化级别、graph reuse、输出收集与记录路径，只允许因素对应的变换不同。
4. 检查两个混合臂是否是真实不同路径。用原生 trace 证明，不只看flags。
5. 给出最小源码/构建/模型哈希/样例入口，不要求下载全部历史几十GB归档才能编译。
6. 检查自然M的q32从0开始、P=256时的对齐。此时whole/local可能退化成相同切分，须进一步核对实际算子、dispatch、front-end bookkeeping与计时路径，不能只凭group数相等认定完全等同。若两个混合臂是已测路径的别名，或自然比较仅重复PR186的packing问题，就取消下述新自然确认，保留机制分解和旧完整请求证据。不得通过padding或挑offset重新制造自然优势。

## R1：2×2实现归因（主任务）

| 臂 | 图切分 | Projection |
|---|---|---|
| W_L4 | whole graph，边界后重新对齐 | backend-loop4 |
| W_P | 同上 | packed |
| L_L4 | local attention | backend-loop4 |
| L_P | 同上 | packed |

主工作负载先用普通生成M，隔离 draft acceptance、proposal 和同步成本。模型仍为已有Qwen3-8B、SmolLM2-1.7B，Q8_0/F16 KV/no-FA/C1024/greedy/cap128。匹配模型/context驻留与当前研究保持一致；真正不装draft的基线留给R2。外层宽度维持32，q<=4不触发宽packing的事实作为负控制。

### 开发和资格

使用固定的每模型4个已暴露根，保留已知边界反例。完整要求由真实cache和绑定的backend recipe导出。原R的producer、UB1、最后输出mask、输出reserve不改变。验证原请求向量、已提交active KV、正确frontier和停止行为；M不能通过改变参考的prefill调用方式得到PASS。

已存在的等同路径可以复用相同版本的资格；新混合臂必须自己的原生资格。编译失败不等于科学负结果，但数值失败不能跳过。

固定几何诊断每模型6格：q=4,8,32，各有B=768的桶内head B-q 与跨界head B-1。总12个模型/几何坐标。每格四臂2次配对测量及同臂预热，共96+96个append执行。真实token tape来自冻结的已暴露材料；若切取prefix用于固定H，这明确是known-token机制诊断，不是自然请求或自然跨界频率。宽q只请求原mask所需行，不扩展oracle输出容量方便观察。

### 新自然确认（条件项，不自动开启）

准入需要：四个组合可合法运行；实际变换有可区分的新机制；已有PR186/190不能回答这个问题。**资格通过本身不是新增数百测量的理由。** 自然对齐导致因素无效时，机制矩阵已经足够回答该处问题，直接进入R2或可移植性，不重复旧面板。

- 每模型16个此前未曝光根：数学8、代码8；两模型各自分析。
- 源版本、prompt模板、native tokenizer、身份/文本曝光排除、长度准入和排序seed在读取输出前冻结。
- 容量准入不得根据crossing、答案、acceptance或速度选样；不padding或拼接来制造边界。
- 每模型16根×4臂×4 sessions，合计512测量+512即时同臂预热。
- 每根每session的四臂用4×4 Williams顺序，sessions跨独立运行时段；根顺序按seed随机。重复次数不是独立根数。
- 声明数值资格和clean确认的不同观察范围。干净计时不导出heavy全状态。
- 该新面板只检验新因子分解，不续跑/替换PR190；不为显著性加根或加session。

### 统计

主要效果保持四个直接比较：L_L4/W_L4、L_P/W_P、W_P/W_L4、L_P/L_L4，报告总完整service比和绝对差。
另一个主要量为根内平均log交互：
`I = mean_r[ log(T_LP/T_LL4) - log(T_WP/T_WL4) ]`，T为每根各session合计；exp(I)<1表示packing在local下更有利。

五项比较组成每模型一个多重比较族，预定root-cluster bootstrap保留所有臂和重复，10,000次，Bonferroni percentile区间；16根下仍属于近似区间，不是功效保证。报告逐根和逐session方向，以及等根log敏感性。不得把主要总service换成刚好更显著的估计量。

所有有效四臂都保留。一次完整测试中的数值失败使该版本不能获得完整面板性能结论；保留已运行槽位，开发修复另注册新确认，不单独重跑失败或慢槽。

### 需要保留的工作观测

图分组和实际算子宽度、量化/MMVQ activity、复制/拼接、graph构建/复用、planner/output-copy计时、完整service、温度/频率与失败。诊断trace单独运行，不能从活动计数估算时间。混合臂若实际上同路径，明确合并标签，不当作四个独立优化。

## R2：资源公平与真正常驻请求串（条件任务）

不重新验证“D4总是快”。只问当前Qwen应用收益在更实际的M和长期worker下是否存在。

固定四臂：W_M_TARGET_ONLY、L_M_TARGET_ONLY、L_M_MATCHED、L_D4。前两个只加载target模型和必要context；第三个保留原matched-residency控制；D4保留自身必要draft资源。所有允许的target算术与graph reuse公平提供。

先在4个已暴露根上核实移除闲置draft后是否仍保持原R。若数值/placement改变，不能硬凑同合同速度排名；另列资源部署身份和对应reference桥接，必要时停止这项比较。

复用R1已冻结的16个Qwen根研究新的生命周期，不能声称它们是另16个独立根。每arm/session只建一个worker：加载一次、2个固定已暴露primer、随后16个不同请求顺序执行且每个request按合同reset。四臂×四sessions，共256计时请求+32primer。顺序预定、无并发，没有prefix复用。

记录实际launch→首结果、模型/context setup、每请求完整service、首个计时请求和后续请求、整个16请求burst wall、峰值显存。密码哈希和资格采集在离线准备中；wrapper完整wall仍单独留存，不冒称互联网API延迟。实际first-result与burst时间直接取时钟，不能只用旧模型装载时间除N冒充实测。

两种M都报告，不能只取慢者；主要应用比较为L_D4对两个target-only M，matched M为敏感性控制。基线占用变化导致数值合同不一致时先说明，不改R混算。

## 退出与后续

R1若没有机制交互或local切分增量，就据实简化方法，不再补轮次。R2若实际M更快，保留该部署结论；仍可完成方法归因。原机正常工程修复自主进行，改变数值实现需重新资格。新FA、Q4、MMA、AUTO、paged/multisequence或新draft机制不属于此阶段。
