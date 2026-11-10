# 32B 强简单基线与可选 B2：设计审查包

状态：**DESIGN_ONLY / NOT_ADMITTED**。本目录不启动 CUDA、模型、GPU 作业、租卡、后台轮询或实验调度。创建 PR 不授权运行。原始结果、标量 R、旧构建、账本与论文均不修改。

## 判断

1. **优先做 32B 强简单基线的有界诊断。** #216 的 whole target-only REF1-group 比图级 REF1-loop 总服务时间少约 5.62%，但当前 graph loop 含逐列图节点和 concat，缺少“同标量点积、循环移入后端”的强简单对照。这个缺口直接影响方法归因。后端 loop 尚未实现/资格验证，不能先宣称可行或省略它。
2. **新题根确认有条件执行。** 先完成三路径资格与真实操作数诊断，冻结解释与实现，再决定是否值得为明确的部署比较做一次 12 根、三实现、四轮确认。负号、无差别或无法实现都是可结题结果，不追求让旧结果变正。
3. **B2 默认暂缓。** 只有论文确实需要 A5000 上这组同状态/同输出宽度的暖态时序结论才激活。其结果不决定 32B 主线，也不能证明一般稳态、live 投机加速或架构因果。
4. **采纳附加审稿意见但控制范围。** B可独立采用合法批量量化，不强制与G有相同launch次数。可选共同graphs可行性在任何S2 clean输出前决定；最多再设计一张已授权A5000的干净重建小复测，默认DEFER，不形成新必过门槛。

## 文件

- `Q32_PROTOCOL.md`：三实现、资格、计时、采样、统计、预算、停止与交付。
- `B2_PROTOCOL.md`：保留原 64 warmup + 64 measured 设计，修正窗口与预算准入。
- `GRAPHS_POLICY.md`：有界共同capture/replay检查、事前单一政策及资格/预算门禁。
- `SECOND_DEVICE_OPTION.md`：可选第二A5000，6根×3臂×3轮、独立R与安静窗口，不池化独立N。
- `MINIMAL_REPRODUCTION.md`：真实统计/转换器/配置回显与单一复现入口验收、明确收口条件。
- `REVIEW_RESPONSE.md`：对附加审稿逐条处理与仍未完成的执行工作。
- `ADMISSION.template.json`：尚未填写的运行准入单，故意不可准入。
- `design_checks.py`：纯 CPU 的确定性顺序与算术检查；可导出符号槽位，不读取模型、不启动实验。
- `test_design_checks.py`：正例与失衡/超预算/空准入负例。
- `SOURCES.md`：固定证据版本、旧问题与防复发规则。

## 本 PR 的验证与边界

在本目录运行：

```sh
python3 -B design_checks.py --check
python3 -B -m unittest -v test_design_checks.py
python3 -O -B -m unittest -v test_design_checks.py
python3 -B design_checks.py --emit-plan /tmp/heterospec-design-slots.json
```

输出中的 root/operand 名称是**槽位**，不是已经选定的新题根或 GPU 作业清单。代码只验证设计结构与计数，不验证 GPU、数值资格、实际后端可实现性或执行权限。`--check-admission ADMISSION.template.json` 应失败；它只做最基本的文件完整性门禁，不代替执行器对真实来源、资格与资源的独立核查。

运行前必须在后续实现提交中填齐精确新根/操作数、源/二进制/模块闭包、独立 R、新窗口与资源授权、逐作业请求/行数、资格报告、统计脚本与远端全文回读。需要后端实现的工作尚未完成；本 PR 不假装是可直接启动的 GPU 执行器。

## 执行交接

按 `Q32_PROTOCOL.md` 的S0→S1→S2推进；若事前激活S1G，它与最终graph政策/完整资格在F1前完成。S3条件性执行；B2、第二卡独立可选且默认DEFER。每阶段先不可变注册与资源准入，再运行。任何冻结、数值、预算或清单门禁失败都停止受影响阶段，保留失败与成本，不通过改日期、换目录、隐藏重跑、改精度或减资格绕过。最小入口及三项结题条件满足后不自动追加实验。只提交新增结果PR，不合并、改论文或覆盖历史。
