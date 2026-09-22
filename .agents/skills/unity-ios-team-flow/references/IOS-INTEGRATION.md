# iOS 集成

## Unity 到 Xcode

- iOS 发布构建使用仓库确认的 IL2CPP、ARM64、最低系统和 Graphics API；变更这些值需独立说明兼容影响。
- Xcode 导出目录是可重建产物，不把手工修改当事实源。能力、Framework、Build Setting、Info.plist、entitlements、Privacy Manifest 和资源复制通过 Unity 设置、包配置或幂等 `IPostprocessBuildWithReport` 生成。
- 后处理脚本对重复运行安全，修改明确 target（通常 Unity-iPhone/UnityFramework），并在 Unity/Xcode 结构不符时失败，而非静默略过。
- Objective-C/Swift/C++ 桥接定义稳定 C ABI；字符串、内存所有权、线程和 callback 生命周期写清楚。UnitySendMessage 仅用于低频、弱类型回调。

## 平台能力

IAP 验证 StoreKit 沙盒商品、恢复购买、重复回调、收据/服务端确认、取消与 pending；Game Center 验证未登录、受限账号和重登；推送验证权限、token 更新、前后台和 deep link；ATT 只在实际跟踪且展示前置说明后请求。

广告、分析、归因和崩溃 SDK 需要核对数据收集、同意状态、SKAdNetwork、隐私清单/Required Reason API、儿童/地区模式和初始化时机。没有产品与法务依据时不擅自新增权限文案或数据用途。

## 生命周期

验证启动、暂停、失焦、切后台、恢复、音频中断、来电、控制中心、屏幕旋转（若支持）、低内存、网络切换和进程被系统终止。存档写入应原子化且不依赖 `OnApplicationQuit` 一定执行。

签名 Team、Bundle ID、capabilities、证书和 provisioning profile 以项目发布配置为准；不要把私钥、profile、API key 或账号凭据提交仓库。
