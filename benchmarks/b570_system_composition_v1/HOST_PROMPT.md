# 给B570 agent：系统组合实验执行任务

作者已同意开展独立B570方案。只在本PR分支、独立worktree/run中推进；不要改main、PR102/104/105/106、旧raw或其freeze，不合并、不发布、不改自动任务。RTX明天按原计划，与你无依赖。不要继续PR105剩余slots，不需要等其缺失logits；同一B570上不能并发运行两项实验。没有权限终止非本任务PID。

**目标：自然prefill状态形成 × MQ/PQ/QB/SERIAL消费方式的系统级价值，而非更细的KV/head搜索。** 阅读README、PROTOCOL、NATIVE_CONTRACT、ARCHITECTURE和SOURCES后开始S0；无需再为普通已界定步骤请求确认。

1. 先报告实际baseline sources/资产；恢复PR92真实R_stock与draft身份，查验PR101 target-only/k1 guard和global schedule限制。新研究必须有自己的自然k3 actor与target/draft独立schedule，不能仅删除guard。原reference不可重锚。
2. 完成隔离Vulkan PQ/QB图适配：保留backend arithmetic DLL；修改actor/graph层的源体和新编译身份全部入freeze。q<=4、capacity4、FAoff、单stream；prefill关闭QB。counts-off phase/reset/reuse路径一并验证。最多一个工作日/两轮有据接入修订；需要shader重写或特殊层补丁即停。
3. 运行本目录CPU测试；补真实serializer和k3接受/纠正/bonus/rollback/early-EOG/cap、进程/预算/错误路径测试。study.py不是native executor，host需补执行器和raw来源映射；不要声称改路径后已可用。
4. 从固定corpus+formatter+tokenizer与全项目exposure清单生成HOST_INPUTS；四旧task只用于bridge/pilot。24新task为MBPP/GSM8K×各自未见池token长度rank三分层×4（固定规则，非事后选分界）；排除ID及token序列重复。输入不足在任何新forward前停止，不拼接/加padding造样本；不带答案/tests进入prompt。
5. 使用`study.py plan`生成完整1576模型请求及48算子计划。必须验证PLAN→recipe→真正将发送对象，并复用同对象发送；禁止DONORS/restore/golden logits。将全部代码、资产、计划、request bytes和执行F0前瞻提交到本PR并认证回读。用户转交本PR后，可在上述界限内进入native阶段；本仓库设计commit本身不是执行F0。
6. S1：16原参考桥接请求＋48算子smoke。桥接或own-path/shape失败立即停；MQ/PQ/QB差异按协议分类。不得通过更换seed/精度或拆成多图假装QB来绕过。
7. S2：四task×十arm×两counts和一heavy，共120。合规但输出不等是科学结果，完成固定矩阵；错输入/route/内存/lifecycle/参考或observer控制错误立即停止。S2结束检查C128_QB完整资格、实际多行micrograph和预期图组织。未具备这些条件不做S3，不转去搜索层/head。
8. 通过S2后，用不再修改的代码与策略执行S3：24task×十arm×3sessions=720正式请求；每个fresh worker一个显式warmup后reset再测一次，共1440请求/720进程。各session至少与前次完成间隔15分钟。首次S3前再次回读同冻结并锁定输入/策略；不能因为pilot速度正负修改任务、k、精度、baseline或停止规则。
9. 以完整参考端点决定每个arm全panel速度是否合格，全部失败、回退、缺失保留。直接对比PQ/QB、SERIAL/QB、M/C、同consumer的P128/P512；不得从成功任务子集提炼“普适speedup”。正式wall包含自然prefill/draft/verify/sync/策略和phase切换；不将heavy/replay/enqueue算组件时间。
10. 从S2现有heavy导出中性架构trace：真实微图宽度、query轴/GQA/KV逻辑payload与来源、对应提交工作量。没有观测到的shader/归约序/DRAM/XMX占用均UNKNOWN。不要新增FPGA/RTL/新算术单元或为架构对话增加native采集。

总上限1576模型请求＋48算子启动，904 native进程，21600 owned秒，8GiB输出；没有额外probe/smoke/warmup/retry。先记账再启动，load失败也保留。不同阶段预算不可挪用做参数搜索。旧PR105已花成本另列，不重置。

完成或停止都直接在对话给出便于截图的结论表：完成数、失败/未启动、每arm资格、实际width、同参考成本、对系统/架构的价值和仍未知项。仓库只需一个持续更新且保留历史区段的RESULT.md、结构化结果、必要源码/测试/F0/raw清单及恢复回执，不堆重复报告。独立restore与CPU重算是验证；不要声称仅同机回读就等于外部审计。

成功不要求“提高接受率”，而要求在有限未见条件下更有用的参考保持执行。若只改善旧四题或全部负收益，停止扩大，交付边界结论；不钻进某一题某一层。
