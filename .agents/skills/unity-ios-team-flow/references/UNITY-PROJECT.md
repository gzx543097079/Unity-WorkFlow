# Unity 工程基线

## 事实源

- `ProjectSettings/ProjectVersion.txt`：Editor 版本；使用精确版本，若本机缺失则报告安装路径，不换版本打开。
- `Packages/manifest.json` 与 `Packages/packages-lock.json`：Package 声明与解析结果；两者作为同一变更审查。
- `ProjectSettings/`：平台、渲染、输入、质量和序列化配置；只修改当前需求所需键。
- `Assets/` 及 `.meta`：逻辑与 GUID 映射；移动/重命名必须保留对应 `.meta`。
- 既有 CI、构建脚本和 asmdef：优先于新建平行体系。

`Library/`、`Temp/`、`Obj/`、`Logs/`、`UserSettings/` 和本地构建产物不提交。仓库若已有更严格规则则沿用。

## 新项目启动

只确定当前阶段必需内容：目标 iPhone/iPad 范围与最低系统、横竖屏/安全区、2D/3D 与渲染管线、输入方案、首个场景、存档/联网边界、目标帧率和最低设备档位。先形成可运行垂直切片，再扩展功能。

不因“iOS 优先”把平台无关领域逻辑写进 `#if UNITY_IOS`。平台差异放在窄适配层，核心玩法通过接口依赖平台服务。

## 项目设置变更

修改前记录旧值与作用平台；修改后检查 YAML diff，避免 Unity 自动写回无关设置。切换 Unity 版本、渲染管线、输入系统、脚本后端、API Compatibility Level 或序列化模式属于独立迁移，除非用户明确要求，否则不夹带在功能开发中。

iOS 生产基线通常是 IL2CPP + ARM64，但以仓库和发布目标为准。不要把开发构建、Autoconnect Profiler、Script Debugging 或 Development Build 带入发布配置。
