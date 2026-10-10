# 全文语言复读记录

按作者指定的 [blader/humanizer](https://github.com/blader/humanizer) 执行全文优化，固定到 v3.1.0、提交 `225a6f39ac85f76ee48dbad772ea4abe4ed6c9d8` 的 [SKILL.md](https://github.com/blader/humanizer/blob/225a6f39ac85f76ee48dbad772ea4abe4ed6c9d8/SKILL.md)。完整阅读规则后，先逐段改写，再对照原稿复读正文、补充、七张图注、Highlights 和声明。未安装或运行该仓库的代码。

共审阅 19 个稿件文件，改写 17 个文件中的 63 个段落块。主要调整重复的结论引导、抽象过渡、机械的 First/Second/Third 结构和反复说明文章如何组织的句子；用具体观察、动作和比较量作主语。七张图注、Highlights 和声明经复读后保留，不为改写而改写。

第二遍阅读修正了两处：geometry 段落的重复介词，以及可能扩大 358H 结论范围的句子。最终使用明确的 conditional budget 表述，不把条件成本边界写成普遍的 parity 障碍。

以下内容保留：实际有信息的技术对比；局部与有限资格范围；普通／匹配／候选比较和计时边界；反例、缺失、停止记录、历史与正式结果的区别；未解决的跨会话不确定性。正文的数值、公式、引用、路径和代码名没有借语言润色改动，也没有添加新实验或结论。

`provenance/HUMANIZER_EDIT_RECEIPT.json` 保存每个改写块的原文与终稿、前后哈希、规则标记和复读处理。`scripts/humanizer_qa.py` 检查 19 个文件的改写可以唯一逆转并精确恢复编辑前哈希，且数字序列、数学表达式、引用／绑定命令、八个 inline table blocks、七个 figure blocks 和版式命令相同。独立的 baseline／numerical／figure QA 继续核对全部原表、科学输入与冻结证据。

文字是否更自然、限定是否等价还需要人工判断。本记录由同一审阅者完成，不代表自动语义证明、独立同行评议或 AI 检测结果。最终两份 PDF、结构化源包和 flat 源包的实际构建结果见 `VALIDATION_LOG.md` 与 `output/` receipts。
