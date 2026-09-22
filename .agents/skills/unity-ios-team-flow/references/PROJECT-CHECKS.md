# 项目验证配置

`.agents/project-checks.json` 只保存已经在当前仓库验证过的无交互命令，不猜测 Unity 路径、测试程序集或构建方法。格式：

```json
{
  "schema_version": 1,
  "checks": {
    "editmode": {
      "argv": ["/Applications/Unity/Hub/Editor/版本/Unity.app/Contents/MacOS/Unity", "-batchmode", "-nographics", "-quit", "-projectPath", ".", "-runTests", "-testPlatform", "EditMode", "-testResults", "logs/editmode.xml", "-logFile", "logs/editmode.log"],
      "timeout_seconds": 1800
    }
  },
  "profiles": {"change": ["editmode"]},
  "inputs": ["Assets", "Packages", "ProjectSettings"]
}
```

`argv` 必须是数组，工具不经过 shell。`cwd` 可选且必须位于项目内。`inputs` 或 `profile_inputs` 定义证据指纹范围；Unity 项目至少覆盖 `Assets`、`Packages`、`ProjectSettings`、构建/测试脚本和本次需求卡。

实施中可直接运行最小测试。最终只在输入冻结后运行一次匹配 profile：

```sh
python3 scripts/teamflow.py verify run --profile change
```

报告会保存每条命令、退出码、耗时、日志路径以及运行前后输入指纹。失败后修复并重新运行；运行期间或运行后输入变化时旧结果不可绑定需求，也不可用于提交检查。

发布 profile 通常额外包含 iOS 导出、`xcodebuild` 编译/Archive 校验、包体或符号检查，但只有用户明确发布目标时才执行会产生外部状态的上传步骤。
