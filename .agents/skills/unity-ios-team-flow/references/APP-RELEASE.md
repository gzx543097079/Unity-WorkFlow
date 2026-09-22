# iOS 外部动作

只有用户明确点名目标时执行；“检查/准备”是只读，不等于导出、Archive 或上传。

| 目标 | 最小必要前置 | 到达目标后停止 |
| --- | --- | --- |
| 导出 Xcode 工程 | Unity/iOS 预检、目标版本和构建号 | 不 Archive |
| Archive | 可重建 Xcode 导出、签名/能力检查 | 不上传 |
| 上传 TestFlight | Archive、导出与上传凭据 | 不分发、不送审 |
| 分发 TestFlight | 已处理构建、明确测试组 | 不提交 Beta Review，除非目标要求 |
| 提交 Beta Review | 构建、测试信息与合规资料 | 不提交 App Store 审核 |
| 提交 App Store 审核 | 版本构建、元数据、截图、隐私/加密/内容合规 | 不自动发布 |
| 发布/分阶段发布/下架 | 已审核版本与明确策略 | 不执行相邻动作 |

发布前至少核对：Marketing Version/Build 唯一且一致、非 Development Build、符号与 crash 解析可用、Bundle ID/Team/entitlements 正确、Privacy Manifest 和 Required Reason API 完整、IAP/远端配置环境正确、启动场景和包体可用、最低系统与设备范围符合产品决定。

普通“上传 TestFlight”必须省略 `testFlightInternalTestingOnly`，不能显式写 `false`。只有用户明确要求“TestFlight Internal Only/仅内部测试”时才设 `true`。

用 CLI 生成只读动作计划或记录已实际完成的证据：

```sh
python3 scripts/teamflow.py release prepare upload-testflight --version 1.2.0 --build 123
python3 scripts/teamflow.py release record archive --version 1.2.0 --build 123 \
  --evidence "Archive 路径与校验摘要"
```

记录不是执行器，不应伪造外部动作成功。
