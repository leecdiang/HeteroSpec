# PR119 入口修复交付

本交付为本地修复与独立代码复审，不是 B570 Windows 验收。历史
3cf5612 / 6214e73d 的 ENGINEERING_BLOCKED、停滞 NOT_REACHED、八项
UNSTARTED、十个缺失退出以及旧三小时证据全部不改。

## 实际审查

已认证本次历史 UUID 的 73 个远端 Git blob；原始 ZIP 367 成员中的
366 个清单文件均逐项验证大小与 SHA256。源码和原始日志确认：
停滞监督器在 win 导入时提前退出；首次复审实际使用默认 actor 资源
谓词，资源守卫触发时没有保存完整样本。因此不能断言进程数量是唯一
触发条件，也不能把后来加入的 aux 配置追认为当时已经生效。

## 修复

- 统一按入口文件的位置加载 runtime，显式核验模块来源；预检实际从异地
  工作目录以隔离 Python 子进程启动四个入口，加载其运行依赖后才报就绪。
- review_entry 强制选择独立有限 review profile；actor 限制不变。资源统计
  来自 OS Job，含嵌套调试器子进程；拒绝前保留原始数值和具体命中项。
- 失败清理继续待处理 debug event 并读取实际退出；未知保持未知。
- 提供 helper_tree 和原始 smoke 核验器，拒绝扩大配置、错拒绝原因及
  已采样却缺实际退出的身份，不把 smoke PASS 当成审查 clean。
- 冻结反例采用 in_process_freeze 类型，核验真实四项日志和修改字节，
  不索要不存在的 WATCHDOG 日志；次数仍计账。命令 smoke 的实际次数
  从 OBSERVER_START 重算。完整 D0 登记与 watchdog actor 历史子集分开说明。

## 验证及限制

31 项新针对性回归 + 原有30项能力回归通过；24个 Python 文件语法检查通过；
10子进程 helper fixture 在本机真实启动/退出通过。导入回归使用明确的
替身Win32后端，不能替代 Windows 原生入口、Job、停滞与清理验收。
历史四个冻结反例只读按真实schema重算通过，未升级历史结果。

四次独立复审记录完整保留。前三次发现的问题已修复，包括依赖预检遗漏、
Job资源覆盖、smoke误报路径、测试分隔符和冻结登记类型不兼容。
第四次对完整最终候选（含 B570_PROMPT）审查达到 P0–P2 scoped-clean。
精确文件/报告绑定见 REVIEW_BINDING.json。

完整 legacy CPU8 适配实现没有借本修复自动获得 clean；B570 必须先通过
真实预检/观察器检查/原生门槛，再对完整候选独立复审，才可生成F0并接八项。
本次未启动GPU、模型、科学执行或Windows实验；不扩展论文，PR保持Draft。
