# 给 RTX 执行端的完整任务

请完成 `JSA_RTX_VALIDATION_V1`：为当前 JSA v0.14.5 稿件补充 RTX 独立会话复测、第二模型家族和外部方法同合同评估。你收到的本方案 PR URL 和完整 head SHA 是设计来源；先核验该 SHA，不依据标题猜版本。

请实际实施和运行，不停留在重新写一份计划。阳性结果不是交付条件。任务范围包括：恢复已有研究依赖、实现新 runner/必要模型图迁移和 LLM-42 adaptation、工程检查、冻结、GPU实验、独立CPU复核、归档、报告、新建 Draft result PR。无需因为到达冻结点再次向用户要一次确认；冻结后 commit/push/独立远端身份核验是程序门槛，随后在本范围内继续执行。资产权限确实缺失、实际身份无法核对或无法实现时，明确交付阻塞并继续其他独立 arm。

本 prompt 的 `prepare → freeze → execute` 是同一授权任务的阶段，**不是旧 RTX_A_B_V3 的 PREPARE_ONLY/EXECUTE_FROZEN 工作流**。旧研究文件的授权只适用于旧研究，不得启动旧 reserved study。本轮仅在 RTX 上新增运行；不运行 B570/M4/358H，不 merge、不创建科学tag/release、不投稿、不修改旧论文和历史证据。

## 首次行动

1. 记录原工作目录 HEAD、dirty state；保留原工作。fetch实际 main 与本方案PR ref，以本方案SHA为基线建立新的独立 worktree/checkout，建议分支 `codex/jsa-rtx-validation-v1`。即使设计PR尚未merge也能从其准确head开始。将 main SHA、方案SHA与本地实际HEAD分开记，不把检索时main锚点当作永久最新main。
2. 阅读本目录 README、RESEARCH、PROTOCOL、DESIGN、SOURCE_BINDINGS，以及 repo 的适用AGENTS、docs/data_policy、docs/experiment_protocol、paper/jsa/README。source bindings只是检索锚点；逐项核对，若不同记录后续diff而不是改历史hash。
3. 阅读并恢复现有RTX Phase1/Phase2/closeout CAS依赖。入口为 `benchmarks/rtx_consistency_contract_v1/`、`rtx_consistency_phase2/`、`rtx_closeout_bcd/` 和 `rtx_pr62_cpu_reference_closeout_v1/`。`RESTORE_WINDOWS.md`说明完整记录包的恢复与Windows深路径规则；公开目录不能单独重建私有CUDA前端。recovery必须在新目录，不覆盖旧run/archive。
4. 创建新实现 `scripts/platform/jsa_rtx_validation_v1/`，新证据 `benchmarks/jsa_rtx_validation_v1/`。旧脚本只能只读复用或有来源的复制。runner输入与离线verifier输入分开，在线端不能读取旧/新reference arrays、正确答案、未来proposal或divergence位置。
5. 在任何第二家族forward前完成MODEL_CHOICE；在任何新confirmation forward前锁定24输入和新exposure audit。执行端需真正解析模型GGUF、完整词表、special tokens/EOG，不能复制Qwen路径与常量。允许已有合法可用资产或公开允许访问的模型下载/转换，记录revision/conversion/quantization identities；不把权重或账户凭证写进Git。

## 工作顺序和自动推进

先恢复S并用四个旧probes验证固定前端/捕获合同，不调数值方案。冻结S的六日期/十二会话日程、命令、完整矩阵及统计；commit/push后独立核验远端，再按窗口执行。可以在S的会话窗口之间进行F/E工程，但不能改变S的库/程序/权重/host设置；S准入前按协议冷却和核验。

F使用预定模型选择顺序。新的24confirmation输入在discovery前锁定；工程和16-mask有限discovery仅用指定exposed输入。C3移植为主，有限mask集合的output-only规则可以增加一个Csel，但不会删除C3失败。自然state crosses仅在实际对齐与sham通过时解释。工程结束冻结候选/实现/确认完整矩阵并发布远端receipt，再自动执行F confirmation。

E按照LLM-42官方方法做独立的同栈 `LLM42_DVR_GGML_W32` adaptation。先写METHOD_MAPPING和实际state/padding/rollback资格。实现的是同target fast decode +固定形状verifier，不是将旧小draft serialized speculation重新命名，也不是把HeteroSpec mask3嵌入后再称纯外部方法。没有完整实现时标IMPLEMENTATION_BLOCKED，不以工程smoke替代正式结果。Qwen和第二家族的新输入confirmation测量可与F精确共享R/M/C记录，账本不重复计数。

主请求计时使用共同HTTP client边界，generation字段的边界须单独审计。E/R完整输出不匹配时仍保留计时/重复性/偏差，qualified speedup=null；不改参考、不删除难任务、不宣称原LLM-42方法错误。若只完成移植，应准确写外部method adaptation，而不是原SGLang系统复现。

每 arm 独立推进和结案。一项失败不抹掉其他两项；不得以另一项结果替代未完成证据。主机/操作异常slot保留、不自动补正式slot；预算、缺失和科学阴性分开报告。六日期固定预算不是小幅增益功效保证，跨1或方向不稳时按协议收窄收益结论。

## 结果交付与验收

最低交付内容以PROTOCOL §9为准，特别是完整raw committed arrays、实际timers、slot账本、freeze/remote receipts、全部失败、独立CPU verifier、内容寻址archive访问路径和重建入口。数据只保存在本机而没有作者可访问路径不算完整交付；digest不能替代原始arrays。

在result PR首页放完成度表：S跨日期收益、F家族资格/迁移、E同合同移植分别为complete-qualified、complete-negative/contract-mismatch、incomplete或blocked，附计数和限制。解释实际前后变化，不能将no-trigger家族写成同机制成功，不能将small gain不可确认写成稳定正收益。

创建并附加一个新的本研究Draft result PR，正文链接完整协议、qualification、报告、raw manifest、复现入口和独立核验。保留本方案PR为设计来源。不要在本方案PR里混入模型结果，避免读者分不清设计时间与结果时间。完成后报告result PR URL、精确freeze/执行SHA、三项结论、实际次数/时间和剩余缺口。
