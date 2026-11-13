# 本轮保留的工程失败与修复

1. full-backend-001配置失败：Windows CUDA host compiler参数的反斜杠路径被解析丢失。保留所有日志和输入；v2全部路径转为正斜杠，完整161步编译/链接通过。没有改上游数学或冻结基线。
2. counter-cpu-001在触发超额异常时退出0xc0000409；没有CUDA/数值DLL链接或加载。相同源只将CPU诊断的/EHsc改为/EHs后退出0，定位为/EHc对extern-C不抛异常的假设。该诊断不是生产放宽：生产仍用/EHsc，新build002采用noexcept bool回调、U wrapper返回cudaError_t、普通C++层处理失败。三个独立编译单元下，exact500/refuse501、exact392/refuse393、过期/溢出/零值/未知操作拒绝及拒绝不dispatch全部通过。build001、原CPU失败和全部源版本保留。
3. Windows管理员启动返回取消：没有建立管理员控制器，没有CPU受限phase或GPUphase执行，也没有新GPU额度预留。聊天中的500次授权已存在，缺的是Windows现场确认；不降低ETW/隔离要求或修改安全配置来通过。该项后续状态以实际控制器/phase回执为准，不能把用户说“已确认”自动等同于控制器已存在。

[Microsoft /EH exception model](https://learn.microsoft.com/en-us/cpp/build/reference/eh-exception-handling-model?view=msvc-170)说明/EHc的extern-C假设；本轮CPU A/B编译复现也提供了直接证据。该工程问题关系失败回执的可靠返回，不是U量化错误或性能证据。所有GPU执行仍须独立完整资格与预算准入，原e10 FAIL不变。
