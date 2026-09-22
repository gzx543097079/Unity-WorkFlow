# 资源、场景与序列化

- 资源文件与同名 `.meta` 同步移动、重命名和提交；GUID 变化等同于引用迁移，需要检查所有消费者。
- 编辑 YAML 场景、Prefab、Material、Animator、Timeline 和 ScriptableObject 前确认 Force Text/既有序列化方式，并优先使用 Unity API 或小范围可审查修改。
- 不在有未保存编辑器状态时并行修改同一场景或 Prefab；Prefab Override 必须区分有意配置与误写。
- 导入设置按资源类型和目标设备制定：纹理尺寸/格式、音频加载方式、Mesh Read/Write、MipMap、Sprite Atlas。不要为单个资源全局改变默认值。
- Resources、StreamingAssets、AssetBundle/Addressables 各有加载和包体语义；新增内容先确认归属、生命周期和更新策略。
- Addressables 变更验证 group、label、依赖重复、远端 URL、catalog 兼容和内容更新流程；不要只以 Editor 的 Asset Database 模式为依据。
- 删除资源前用 GUID 搜索引用，并检查代码字符串、Addressables、Build Settings、Timeline、动画事件和原生侧引用。

资源或场景改动的 AC 至少包含可观察画面/行为、目标设备和引用完整性；视觉验收无法自动化时保存截图/录屏位置并标待用户验证。
