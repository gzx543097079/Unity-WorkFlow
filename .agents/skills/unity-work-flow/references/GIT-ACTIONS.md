# Git 动作

只有用户明确要求目标动作时执行写操作。

commit 前只暂存当前需求范围，检查场景/Prefab YAML、`.meta`、Package 锁、ProjectSettings 和大二进制是否有无关变化，并运行：

```sh
python3 scripts/teamflow.py git check REQ-0001 \
  --result logs/project-checks/运行编号/result.json
```

提交消息包含 `Requirement: REQ-0001` trailer。若暂存内容与验证输入不一致，重新冻结并验证。commit 不授权 push；push 不授权标签或 GitHub Release；GitHub Release 不授权 TestFlight 或 App Store 动作。

Unity 合并冲突优先使用项目配置的 UnityYAMLMerge/Smart Merge，仍需语义检查引用与 Prefab override；不得用简单选边解决场景、Prefab 或 `.meta` 冲突。大文件遵循仓库现有 Git LFS 规则，不临时改写历史。
