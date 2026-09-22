# iOS TeamFlow 上游同步基线

## 当前基线

| 字段 | 值 |
| --- | --- |
| unity-work-flow 版本 | `1.0.2` |
| 上游项目 | `git@github.com:gzx543097079/iOS_TeamFlow.git` |
| 上游工作流版本 | `3.1.2` |
| 上游标签 | `teamflow-v3.1.2` |
| 上游提交 | `1217f4b7b2957bd57c649570408a9ff05045cff9` |
| 基线提交时间 | `2026-09-22T16:53:07+08:00` |
| 本次同步日期 | `2026-09-22` |

上述节点是 unity-work-flow 1.0.0 初始设计和工具逻辑的来源基线，1.0.2 仍沿用该基线。它表示“已审阅并适配到这个上游节点”，不表示两个项目文件逐行相同，也不承诺自动兼容后续 iOS TeamFlow 版本。

## 已适配的上游逻辑

- 单一需求卡、固定状态/AC 图标和验证证据绑定。
- “完成改动 → 环境预检 → 针对性测试 → 文件冻结 → 完整验证 → 目标交付”的执行顺序。
- 基于项目真实命令的 profile、输入指纹和暂存区一致性检查。
- commit、push、标签、GitHub Release 与 App 外部动作的显式授权边界。
- TestFlight Internal Only 只能显式启用的独立边界。

Unity 版本在此基础上增加并替换了 Unity Editor、Package、场景/Prefab、资源 GUID、EditMode/PlayMode、IL2CPP、Xcode 可重建导出、iOS 真机性能和原生 SDK 等规则。

## 下次同步方法

1. 获取上游新标签并确认目标提交，不直接跟随未发布工作区。
2. 比较 `1217f4b7b2957bd57c649570408a9ff05045cff9..目标提交`，优先审阅需求卡 schema、验证指纹、Git/发布边界和接入脚本。
3. 只移植仍适用于 Unity 的语义；iOS 原生 App 专属的 Swift/Objective-C/UI 架构规则不机械复制。
4. 更新本文件的版本、标签、提交、时间和适配说明，同时按 Unity 工作流完成需求卡、测试和完整验证。
5. unity-work-flow 是否升版本由实际兼容性变化决定，不直接镜像上游版本号。
