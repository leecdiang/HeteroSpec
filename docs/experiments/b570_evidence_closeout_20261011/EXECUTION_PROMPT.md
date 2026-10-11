# B570 执行端交接提示词

在真实B570主机完成本设计并创建独立结果Draft PR。以本补全PR实际HEAD为准，先完整读取README、ASSESSMENT、PROTOCOL、DESIGN、ASSETS、SOURCE_BINDINGS、MINIMUM_EXCLUSIONS、EVIDENCE_AUDIT、RECORD_SCHEMA和CPU_VALIDATION。此设计尚未运行trace或native/GPU。

1. 实际Git/source/CAS恢复#88所有必要依赖与模型hash；本PR基于#88但不复用其已停止formal账本。固定Q6 target/Q4 draft/k1，不启动Q8或草稿候选搜索。
2. 先运行trace_preflight.ps1只读盘点。若WPT/权限不足，保留错误并按协议停止，不能手填proof=true、自动提权或取消512MiB门槛。
3. 在最多6 load-only单元/60分钟内，实现并冻结真实ETW/WPT采集与独立decoder。封存并实际remote读回F0P后才load；零forward源证明不得有hidden warmup。实际device LUID/PID、所有weights/KV allocation映射和event覆盖必须可获取，不能只有PDH或VK budget。
4. 仅P0工具/加载观测成功后封存/远端读回F0A，进入256单位总工程。验证五arms、完整raw IDs/EOG/cap、actual物理UB1 scope、capacity4和phase/reset/rollback；首选负收益也保留，不改选。
5. 关闭重型compute callbacks/KV readback的新正式通道需要capture-on/off完整输出对照，source/version全部留存。冻结统一轻量ETW、same-PID预算观测与全worker证据，独立解码原始ETL后生成receipt。任何proof不完整停止，不用CPU结构检查冒充证书。
6. 完整历史排除后从奇数description桶选12MBPP+12GSM8K题，与RTX补全偶数桶分离；题目描述、target模板/native IDs、所有source/model/DLL、observability、排程/统计冻结共同F0B并实际remote blob读回。
7. closeout.py schedule生成1200formal+50warmup五条件五轮排程；实现隔离本地single-writer无人值守controller。不依赖Codex/OpenAI API轮询，不重发formal，不因负速度取消已准入C的确认。
8. 全部实际worker的物理证据、native CHECK、allocation/paging/event-loss与费用保留。adapter字段映射只改字段名，不能删raw IDs/suffix；输出在计时内，persistence另账。当前code结构 gate不解码ETL，需独立实际decoder验证。
9. closeout.py analyse输出比较-specific资格/null与诊断费用；原始ETL/files与receipt hashes由独立验证者核对，不以手写receipt绕过。以8h lifecycle/7天预算停止。
10. 真实CPU科学档案复算与Git/local恢复，结果Draft PR接在本设计上。若仍RESIDENCY_PROOF_UNAVAILABLE，提交最终边界报告，formal为0，qualified ratio全null；不追加量化重启。禁止merge、paper/release编辑。

CPU命令：
```bash
python scripts/platform/b570_evidence_closeout_v1/closeout.py --design docs/experiments/b570_evidence_closeout_20261011/DESIGN.json validate
python scripts/platform/b570_evidence_closeout_v1/closeout.py --design docs/experiments/b570_evidence_closeout_20261011/DESIGN.json schedule --inputs <new_confirmation_inputs.json> --out <new_formal_plan.json>
```
这份方案可以以完整负成本或完整准入停止收尾。没有正结果承诺。

