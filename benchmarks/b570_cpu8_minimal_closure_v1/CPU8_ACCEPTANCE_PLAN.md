# C：条件验收与预算推导（未授权，0/8）

没有 A 的最终完整独立 SOURCE_REVIEW_PASS 和 B 的原生 ENTRY_ADMITTED，就不建立 C 执行冻结，也不启动第一个正式槽位。当前所有格子仍 UNSTARTED。以下为预算准备，不能当作已批准价格。

## 先纠正旧数字的含义

从已保存的 `CPU8_PLAN.json` 得到七项 90 秒、一项 transition 180 秒；各自外侧 30 秒 cleanup/调度期限。相加 `7*(90+30)+(180+30)=1050` 秒，只是源代码允许的串行槽位区间，尚未包含前后部署、审计、冻结、恢复和发布。

旧 `tool_binding.py` 将整个正式 guard 固定为 1125 秒、cleanup 5 秒、Job cap10，再加两个假设外层根：`(10+2)*(1125+5)=13560` 进程秒。它接近旧 13600 预留，解释了分配的来源，却不证明其有效。1120 秒 watchdog phase 与上述 1050 秒仅相差 70 秒，也不能因此声称各项审计、启动和收尾必定能容纳。

037 旧 review 的同一假设为 `(4+2)*(500+5)=3030`。039 原始快照出现六个活跃 Job 成员，因此 3030 不能作为新复审报价，简单把 4 换成 6 也没有给服务根、累计 starts 和 cleanup 建立硬界。

## 八项表：须由 B 和最终源码填实

`H_i` 是不在旧 case_seconds 内的启动、审计、监督/外层清理等墙钟上界；不能漏算或填 0。下表中 `T_i=旧 case_seconds+H_i`，`L_i=30` 是保留的旧槽位 allowance，不削弱实际代码中更早的硬截止。若最终调用结构需要额外外层 grace，应纳入 H 或拆子树，不能重复借用同一余额。

`P_i` 必须是已证明可强制的完整受控并发数；`U_i` 为覆盖其余服务的独立有限保守收费。每行 `E_i=ceil(P_i*(T_i+L_i)+U_i)`，而非下表旧时限直接乘以旧 cap。

| 顺序/用例/实际 detector | P_i | T_i（秒） | L_i | U_i | E_i | starts 上界 | storage/export 上界 |
|---|---|---:|---:|---|---|---|---|
| 1 normal_single / NORMAL_COMPLETE | UNKNOWN | 90+H1 | 30 | UNKNOWN | ceil(P1*(120+H1)+U1) | UNKNOWN | UNKNOWN |
| 2 normal_transition / TRANSITIONS_COMPLETE，8对16唯一槽 | UNKNOWN | 180+H2 | 30 | UNKNOWN | ceil(P2*(210+H2)+U2) | UNKNOWN | UNKNOWN |
| 3 terminal_pending_completion / SEALED_WRITE_REJECTED | UNKNOWN | 90+H3 | 30 | UNKNOWN | ceil(P3*(120+H3)+U3) | UNKNOWN | UNKNOWN |
| 4 frozen_input / SEALED_WRITE_REJECTED | UNKNOWN | 90+H4 | 30 | UNKNOWN | ceil(P4*(120+H4)+U4) | UNKNOWN | UNKNOWN |
| 5 late_closed_slot_write / SEALED_WRITE_REJECTED | UNKNOWN | 90+H5 | 30 | UNKNOWN | ceil(P5*(120+H5)+U5) | UNKNOWN | UNKNOWN |
| 6 resource_read_failure / RESOURCE_READ_REJECTED | UNKNOWN | 90+H6 | 30 | UNKNOWN | ceil(P6*(120+H6)+U6) | UNKNOWN | UNKNOWN |
| 7 directory_read_timeout / COVERAGE_GAP_REJECTED | UNKNOWN | 90+H7 | 30 | UNKNOWN | ceil(P7*(120+H7)+U7) | UNKNOWN | UNKNOWN |
| 8 journal_write_failure / JOURNAL_FAILURE_REJECTED | UNKNOWN | 90+H8 | 30 | UNKNOWN | ceil(P8*(120+H8)+U8) | UNKNOWN | UNKNOWN |

这不是八个已知的数值报价。旧每项 reserve40 starts、16MiB stream cap、历史归档压缩大小都不能替代新启动树和完整八项证据的上界。存储还必须计目录/分配粒度、链接、原始日志、sealed tree、两份归档、编码传输、恢复树、导出和发布尾部；保留 256MiB evidence/restore、64MiB export 及适用的 1GiB 总帽/10GiB free gate。每个 native 角色仍服从原资源与间隔限制。

整体前瞻报价：`C_proc = E_deploy + E_native_prereqs + E_freeze + sum(E_i) + E_seal + E_upload + E_download + E_restore_recompute + E_final_ack + justified_margin`。同样分别合计 wall、starts、storage 和 capture/export。常驻 guard/watchdog/supervisor 在槽位之间的间隔也要收费；可单列子树区间，或在每项包含所有祖先且额外覆盖非槽位区间，不能漏项，也不把并发 wall 相加当作实际串行墙钟。

交付不是免费 API 尾部：上传失败、未知提交结果、回读、终态导出、最终确认都有 prospectively bounded deadline 和空间。若提供方/服务 U 无有限依据，或整个序列+恢复+最后确认+cleanup 不能容纳，则 C 首槽之前停止。

## A/B/C 各自预算状态

| 账本 | 当前可证明报价 | 下一步 |
|---|---|---|
| 旧 647fc68d / 48d45054 | 仅各自历史事实，保持永久关闭与原 origin | 不重置、不转账、不追认 |
| 当前源码/方案工作 | 实际源码验证已做；全 host/服务生命周期、起点及成本覆盖 UNKNOWN；不声称受限 A campaign 合格 | 新的完整独立 review 先取得可强制 worker/time/cleanup 边界；没有启动该 review |
| A 的最终完整复审 | E_review 仍不可数值定价 | 不能重用 3030；不以重复短审代替完整一次 |
| B 的固定四行及收尾 | P/U/starts/外层时限未证明，报价未成立 | 先证明 B 本身保守硬 envelope，再另行授权 |
| C 的八项及交付 | 上表未填实，报价未成立 | 由实际 A/B 校准，独立新 UUID/origin/approval |

## 正式判定和交付

固定八项顺序逐个一次；任一非预期失败/超时/身份或清理缺失即停止，后续 UNSTARTED。故障 PASS 必须同时绑定原 fault id、指定目标、原始触发与预期 detector，而不是任意失败。内层原 100ms/1 秒、pending completion 与 transition 16 槽不变。任何源码变化使 F0 失效，不能修一个失败槽继续。

交付至少包括：A/B immutable manifests、源码/导入/DLL 独立 hash、机器/解释器/OS、F0 与全部 native prerequisites、八项 raw/控制点/资源与实际 OS 退出、真实 tool/session/terminal exports、完整 sealed manifest、原 ZIP 与真实 fresh remote download、包内未修改 reader 的隔离重算字节、外部 completion receipt 与最后发布确认。missing provider stable ID 明示 UNKNOWN；捕获一致性不是外部认证。

原根 stable prefix 也要先做实时原生/进程/存储/预算检查，再输出 reconstruction-only 稳定投影。新恢复根只能 RECONSTRUCTION_ONLY，禁止用 relocated 参数给原根豁免。保持 prefix 与恢复字节比较，不能把 live 的当前时点字段伪造成稳定字段。

8/8 但交付不全：`CPU8_CASES_PASS_DELIVERY_PENDING`。只有完整 live/native/freeze/case/delivery 都合格才可 `CPU8_INTEGRATION_PASS`。没有 ENGINEERING_READY、B570 数值/性能或科研硬件收益的自动升级。

## Non-circular C freeze protocol — DESIGN ONLY

The original C proposal contained a dependency cycle: F0 hashed the role map and all `tools/*.json`; the role map hashed an actual formal operation whose argv required F0's own SHA256. That is not implementable by iterative hashing or receipt exceptions.

Prospective exact sequence (each gate has independent process/storage/start/wall admission and is **not currently authorized**): (1) after authentic A SOURCE_REVIEW_PASS and B ENTRY_ADMITTED, materialize the approved `OPERATION_ROLE_MAP.json` with `C-formal-watchdog.kind=formal_cpu8, post_freeze_template=true, template_sha256=<HASH>` and one full, pre-priced `tools/<op>.operation.template.json` with sentinel `__F0_SHA256__`; no runtime operation or provider intent may pre-exist; (2) `budget_v6.snapshot(C)` reserves the **template** upper bound and `freeze_cpu8` seals source, A/B evidence, template and role map into F0 while explicitly rejecting any premature runtime operation; (3) a separate post-F0 action materializes one `tools/<op>.operation.json` with **only the sentinel replaced** by SHA256(F0), using the reviewed deterministic renderer; (4) actual guard request, argv, terminal and raw output bind to SHA256(runtime operation), while the runtime operation is accepted only if it equals the rendering of the F0-sealed template and F0 digest; (5) `snapshot(C)` charges the *runtime* instead of the template after materialization, never both. The post-F0 file is excluded from F0's immutable file set but not from current launch/receipt/delivery authenticity checks.

Negative controls: runtime operation appears before F0; map or template drifts; F0 includes runtime operation; runtime argv has wrong F0 or other changed token; renderer executed twice; pre-/post-F0 quote accidentally counted twice. None requires B570 native execution. An executed source-only test and independent P0-P2 review are still required; synthetic F0 fixture PASS never creates an actual F0.

## First informative B570 experiment after actual C approval — design only

**Question:** Is there an exact-reference-qualified, statistically resolvable and practically useful QB ↔ compact/permuted QH_C mapping crossover on B570 that differs from RTX after **real replay ON** and complete Q preparation/conversion/readback costs are charged? This tests cross-architecture generalization, not a pre-assumed FPGA accelerator gain. Freeze fresh B570 reference bytes and input-lifetime invariance before timing. Start with visible key lengths 1023/1024/1025, GQA/q=1/2/4 and QB/QH_C maps; no unqualified geometric padding at 1024. Use independently restarted balanced sessions and QB_A/QB_B A/A noise control, order reversal, clean graph-completion timing separated from profiling, true replay OFF/ON, resident vs input-inclusive budget, and report local reversals/p95 as well as paired mean/block intervals. Predefine a practical threshold exceeding measured A/A resolution and observed conversion/selector costs; if this never clears, report SOFTWARE_FIRST/HOLD and stop hardware extrapolation. If it clears, require independent kernel-path/physical bottleneck and system critical-path evidence before any focused FPGA probe. No GPU, model, actor or RTL execution is authorized by this plan.
