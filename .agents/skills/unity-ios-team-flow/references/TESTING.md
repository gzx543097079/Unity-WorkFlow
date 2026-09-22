# 测试策略

## 分层

| 层 | 适用内容 | 典型证据 |
| --- | --- | --- |
| EditMode | 纯 C#、数据转换、存档迁移、编辑器工具、导入规则 | Unity Test Framework XML + Editor 日志 |
| PlayMode | 生命周期、场景、Prefab、协程、输入/UI、运行时资源 | 测试 XML、日志、必要截图 |
| iOS 真机 | 触控、安全区、权限、IAP、Game Center、推送、原生 SDK、性能/热状态 | 设备型号/系统、构建号、操作步骤、日志/录屏/指标 |
| Xcode/发布 | 编译链接、签名、entitlements、Privacy Manifest、Archive | xcodebuild/Archive/导出日志 |

选择能证明 AC 的最小层级，但不降级平台风险。Editor 测试通过不能证明 IL2CPP/AOT、原生链接、权限弹窗或真机性能。

## 批处理要求

Unity 命令固定精确 Editor 路径，包含 `-batchmode -nographics -quit -projectPath`；测试使用 `-runTests -testPlatform EditMode|PlayMode -testResults <path> -logFile <path>`。命令退出码和 XML 测试结果都必须成功。若项目使用自定义 `-executeMethod`，方法必须明确失败退出、输出产物路径并避免读取交互 UI。

不要同时让多个 Unity Editor 进程打开同一项目目录。CI 使用干净工作区和可控缓存；许可证或 Package Registry 故障与代码失败分开报告。

## 人工矩阵

按变更风险选择：最低支持设备、当前主流设备、不同宽高比/安全区、弱网/离线、来电或控制中心中断、切后台/恢复、低存储、不同语言、升级安装和长时间运行。矩阵写进 AC 或证据，不用“真机正常”概括。
