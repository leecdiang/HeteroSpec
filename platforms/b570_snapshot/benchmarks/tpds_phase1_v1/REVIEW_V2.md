# 正式计时前修订 v2（2026-11-06）

本文件落实作者对 #192/#193 的审阅，不推翻 R1/B1 的研究方向。本次只修改设计、准备与分析工具；没有在作者环境运行 GPU，也不知道原机未上报的执行状态。先查原机 freeze/ledger/工作目录，不能从 GitHub 没有结果推断“尚未开始”。

## 1. 版本规则：不在面板中途改变合同

- 未冻结：完成本修订的原机适配与资格，再冻结 `review-v2` 的源码、依赖、输入、执行臂和估计量。
- 已冻结/开始：保留旧 commit、冻结件、已运行及未运行槽位的身份，不中途加臂、换 observer 或换计时字段；记录本次问题。后续修复使用独立的新版本和输出目录，不覆盖旧记录、不混合两版本。是否继续完成旧面板或按其原规则结案，应如实记录；不能将已知不合格数据当新版本结果。
- 只修改分析器时，可以对旧记录生成明确标注的只读重算；不重写原 receipt、不把新统计作为旧预注册估计。
- `baselines.adoption_action` 只帮助解释原机状态，不控制正在运行的进程。正常构建、ABI、路径、compiler dependency 格式和 observer 接口修复继续自主进行，不需反复等作者确认。

## 2. RTX R2：覆盖最强合法普通生成路径

原四臂只包含 W_L4 和 L_P 两种 target-only，可能漏掉 W_P/L_L4。新规则在 R2 测试输出之前逐项审查 R1 的四种组合：

| R1 组合 | R2 名称 | 驻留 |
|---|---|---|
| W_L4 | W_M_TARGET_ONLY | 只加载 target |
| W_P | W_P_M_TARGET_ONLY | 只加载 target |
| L_L4 | L_L4_M_TARGET_ONLY | 只加载 target |
| L_P | L_M_TARGET_ONLY | 只加载 target |
| L_P, M | L_M_MATCHED | 保留匹配的闲置 draft |
| L_P, D4 | L_D4 | 实际 draft 资源 |

默认包含全部合法且执行不同的四个 target-only 组合，再加 matched M 和 D4。保留两个原 target-only 控制；两个混合组合仅可因**已证明的执行等价**或**明确的数值/能力/容量不适用**省略。

等价需同时引用同参考、源码、实际 trace，以及前端/开销窗口证据；仅 group 数相等、速度相近、参数同名均不足。普通工程尚未完成不算不适用。不能因慢而删臂。开发阶段观测最强的合法组合必须直接包含或有等价代表，R2 测试性能不得决定比较对象。

用 `phase1.r2-baselines.v2` 审查件调用 `baseline_set`，并在新 R2 freeze 中绑定审查件哈希。每项包含 qualification/source/trace 证据入口；省略项包含原因和证明。该表不是自动数值资格，真实证据由原机提供。

排程保持 16 个根、4 轮、每 worker 两个 primer。4–6 臂对应 **256–384 次正式请求 +32–48 次 primer**；没有新增 session，3072 请求/4M 行总上限不变。超出原四臂时使用预定四行循环顺序，明确不是完整 Williams 平衡；保留 arm/session 次序和时段。所有不同执行臂必须在正式开始前固定。

主要比较为 L_D4 对**所有纳入的固定 target-only M**，按其数量做同族校正，同时报告每个对照、逐根/逐轮和实际 burst wall。不能事后选一个慢 M，也不能只对观察到的最小 M 做未经校正的推断。matched-residency 敏感性仍单列。

## 3. 完整构建输入冻结

`stage_native.snapshot` 现在核对隔离 source tree 的完整文件集合（仅排除 .git），不再只校验五个前端文件；两个前端所有传递文件也必须一致。原机先在独立目录建立完整 source snapshot，再运行 staging。不要把整个历史输出目录/模型文件复制进去。

正式性能冻结使用 `build_freeze.py`：

1. 从真实 compiler depfile、MSVC sourceDependencies 或 include trace 导出每个 translation unit 的传递依赖，保存原报告。
2. 显式绑定全部源、头、生成文件、build/CMake 配置、response files、编译与链接 argv、working directory、compiler/linker、静态库/对象以及构建相关环境值；不扫描或上传凭据。
3. 完成 native qualification 后保存实际加载模块清单及字节哈希，包括惰性加载到的模块。文件夹清单不代替加载清单。
4. 在所有正式 timing 之前冻结。重新核对文件/选项和原生实际模块；变更则单列新版本，不能沿用旧冻结身份。

配置为 `phase1.build-inputs.v2`：`files` 是 ID→{path,role}；`dependency_report` 指向真实编译器报告的标准化 JSON（source, original_reports, units[source,dependencies]）；`compile_commands`/`link_commands` 保留 argv；`generated_files`/`build_configuration_files` 显式列出；`runtime_report` 包含 observed_after_qualification 和 modules[path,sha256]；`qualification_binding` 指向实际资格。可适配报告格式，不能用手选少数 .cpp 文件伪造完整 closure。工具只核验记录一致性，不证明编译或数值正确性。

```sh
python3 build_freeze.py freeze build-inputs-v2.json build-freeze-v2.json
python3 build_freeze.py verify build-inputs-v2.json build-freeze-v2.json --observed-modules actual-loaded-modules.json
```

## 4. B570：真实配置与 append 窗口

C4096 必须实际构建并分配 context/KV/scheduler workspace，记录 `llama_n_ctx`、实际输出分配、原 producer/reserve、signed memory reserve 和 build-freeze 身份；Python capacity 字段或源码替换成功不是资格。

q2/q4 使用原登记请求行，q32 保留 last-only。原 R 的 UB128 producer 和输出 reserve 不改变，候选的必要输出缓冲由真实资格验证。不要为方便采集扩成 q32 全输出。

clean 模式不能仅隐藏显式 commit：原机要检查 observer.decode/begin/end/finish 的完整调用链，重型完整向量/KV、磁盘采集和独立参考回放不能留在 clean append 内。正常执行必须的同步和请求输出复制仍计入。通过实际 scope counter 或独立诊断确认，不从 `phase1_clean=true` 推断计数为零。

`normalize_receipt(..., window='append_after_valid_state', coordinate=...)` 只接收 `append_ms` 与对应 native begin/end，拒绝 service_seconds 回填。需要实际 capacity/mask/拷贝行数，`append_observer_calls` 的四项实际计数，以及 `native_admission_receipt`。主计时从已准备/恢复有效状态之后开始，包含 phase bind、执行、同步和请求输出取得；准备/prefill/恢复和完整请求另记，不能混用。

源码 overlay 已加入 begin/end、clean/window 元数据。四项 scope counter 和真实 allocation 绑定仍须原机适配，不能默认填0。overlay 和 helper 测试不代表 C4096 已运行。

## 5. 未测、零和部分成本

新 `saved_costs` 对顶层及嵌套 target/draft 每个 phase 分别统计 coverage。缺失值、空 phase map、未单独计时项均为 null；历史默认0缺少 MEASURED 标记时列为未核实零，不升级为实测0。明确未执行记 NOT_EXECUTED/NOT_APPLICABLE，仍与“测到0”区分。

完整总成本要求预定 root/session 矩阵或显式 expected_requests 完整。缺少请求/phase 时 `total_s=null`；只允许另列 `observed_sum_s`、present/measured/expected 数，不将部分和叫总成本。不从 inclusive 时间强拆未测 draft 子项，不将嵌套父子时间相加。

旧逐请求文件保持字节不变。扫描器默认 PR190 的6轮；其他记录显式设置 `--expected-sessions`，不从缺失后的记录推断应有数量。

## 原机完成标准

完成适用分支的原机接入、构建/依赖绑定、资格和计时；正常工程问题自行解决。R1 自然面板不必要时继续 R2；C4096 受限时继续 C1024 与干净构建。不要等待另一平台，不改原 R、历史结果、arXiv 或安全预算，不新增租卡/模型/算法支线。
