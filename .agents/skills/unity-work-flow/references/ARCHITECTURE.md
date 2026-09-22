# Unity 架构与代码

- 领域/玩法逻辑尽量写成无 `MonoBehaviour` 的可测试 C#；`MonoBehaviour` 负责生命周期、场景引用和适配。
- 用 asmdef 明确边界，避免新的循环引用和全项目重编译；Editor 代码放入 Editor-only 程序集或目录。
- 避免在 `Update`/`LateUpdate`/`FixedUpdate` 热路径分配、反射、LINQ、字符串拼接和重复查找组件；需要时用 Profiler 证据指导优化。
- 显式拥有订阅、协程、异步任务、对象池和原生句柄的释放；场景切换、Domain Reload 配置和切后台不得留下重复监听。
- `Awake`/`OnEnable`/`Start` 的先后不作为隐含依赖；跨对象初始化使用明确 bootstrap 或依赖注入顺序。
- 时间相关逻辑区分 scaled/unscaled time；物理逻辑与渲染帧率解耦；随机数和时钟在需要复现时可注入。
- 保存数据、远端配置和 ScriptableObject schema 变更要有版本兼容或迁移策略。
- 平台服务（IAP、Game Center、推送、权限等）通过窄接口与可替身实现隔离；Editor fallback 不能伪装成真机通过。

Unity 对象通常只能在主线程访问。异步工作返回主线程前检查对象和场景生命周期；取消必须可传播。异常不能只写日志后继续产生坏状态。
