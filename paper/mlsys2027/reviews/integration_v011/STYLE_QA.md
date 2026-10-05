# v0.11.0 语言、图表与排版核验

2026-10-05。最终主文12页（10正文+2参考），附录27页。所有主文页面及最终附录页面均经过渲染/文本检查；末次调整把 T.2 的运行方法放在完整任务表之后，消除了原近空白中间页，附录由28页变为27页。末页为参考文献，正常保留。

已完成：重写标题/摘要与贡献定位，精简方法/综合结论，增加 ordinary target-only bridge 与收费离线 selector，统一 restore/reproduce/no-op/unknown 语义，移除重复主文表，保留端点和 timing 区别。新图用固定四组任务模式呈现三条件/参考关系，采用已有配色、嵌入字体、矢量 PDF；没有使用生成图像模拟数据。

两次独立解包 clean build 均通过；逐页提取文本完全相同，正文页数相同。**不是 PDF 字节级可重复构建声明**，TeX 元数据时间可变。两次均零 overfull box、零未定义引用/命令。underfull 主文23、附录41，已结合页面检查，未发现截断、重叠或越界。PDF 字体嵌入/subset，未检出 Type3。

匿名核验：PDF author 为 Anonymous Authors；提取文本未发现仓库账号、github.com、/workspace 或作者名字匹配项。作者审阅和 venue 报告只放匿名材料之外。历史版权与官方模板依赖保留；当前格式是工作稿格式，不能代替正式投稿时核验模板。

文档核验结果：[BUILD_QA_V011.json](BUILD_QA_V011.json)。数据核验结果：[EVIDENCE_VERIFICATION.json](EVIDENCE_VERIFICATION.json)。精确最终字节：[ARTIFACT_MANIFEST.json](ARTIFACT_MANIFEST.json)。

匿名证据 wrapper 通过历史计算、完整数组/端点 exports、19任务图分组，以及原收费 replay 和10项既有 CPU 测试。没有新的硬件执行、timing、能耗或 code pass@1 结果。科学合同和历史数字保持原身份；新图表只从现有 exports 计算，不填补缺失项。

发布前另核对15个带有原注释的未改科学依赖：原Git blob身份一致，匿名ZIP仅移除TeX注释。打包器执行同一匿名变换；仓库中的历史数字文件保持原字节，不为匿名打包改写。
