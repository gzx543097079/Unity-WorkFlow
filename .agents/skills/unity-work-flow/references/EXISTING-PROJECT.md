# 已有 Unity 工程接入

先做只读盘点，不触发 Unity 导入或重新序列化：

1. 读取 Unity 版本、Package 清单、asmdef、场景列表、Build Settings/Profiles、渲染管线和测试目录。
2. 查找既有构建入口、CI、Addressables、原生插件、Pods/SPM、IAP/广告/分析/崩溃 SDK 与本地化方案。
3. 识别项目级约定文件、代码生成和被忽略的机密配置。
4. 把真实无交互测试/构建命令写入 `.agents/project-checks.json`；无法确认的命令保持未配置，不猜测 `-executeMethod`。

大型项目按程序集、功能目录或资源组限定读取范围。跨模块入口（bootstrap、service registry、shared asmdef、全局 ScriptableObject、ProjectSettings）只有与当前任务相关时读取。

首次用 Unity 打开可能生成大量导入结果；执行前确认精确 Editor 版本与干净工作区。若打开后出现大面积无关 YAML 或 `.meta` 变化，停止并保留诊断信息，不把它们混进当前变更。
