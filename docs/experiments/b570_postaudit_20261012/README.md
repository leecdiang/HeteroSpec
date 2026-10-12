# B570 #92 完整输出交叉审计

本补充接在 #92 的 `82946adf946491e6cf7fef761bcc1ec0772e914e`，只读取已封存档案，不运行模型，不改变旧数据、资格、参考或费用。

目的：在全部24题、两会话、五轮上直接比较五个arm的完整原生IDs/EOG/长度/terminal/stop，确定 R_prod、M_match、C_k1 是否彼此保持完整输出。首差相同不能代替完整数组相同。

`scripts/audit/b570_pr92_pairwise.py` 使用 Python 标准库读取固定Git blob，验证两分片、完整CAS、manifest和全部7379个逻辑文件的内容哈希；不导入或执行档案内源码/二进制。数据处理只在CPU执行。GGUF外部依赖不下载，因本审计不运行模型。

运行入口：仓库的 `B570 PR92 sealed-output CPU audit` workflow；或在可读取本仓库的环境设置只读GitHub认证后运行：

```bash
python -m unittest discover -s scripts/audit -p 'test_b570_pr92_pairwise.py'
python scripts/audit/b570_pr92_pairwise.py --output audit-output
```

新结果属于事后完整交叉分析。即使某对arm全部相同，也不改写 #92 以 R_stock 为锚的预注册 `request_qualified_ratio=null`，不裁剪不合格题，不补跑正式槽，不宣称物理驻留或已验证成本模型。

当前发布阶段：CPU审计脚本及六项合成拒绝测试已完成；真实档案审计结果将在本PR的结果提交中记录，不能把测试通过当真实输出结论。
