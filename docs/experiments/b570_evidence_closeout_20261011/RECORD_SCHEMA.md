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

