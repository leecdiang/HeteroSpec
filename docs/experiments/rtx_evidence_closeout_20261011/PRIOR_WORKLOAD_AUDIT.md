# #84 原生计数和请求长度再分析

来源是#84固定head 59b0f87a7011dad15f5e1146591ae83d9556d0e7 的完整 RESULTS.json 导出与 CONFIRMATION_INPUTS.json，实际Git blob/字节hash绑定见JSON。本次只做CPU复算，未独立恢复科学raw数组档案或重跑推理。576个C3_K3正式请求、每家族192、每题域96均保留。请求比沿用每题/会话四轮中位数、题等权log与两会话等权；接受比例为累计token加权，两者分母不同。

| 家族 | 题域 | 原生累计接受/草稿 | 输出ID中位数 | CAP停止比例 | M3/C3 请求比 |
|---|---|---:|---:|---:|---:|
| Qwen | MBPP | 70.69% | 25.5 | 0.00% | 1.022311× |
| Qwen | GSM8K | 78.06% | 128 | 100.00% | 1.196750× |
| SmolLM2 | MBPP | 72.82% | 31.5 | 0.00% | 0.602608× |
| SmolLM2 | GSM8K | 66.58% | 128 | 100.00% | 0.586590× |
| Llama | MBPP | 89.27% | 28 | 0.00% | 0.972621× |
| Llama | GSM8K | 81.09% | 128 | 91.67% | 1.148054× |

这些是原生发布 draft_n_accepted/draft_n 的计数代理，尚不是本新协议定义的每周期有效进展、全部draft工作或精确committed acceptance。它们已经说明只按接受率排名不足：Llama MBPP的89.27%高于Qwen MBPP的70.69%，但前者M/C0.972621仍慢，后者1.022311稍快。额外prefill、draft实际费用、验证width/微图、调度/回滚与短输出固定开销是待检验解释，当前不宣布唯一根因。

三个家族MBPP输出中位数约25.5/31.5/28，GSM8K中位数均128；Qwen/Smol的GSM8K全部CAP停止，Llama为11/12题。该窗口不是完整解题成本，不能将CAP命中算自然长答案完成。模板/native token化不同，长度只按家族解释；不把跨家族ID数看成同等语义工作。

现有正式导出没有完整verify/draft catch-up/rollback行数和可用phase wall/GPU timer。新模型参数未拟合；必须按MECHANISM_PROTOCOL用曝光工程校准、封存后在新题验证。历史Qwen约1.035与此1.106并非同面板/运行时A/B，不构成优化提升证据。

可复算命令：
```bash
python scripts/platform/rtx_evidence_closeout_v1/prior_workload.py --root . --out <scratch_prior_workload_audit.json>
```
