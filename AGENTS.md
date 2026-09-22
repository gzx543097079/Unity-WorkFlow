# unity-work-flow 团队工作流入口

本仓库使用中文协作，是工作流工具仓库，不是具体 Unity 游戏项目。开始先读 `.agents/skills/unity-work-flow/references/WORKFLOW.md`；再按本次任务加载专题，已读且未变化不重读。

<!-- unity-work-flow:start -->
## unity-work-flow

本项目采用仓库内的 `.agents/skills/unity-work-flow/SKILL.md`。开发变更维护一张需求卡和一份验证证据；问答、检查和只读分析不建卡。
项目空间是当前 Git 根及其目录树；处理空间外对象前先说明具体范围和操作，并取得用户本次明确允许。
不得猜测或擅自升级 Unity Editor、渲染管线、Package、Xcode 工程设置、签名或最低 iOS 版本；以仓库锁定值和明确目标为准。
有实现与交付的任务按“完成全部改动 → 环境预检 → 针对性测试 → 文件冻结 → 一次完整验证 → 目标交付”执行；完整验证后受跟踪输入变化时重新验证。
场景、Prefab、ScriptableObject、资源及其 `.meta` 是一体化输入；禁止通过删除 `.meta`、批量 reserialize 或无关 reimport 修复局部问题。
玩家可见文本来自项目本地化资源；性能结论必须标明设备、画质、场景、时长和可复现指标。
commit、push、标签、GitHub Release，以及 Xcode 导出、Archive、TestFlight、App Store 审核、发布和下架只在用户明确目标时执行；只补齐目标不可缺少的前置。
普通 TestFlight 上传不启用 TestFlight Internal Only；只有用户明确要求仅内部测试时才允许设置 `testFlightInternalTestingOnly: true`。
使用 `python3 scripts/teamflow.py` 处理需求、验证和显式动作。未经明确指令不提交、不上传、不提审、不发布。
<!-- unity-work-flow:end -->
