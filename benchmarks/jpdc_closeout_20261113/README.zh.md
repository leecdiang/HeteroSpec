# JPDC 零 GPU 收口 — 2026-11-13

本次只读取保留证据、复算统计、核对源码与许可，并更新证据可得性。**没有修改论文、数值模块、参考、旧 STATE 或账本；模型请求、GPU context、placement、forward 均为 0。** 新目录从 main `701079f265c0ff8fd05d43fbc2d8d5054a711e1b` 独立建立。

已完成能够用现有材料完成的收口工作；“完成收口”不表示所有历史原始数据都重新验证，也不表示已经满足投稿的所有要求。逐项状态见 [STATUS.json](STATUS.json)。

已从公开不可变提交回读全部 52 个交付文件，核对清单字节和 SHA，并用下载的公开材料重跑三份统计脚本及 8 项测试，均通过：[PUBLIC_READBACK.json](evidence/PUBLIC_READBACK.json)。后续提交只补充这份回读记录、状态与运行环境说明。

## 直接结果

| 项目 | 本次完成 | 限制 |
|---|---|---|
| #203 8B 服务、#204 8B 因素归因 | 从冻结公开逐请求数据独立复算全部计时估计与区间，384 + 256 条 | 没有新核对这两项的私有逐请求 receipt 或重新资格 |
| #205 Llama、#206 14B、#208 14B 因素归因 | 现存私有 receipt → 原冻结分析器精确重放 → 独立统计实现交叉复算，288 + 384 + 256 条 | 此处重放的是计时记录，不是重新执行原生数值比较 |
| #218 S3 | 288 条 warm/measured 记录的固定分层 root bootstrap 复算 | 主比较 C/B：root 几何比 0.984864，95% CI [0.982148, 0.987721]；不能将相对弱 G 的收益替代它 |
| #236 自由多轮 | 8 个完整 episode 的服务成本和负结果复算 | LOCAL/strong 总耗时比 1.042196；仅两个预先固定案例，无总体加速证据 |
| 方法与代码 | 十项保证逐一对应源码、在线检查、离线资格与缺口 | 通过收窄主张解决；没有凭静态审查宣称新 native PASS |
| 数据可得性 | 清理实际执行与保留样本、归档、S3 副本映射分开记录 | 全量 S3 候选副本内容验证未执行；#221 CPU 原始 payload 尚未定位 |
| OASST | 固定 revision 的 Apache-2.0 来源核实，记录 #233 许可标签勘误 | 模型许可分别适用；不重写历史冻结材料 |
| 投稿要求 | 通用 Elsevier 政策及剩余事项列明 | JPDC 专属作者指南访问 403，格式要求仍待作者直接确认 |

独立复算共覆盖 1,568 条旧确认/迁移计时、S3 的 288 条记录和自由多轮 8 个 episode。不同实验不混池；重复轮次不冒充新的独立 roots。

## 从本目录复算

Python 3.10+，前三条仅用标准库：

```sh
python3 benchmarks/jpdc_closeout_20261113/recompute_panels.py
python3 benchmarks/jpdc_closeout_20261113/recompute_service.py
python3 -B -m unittest discover -s benchmarks/jpdc_closeout_20261113 -p 'test_*.py' -v
```

#203 原方案使用 NumPy PCG64 抽样；使用已有 NumPy 环境，不需要安装或升级项目依赖：

```sh
python3 benchmarks/jpdc_closeout_20261113/recompute_transfer.py
```

本次实际使用 NumPy 2.3.5 的已有 CPU 环境。`--out` 只接受新文件，避免覆盖旧证据。比较允许的 `2e-12` 只用于统计浮点求和的跨实现舍入差异，**不是**放宽 native 全向量/KV 的资格标准。

`collect_retained_panels.py` 仅供有私有保存目录的维护者重读 #205/#206/#208 receipt。它要求原分析器 SHA `8b1d0f7b794132bf5a33208d5c85124246bd112685f8bf33283156b70d7b0887`，对应 base main 的 `docs/merge_audits/20261111/legacy_shared/experiment.py`；不能换成当前 shared 版本。公开 `TIMING_ROWS.csv` 足以独立复算统计，但不是原始张量。

## 审阅入口

- [主张、强基线、负结果及直接来源](CLAIMS_AND_BASELINES.zh.md)
- [方法保证与真实代码边界](GUARANTEES.zh.md)，[完整冻结 guard 来源](evidence/GUARD_SOURCE_AUDIT.json)
- [删除后的证据与恢复边界](DATA_AVAILABILITY.zh.md)
- [OASST 许可勘误和直接来源](LICENSE_PROVENANCE.zh.md)
- [剩余投稿工作与停止决策](READINESS.zh.md)
- [源码/版本身份](evidence/VERSIONS.json)，[实际源码成员核对](evidence/SOURCE_MEMBER_CHECK.json)

没有必须补跑的 GPU 实验才能支撑本目录**收窄后的**论断。完整现代后端比较、自然多轮服务加速、普适 recipe/fallback 保证、完整 261 项资格不属于已经建立的结论；若将来要主张这些，需要另立研究及授权。
