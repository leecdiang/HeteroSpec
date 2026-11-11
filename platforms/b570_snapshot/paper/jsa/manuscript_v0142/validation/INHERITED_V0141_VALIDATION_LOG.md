# v0.14.1 实际验收记录

本轮仅已有导出CPU复算、编辑、编译、渲染和源包重建；无模型请求/forward/warmup、新硬件实验、merge、投稿或公开数据发布。

| 检查 | 记录 | 实际范围 |
|---|---|---|
| latest/祖先 | provenance/BASELINE_INHERITANCE.json | main f3fd2ae、#70 00ea8f7、#71 c1f11267；两PR开放，继承PR71 |
| 内容不变双栏 | output/BASELINE_LAYOUT_QA.json、validation/CONTENT_UNCHANGED_LAYOUT.patch | 30→14页；全14页本轮contact查看，记录float backlog/孤立末图 |
| 科学数值 | output/NUMERICAL_QA.json、SCIENTIFIC_QA.json | 384RTX、119B570、分母/suffix/phase/crosses/width/M4；不同计时/统计流保持 |
| 科学文本 | output/SCIENTIFIC_TEXT_REVIEW_QA.json | 20项检查，22源快照；关键数字/局限在摘要/主文/补充一致 |
| 本轮源认证 | SCIENTIFIC_AUDIT.md及上述JSON | 133源绑定、26导出、16历史；42份与v014字节一致，非完整private raw重审 |
| 干净编译 | output/FINAL_CLEAN_BUILD_QA.json、BUILD_QA.json | 从空build开始；12/27页，无undefined/duplicate/overfull/missing glyph；嵌字无Type3 |
| 页级视觉 | output/MAIN_VISUAL_QA.json、SUPPLEMENT_VISUAL_QA.json | 最终39页重新看；主文单页100dpi，补充另16重点页150dpi；30目录项/目标一致 |
| 词数 | output/WORD_COUNT_QA.json | TeXcount3.1.1，正文6394→5908，范围分项明确 |
| structured ZIP | output/SOURCE_PACKAGE_REBUILD_QA.json | 最终ZIP空目录解包/fullCPUbuild，源字节/18assets/numerical/twoPDF一致；非live Overleaf |
| flat ZIPs | output/FLAT_SOURCE_REBUILD_QA.json | main20源文件、supplement17源文件，同级、唯一basename、空目录重建12/27页 |
| flat main byte差异 | output/FLAT_MAIN_PDF_DIFFERENCE_QA.json | 5个PTEX.FileName变；485对象/415compressed、streams/text/12RGB页验证，其余一致 |
| baseline Git tree | output/INHERITANCE_QA.json | 本轮5683既有blob身份保持；不将树身份核对说成9.8GB全raw本地重读 |
| 工具链/哈希 | output/TOOLCHAIN_QA.json、SHA256SUMS.json | 版本、固定SOURCE_DATE_EPOCH、各PDF/ZIP SHA256 |

核心命令（从新稿目录，Poppler须在PATH）：

```bash
python3 build.py
python3 scripts/check_package.py
python3 scripts/flat_sources.py
python3 scripts/render_qa.py
texcount -inc -sum main.tex
```

本轮clean构建前明确删除新目录的build；源码ZIP检查在另一空目录开始。SOURCE_DATE_EPOCH=1791504000、FORCE_SOURCE_DATE=1、TZ=UTC固定构建元数据。PDF是否字节相同以实际对比为准。structured包完整重建、flat包仅编译必要source，工作树额外有42次v014 sibling比较，而独立作者ZIP只有内部绑定核对，审计记录如实区分。

原作者private归档审计、较早reference/requirements检查与视觉记录保留为INHERITED_V014_*，不归为本轮已执行。当前JSA Guide403，EM未访问；作者真实信息、AI/数据访问/最终人工核验等见AUTHOR_TODO。本次source/edit检查不等于外部peer review或商业查重。
