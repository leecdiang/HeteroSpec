# 新结果的标准记录接口

CPU工具是未来export的验证器，不是native worker或GPU启动器。执行端adapter需保留原始response/log并将其映射到以下JSON，不得改变原始输出。所有ID、EOG/长度/停止与cap用native定义，第一EOG包含它；若raw有后缀，记录不合格而不是裁掉。

每formal record:
```json
{
  "slot": "<frozen slot>",
  "family": "<family>",
  "condition": "<arm name>",
  "task": "<registered ID>",
  "session": 0,
  "round": 0,
  "phase": "formal",
  "warmup": false,
  "freeze_commit": "<actual F0B Git SHA>",
  "input_sha256": "<closeout.digest(family-specific task)>",
  "status": "COMPLETED",
  "wall_ms": 123.0,
  "runtime_identity_verified": true,
  "actual_condition": "<complete resolved condition object>",
  "output": {
    "ids": ["native integer IDs"],
    "eog_flags": ["native booleans"],
    "length": 1,
    "terminal_id": 1,
    "stop_reason": "EOG",
    "cached_tokens": 0,
    "truncated": false
  }
}
```

示例内尖括号和数组说明是schema占位，不是运行数据。实际output.ids/eog_flags必须为integer/boolean数组。STARTED/FAILED记录保留同一个slot、phase/input身份和错误，不能被后续重试覆盖。身份核验要对应完整source/binary/model/DLL bytes与实际CLI/runtime logs，不能只设置boolean。

B570额外记录worker_pid、adapter_pci、residency_receipt_sha256。receipt至少绑定raw_etl_sha256（多个ETL时为完整ETL清单的hash）、decoder_sha256、allocation_map_sha256、worker_pids、adapter_pci=8086:E20C、events_lost、coverage_complete、weight_kv_allocation_mapping_complete、dedicated_segments_only、paging_or_eviction_events、unattributed_allocations、minimum_signed_headroom_bytes及covered_phases。只有独立真实decoder从保留的ETL/allocations导出OBSERVED_SCOPE_CERTIFIED才可通过。CPU工具只检查结构、引用及worker范围，不证明物理事实；执行端另行重算hash、raw解码与证据范围。

新输入沿用#84 tasks/families结构，每全局task需要id/domain/description；每family-specific task含id、完整prompt_ids、cap128及原生模板/输入hash。history_audit必须含completed、by_id_and_description、unknown_hosts_disclosed、training_unseen_claim=false、excluded_ids、evidence_sha256。

freeze JSON含actual commit、actual_remote_blobs_verified、before_first_formal_forward、plan_sha256=closeout.digest(plan)、input_sha256=closeout.digest(inputs)。这些是实际预先remote核验收据，不是此设计PR已经完成的F0B。

每block另保存命令、loaded metadata/PID、全部warmup/failed、source版本和完整生命周期；搜索/trace探测/计数capture单独列账。分析文件附原始record哈希清单和独立复算收据。


## 工作量和模型接口

正式记录可附 workload 与 feature_units（无重型trace）；各feature单位及计数守恒见MECHANISM_PROTOCOL和mechanism.py。workload缺失标为缺项，primary输出/成本资格独立处理。所有字段源于新冻结native adapter和实际原始证据，不以boolean替代核验。

MODEL_CALIBRATION.json = {"rows": [...]}，精确包含每family固定6题×4arms的lite校准行。每行phase=exposed_profile、profile_mode=lite、slot/family/condition/task、wall_ms、feature_units、component_ms（键完全对应）、actual_no_added_sync=true、completed_wall_partition=true、on_off_raw_equal=true、source_identity_sha256、raw_evidence_sha256。feature_units包含target_prefill_ids、draft_prefill_ids、draft_continuation_rows、reconcile_output_ids、rollback_calls、request_channel及target_continuation_calls_w1..w(k+1)。component_ms是真实同一clock完成wall互斥分项；无对应work却有费用不可硬塞该分项，先检查phase定义。

calibrate返回模型只处于COEFFICIENTS_REQUIRE_F0B_SEAL；F0B额外绑定model_sha256=closeout.digest(model)、model_frozen_before_first_formal=true，以及实际模型文件字节SHA。receipt不代表此设计已完成native校准。独立raw verifier仍需复算原始计数、时钟与Git封存时间。

正式feature_units只用于冻结模型预测；确认wall不参与系数拟合。未覆盖feature输出UNSUPPORTED_SHAPE与null，不能填零。模型文件状态MODEL_TIMING_UNAVAILABLE时保留原因与空系数，仍可交付有资格的原生成本结果。

workload原生字段与守恒见mechanism.workload_metrics；正式记录还含source_identity_sha256，与该家族校准的完整source/runtime/model身份相同。验证caller每周期含一个seed行，实际draftUB1行数等于continuation调用数。初始/bonus/correction/fallback为互斥提交来源。feature_units不得从请求耗时或模型预测反推。组件wall闭合精度为max(0.05ms,0.001*wall_ms)。
