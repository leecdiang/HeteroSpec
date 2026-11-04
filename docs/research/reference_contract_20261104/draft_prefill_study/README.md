# QB draft prefill：决策计划与CPU重算

先读[PLAN.md](PLAN.md)。本目录仅新增研究文档、标准库分析脚本及派生结果，不改变runtime或历史记录。**新的Qwen/Smol GPU实验尚未启动，本包没有模型请求、用户设备访问或实测加速。**

## 复现

从仓库根目录运行，选择尚不存在的输出文件：

```sh
python docs/research/reference_contract_20261104/draft_prefill_study/test_screen_prefill.py
python docs/research/reference_contract_20261104/draft_prefill_study/screen_prefill.py \
  docs/research/reference_contract_20261104/draft_reuse_research/source_projection.json \
  --output /tmp/new-draft-prefill-sensitivity.json
```

只需Python 3标准库，不安装包、不下载模型、不访问网络/GPU。脚本认证输入SHA256，运行六个会计自检，只创建指定的新输出；拒绝修改过的projection和覆盖已有输出。输入与本包输出相同条件下，新JSON应与`sensitivity.json`逐字节一致。九项unittest包含`python -O`下输入认证仍有效的检查。

输入是[224d928固定projection](https://github.com/leecdiang/HeteroSpec/blob/224d92865c1f55988539453e02e0e25f1ad9cb2d/docs/research/reference_contract_20261104/draft_reuse_research/source_projection.json)，SHA256：`22e622cf1f69abe953a810069ebaf48b8bdadd90747225ac923e260ab8c3e340`。无需在本目录重复复制历史证据。

如持有[固定历史release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-scope-transfer-v1-evidence-20261030)的两份ZIP，可用相邻draft_reuse_research/reproduce.py的`--archives`独立重建。此次云端已认证两ZIP、重建672条formal记录与288个scope pair，精确匹配既有projection和RESULTS.json。新screen只使用其中96个QB pair：每模型12个暴露输入重复四session，不能当96个独立工作负载。

## 输出口径

- `grid`：两侧同步删除假设target-prefill时间后的敏感性格。
- `thresholds`：相对同scope M，打平或超过3%收益所需draft-prefill删除比例；包含0与每请求10ms额外开销坐标。
- `ideal_overlap`：余下target/draft prefill完美重叠、无竞争和额外开销的上限。
- `session_thresholds`：四个历史session分别计算，属于观测范围而非置信区间。

fraction表示假设可删除的**elapsed-time比例**，不是token overlap、cache hit rate或真正缓存干预。所有其他成本固定；结果是host accounting反事实，非因果、非并发测量、非部署预测。

重要筛选：冷Smol打平需69.946%删除，超过M的3%需77.419%；如果双方各删除50% target prefill，Smol理想prefill overlap仍为C/M=1.051664；全删target prefill而draft仍冷时为1.569481。真实双缓存可能也删除draft prefill，但必须重新计fill、catch-up、restore、state、eviction与continuation成本。Qwen原本已胜过M，新增方案还需胜过现有有用draft及更强同合同竞争者。

详细源、测试与未完成范围见[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)、[VALIDATION.json](VALIDATION.json)。本计划不提供accept概率或新颖性保证，不合并PR、不更新论文。
