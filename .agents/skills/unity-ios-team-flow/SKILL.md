---
name: unity-ios-team-flow
description: 中文 Unity 游戏需求、实现、验证与显式交付工作流，重点覆盖 iOS 构建、真机性能、原生能力、TestFlight 和 App Store；用于 Unity 项目开发变更，不用于纯问答或非 Unity 工程。
---

# Unity iOS 工作流入口

`PROJECT_ROOT` 是当前 Git 根及其目录树。只使用本项目内 Skill；处理空间外文件或其他项目之前，说明对象、原因和操作并取得用户本次明确允许。需要安装 Unity、Xcode、SDK，或需要登录、证书、密码和系统确认时，先完成只读诊断，再把具体人工动作交给用户。

先读 [完整工作流](references/WORKFLOW.md)。同会话已读且文件未变化时不重读。随后只加载当前任务相关专题：

| 当前工作 | 必读资料 |
| --- | --- |
| 新项目或已有项目接入 | [Unity 工程](references/UNITY-PROJECT.md)、[已有工程](references/EXISTING-PROJECT.md) |
| 功能、架构或业务代码 | [架构与代码](references/ARCHITECTURE.md) |
| Bug 修复 | [Bug 修复](references/BUGFIX.md) |
| 场景、Prefab、资源、Addressables | [资源与序列化](references/ASSETS.md) |
| 构建、测试或验收 | [测试策略](references/TESTING.md)、[验证配置](references/PROJECT-CHECKS.md) |
| 帧率、内存、包体、启动、发热或耗电 | [性能与稳定性](references/PERFORMANCE.md) |
| iOS 平台设置、原生插件、IAP、Game Center、ATT、推送或隐私 | [iOS 集成](references/IOS-INTEGRATION.md) |
| 玩家可见文本或多语言 | [本地化](references/LOCALIZATION.md) |
| 用户明确要求 commit、push、标签或 GitHub Release | [Git 动作](references/GIT-ACTIONS.md) |
| 用户明确要求导出 Xcode、Archive、TestFlight、审核、发布或下架 | [App 发布](references/APP-RELEASE.md) |
| 对照或同步 iOS TeamFlow 上游逻辑 | [上游同步基线](references/UPSTREAM.md) |
| 发布 Unity TeamFlow 源码或 ZIP | [工作流源码分发](references/RELEASE.md) |

问答、检查和只读分析不建需求卡。开发变更使用 `python3 scripts/teamflow.py req create --title "标题"` 建立唯一需求卡，同一需求续接原卡。状态、范围、AC 与验证证据只在该卡维护。

有实现或交付的任务按固定顺序执行：完成全部改动 → 环境预检 → 针对性测试 → 文件冻结 → 一次完整验证 → 目标交付。完整验证后，只要受 profile 跟踪的脚本、资源、`.meta`、场景、Prefab、Package、ProjectSettings、原生插件、测试、文档或版本发生变化，旧证据失效。

以仓库中的 `ProjectSettings/ProjectVersion.txt`、`Packages/manifest.json`、`Packages/packages-lock.json` 和既有流水线为事实源。不得为了方便擅自更换 Unity Editor、渲染管线、包管理方式、输入系统、序列化模式、iOS 最低版本或签名方案。已有项目约定优先，不顺手迁移无关内容。

任何外部或共享状态写入都必须由用户明确指出目标动作。目标若依赖未完成前置，可自动执行最小必要前置；授权不向后扩张：commit 不自动 push，Xcode 导出不自动 Archive，TestFlight 上传不自动分发，审核不自动发布。

普通 TestFlight 上传完全省略 `testFlightInternalTestingOnly`。只有用户明确要求“仅内部测试”或点名该选项时，才允许设置为 `true`。
