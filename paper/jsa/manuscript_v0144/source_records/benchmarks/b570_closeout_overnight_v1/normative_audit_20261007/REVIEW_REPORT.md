# B570 实验规范性审核及缺项补齐（2026-10-07）

审核结论：**科学规范审核通过；原 NIGHT 有限核心完整，发现的机制诊断遗漏已补齐。宣布完整闭环还须本审核提交的 GitHub 全文件回读通过。**范围为 PR #63 prompt v1 的固定 B570/Vulkan、模型、任务、角色阶段、单序列和实际输出长度，不扩大为整个平台任意输入无损或唯一硬件根因已识别。

本次审核起点是已发布科学提交 `bd5e3963757857f7ce5cd6a7a87bb04d6eb48d8d` 与原 immutable 包 `238e1e499c8529fd65bfab00691a5f5d5cc31140e3595e5ae15e1765d1bc8697`。原 prompt v1 Git blob `d99dae9d78282c44de4900fdf18947a57f4ef7eb` 保持不变；原失败、参考、输入顺序、费用、deadline、暖机、恢复/拒收收据及 raw 全部保留。原报告中的“完成”在本次审核前尚未覆盖这个新增的规范性缺项，以下更正后才给出完整判断。

## 审核方法与原核心结果

新增 CPU 审核不导入执行器/原 verifier 的端点和比较函数。直接重读 token 全数组、运行时 EOG、raw 后缀、原指标文件、源 epoch、模型加载设备、重置、转移、post-sample sampler、请求冻结顺序和每一个成本分母。该审核通过 **64,921** 项检查，重新核算 **744** 行成本记录，并复核原包每个对象和恢复文件的字节。

原核心 **1,456/1,456 非热身请求**完成：G0 144、桥接20、B512、C504、原锚点长确认84、D reset96、D timing96。原 raw **1,961** 条，含1,774非热身和187热身；原独立验证363,698项通过。错误平台190条完整记录另行拒收；两条因截止/暂停而已完整输出的 D reset 仅 CPU 恢复，未再前向；科学失败零自动重试。

| 检查 | 结论 |
|---|---|
| 输入冻结、暴露审计、unused确定性选择 | 原输入/协议哈希不变；首次正式新输入在freeze之后；24共享明确已暴露，8 unused仅在可访问历史范围内 |
| 参考与分母 | 每轮R另付费且稳定；完整数组、长度、reason、runtime-EOG/cap比较；native overshoot保留并付费 |
| 实际B570及角色阶段 | 实际模型加载B570、目标37/37与草稿29/29 GPU offload；prefill/continuation分别绑定；实际KV/reset/pending证据有效 |
| 计时 | generation含首样本、在线状态传移、草稿、验证/rollback及最终同步；whole含解析、重置、创建/转移、生成和cleanup；证据文件写盘排除、host延迟另存 |
| capture与成本 | capture资格和capture-off费用分开；热身/冷加载/会话清理另账，不从instrumented时间扣算无观测费用 |
| 中断与deadline | 原时间窗保留，后续人工授权续跑/暂停/恢复留痕；所有原正式前向在续跑实验cutoff前；后续CPU交付单独记录 |
| 原档案与资产 | 原归档SHA/全对象CRC/SHA/恢复文件再次通过；153项原资产再次完整字节哈希通过 |
| 论文及历史研究 | 本PR diff限本研究目录；未修改论文、旧研究、shader算术、采样或参考，也未替换科学失败 |

原速度比重新核算为基线时间/候选时间：

| 共享队列比较 | generation | whole request |
|---|---:|---:|
| B：N0 / N1 | 0.999522x | 1.247059x |
| B：matched T / N1 | 0.804023x | 0.693541x |
| B：ordinary R / N1 | 0.188525x | 0.179055x |
| D：matched T / N1 | 0.827853x | 0.727751x |

N1相对N0整请求收益1.247059x，约19.8%时间减少，生成阶段基本不变；相对matched T和ordinary R均较慢。C有限旧长面板 k3/UB4、cap128存在已合格1.345798x生成/1.048339x整请求，不能泛化为全24任务部署收益。B_unused的MBPP/72中T及N1各四轮失败，N0/R通过；不更换任务/答案，也不宣称全新输入无损。C、原锚点长确认和原D在冻结队列通过。E五个UB2候选在旧/42、/145、/138失败，维持 **NO_GO_PILOT**；独立候选确认/候选resident没有资格而合法跳过，原型为可选NOT_IMPLEMENTED。

## 必须补齐的缺项：有限机制诊断

原 `mechanism.py` 仅从C筛选失败，因此 `MECHANISM.json` 的GATED_BY_QUALIFICATION只能解释“C无失败”，不足以解释本轮已有B/E失败时整个机制诊断省略。原文件保留作为历史收据，当前诊断结论以本目录 `SUPPLEMENT_VERIFICATION.json` 为准。

按当前用户“如果有欠缺，就继续补”的授权，在任何补充前向前另存UTC amendment、新有限时间窗、源码及私有build冻结。只扩大诊断来源至正式B/C/E，按原宽度/cap/任务顺序选首两个独立task/config pair：**HumanEval/42和/145，k1/UB2，cap128**。这是事后失败诊断，不冒称原研究的前瞻收益确认。没有按速度、margin或便利选择案例，也没有第三个方案、调参或换参考。

只增加只读 full float32 target logits 写出；native/target循环、采样、算术、模型、Vulkan ABI和既有参考保持不变。先在/134和/58做R/T/N0/N1共8条原参数桥接，全部保持历史契约。两个失败pair各自然生成R、matched T、失败native、原N1、ordinary同k/UB：10条父轨迹；ordinary的target prefill2与修复路径128差异明确记录。每个实际会话1条排除热身，共14热身；没有人工强制参考前缀、未来proposal tape、辅助decode或状态交叉。

新增 **18非热身+14热身=32条**，独立核验 **21,172** 项，通过全部 **4,108** 个自然决策的full-vocabulary float32行，重新算真正top1/top2和指定参考/替代/EOG分数。原锚点保留R，失败native复现原pilot两次的完整失败数组。诊断成本只作capture诊断，新增正式性能样本为0。

以下索引均从0开始，margin是当前自然父轨迹实测分数，不能解释为已控制过去状态的因果干预。

| 任务 | 父路径 | 保留R | 长度 | 首分歧 | 同原生边界前缀 | top1/top2 margin | reference−native替代 |
|---|---|---|---:|---:|---|---:|---:|
| HumanEval/42 | N1_repaired | PASS | 128 | — | True | 0.00880051 | 0.00880051 |
| HumanEval/42 | M_failed | FAIL | 128 | 73 | True | 0.34668732 | -0.34668732 |
| HumanEval/42 | T_matched | PASS | 128 | — | True | 0.00880051 | 0.00880051 |
| HumanEval/42 | M_ordinary | FAIL | 128 | 73 | True | 0.59547424 | -0.59547424 |
| HumanEval/42 | R_reference | PASS | 128 | — | True | 0.00258255 | 0.00258255 |
| HumanEval/145 | T_matched | PASS | 128 | — | True | 0.01523590 | 0.01523590 |
| HumanEval/145 | N1_repaired | PASS | 128 | — | True | 0.01523590 | 0.01523590 |
| HumanEval/145 | R_reference | PASS | 128 | — | True | 0.01161194 | 0.01161194 |
| HumanEval/145 | M_ordinary | PASS | 128 | — | True | 0.00059891 | 0.00059891 |
| HumanEval/145 | M_failed | FAIL | 128 | 56 | True | 0.11664200 | -0.11664200 |

两处首分歧都不是runtime-EOG：普通token的指定参考/替代比较与EOS margin分开保存。/42的ordinary同k1/UB2也失败；/145的ordinary同k1/UB2却保留完整R，而prefill128修复native失败。因此该修复的资格依赖角色/阶段及路径，更多约束没有单调改善证据。ordinary这个局部通过不构成完整pilot资格或新增效率方案；本次未做它的正式速度选择或部署推荐。

每条观察保存自然common-prefix哈希、decision-logit哈希、KV位置、logits row索引、可兼容的caller tokens/positions/seq/logits mask、实际图和role/phase，以及分别列出的runtime-EOG/指定参考margin。query关联来自保留trace中的兼容位置/KV maximum，不伪装为mid-state donor恢复。不同父轨迹的caller或自然过去状态不一致时，不能称为同状态反事实。

前端仍缺自然中途target+draft+post-sample sampler checkpoint；**state cross NOT_IMPLEMENTED，NOT_CAUSALLY_IDENTIFIED**。prompt明确允许记录真实trace/state/logit并保留这个限制；一般state serialization API存在不等于当前前端实现了自然交叉。prefill源不变、KV字节往返和pending/sampler行为得到验证，opaque sampler字节、唯一Vulkan kernel原因、可部署在线guard和普适最小范围仍未证明。两个不同task是两个自然诊断案例；不把重复cap计为独立案例。

## 同步次数与其它保留限制

补上 `1570` 条正式阶段记录的前端显式 `llama_synchronize` 调用数，含 `1442` 非热身及 `128` 热身：冻结源码的native reset2+terminal2，target reset1+prefill barrier1+terminal1，实际online move中的state调用3次，以及capture打开时每个已记录observer caller的强同步。逐请求绑定raw SHA和source epoch，结果见 `EXPLICIT_SYNC_COUNTS.json`。

这是**依据实际分支/记录和冻结源码推导的前端API调用数**，不是运行时内部所有同步的测量，也不是kernel dispatch。内部同步仍MISSING；已计时的真实终端同步并未因此遗漏。原 `WORK_ACCOUNTING` 的MISSING字段不事后伪造成测量值。无板卡功耗域故无能耗主张；共享/unused/旧长队列不混为独立样本；RTX不可访问bulk raw和不同后端/参考/ctx/threads仍披露；用户关闭屏保为用户陈述，不证明所有桌面GPU干扰消失，也不推断热漂移/壁纸因果。

## 封存、最终判断与复现

补充包 `058bcacc39b2d44047d4e5aa7c918ae79c87879bb51c758cc88250b394a8b3f1`，1,083,534,860 字节，4,459 文件、2,049 唯一对象；完整 CRC/SHA、私有程序、历史 bundle 与干净 CPU 重新派生均通过。最终 GitHub 回读另见交付收据。

原包保持 `238e1e499c8529fd65bfab00691a5f5d5cc31140e3595e5ae15e1765d1bc8697`。补充包独立封存raw全轨迹、full logits、KV、日志、失败/暖机/计时、冻结源码/bundle和私有exe；权重与runtime DLL作为已有哈希外部依赖，不入Git或补充包。Git只追加派生审核、源码和收据到同一Draft PR #63。`verify_supplement.py <restored-root>` 可CPU重算补充；原核心从原不可变包恢复后用原verifier复算；source-derived显式同步脚本读取原包raw与冻结源码，不再模型执行。

本轮保留原锚点的已验证适用范围，拒绝不合格的额外效率候选。核心问题、失败边界、匹配费用、长驻reset、有限自然诊断及可恢复交付全部完成且最终回读通过时，可宣布 **B570本平台本轮按PR #63 prompt的完整有限实验闭环**。没有剩余核心实验漏项；有明确负结果及prompt允许的机制/遥测限制。PR保留Draft，**不合并**。

## 最终交付已核验

审核科学/派生提交 `50b84aaf30067d02459bec51d854d9ec210bf9c3` 的全部209个研究文件，经全新Git存储从GitHub抓取、干净checkout与逐文件字节比对通过。**本平台本轮状态：COMPLETE_FINITE_SCOPE_AUDITED。可以宣布按PR #63 prompt的完整有限实验闭环。**原/补充包恢复通过，无剩余核心实验漏项，负结果及机制限制保留，Draft不合并。交付收据和manifest另提交后再次完整回读；最终提交身份见PR和本机final receipt。
