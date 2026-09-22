# 工作流源码分发

本文件只处理 Unity iOS TeamFlow 自身的 ZIP 和 GitHub Release，不处理业务游戏的 Xcode、TestFlight 或 App Store 发布。

更新 `references/VERSION`、`.agents/teamflow.json`、README、分发清单和测试后，冻结文件并运行：

```sh
python3 scripts/teamflow.py verify run --profile change
python3 scripts/package_release.py
```

打包脚本输出以下可重复产物及 SHA256：

- `Unity-iOS-TeamFlow-v版本.zip`：工作流源码、测试和完整 Skill，用于开发本工作流。
- `unity-ios-team-flow-skill-v版本.zip`：目录根为 `unity-ios-team-flow/` 的独立 Skill；在业务 Unity 项目的 `.agents/skills/` 下解压。

两个包都使用显式文件清单和固定 ZIP 时间戳，不包含 `requirements/`、`logs/`、`releases/`、`dist/`、Git 数据、业务 Unity 工程或密钥。本地打包不等于发布。

只有用户明确要求 GitHub Release 时才补齐验证、commit、push、标签、附件上传和公开 Release。发布附件包含两个 ZIP 及各自 `.sha256`；GitHub Release 不授权 TestFlight 或 App Store 动作。
