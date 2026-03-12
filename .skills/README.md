# Skills 目录

这个目录包含了可复用的自动化脚本（skills），用于简化常见任务。

## 可用的 Skills

### 📦 release - 版本发布

自动化执行版本发布的标准流程。

#### 使用方法

**Shell 版本（推荐）：**
```bash
./.skills/release.sh <version>
```

**Python 版本：**
```bash
python .skills/release.py <version>
```

**示例：**
```bash
./.skills/release.sh 0.8.2
```

#### 执行步骤

1. ✅ 验证版本号格式（SemVer）
2. ✅ 检查工作区是否干净
3. ✅ 更新 `pyproject.toml` 中的版本号
4. ✅ 运行完整测试套件
5. ✅ 创建 commit: "bump ver"
6. ✅ 创建 tag: `v{version}`
7. ✅ Push tag 到 origin

#### 前置要求

- Git 工作区必须干净（没有未提交的更改）
- 已安装 `uv` 工具
- 有 push 到远程仓库的权限

#### 错误处理

- 如果工作区不干净，脚本会中止并提示
- 如果测试失败，脚本会中止并回滚版本号更改
- 如果 tag 已存在，脚本会提示使用不同的版本号
- 如果 push 失败，脚本会提供排查建议

#### 示例输出

```
============================================================
📦 Release Version: v0.8.2
============================================================

🔍 Checking working directory...
✅ Working directory is clean

📝 Updating version to 0.8.2...
✅ Updated pyproject.toml to version 0.8.2

🧪 Running tests...
✅ All tests passed

📝 Creating commit...
✅ Created commit: abc1234

🏷️  Creating tag...
✅ Created tag: v0.8.2

🚀 Pushing tag v0.8.2 to origin...
✅ Tag v0.8.2 pushed to origin

============================================================
✅ Release completed successfully!
============================================================

📦 Version: v0.8.2
📝 Commit: abc1234
🏷️  Tag: v0.8.2
🚀 Pushed to: origin/v0.8.2

📋 Recent commits included in this release:
   abc1234 feat: add new feature
   def5678 fix: correct bug
   ghi9012 docs: update documentation

🎉 Done!
```

## 添加新的 Skill

要添加新的 skill，请遵循以下结构：

```
.skills/
├── README.md           # 这个文件
├── skill-name.md       # Skill 文档
├── skill-name.sh       # Shell 实现
└── skill-name.py       # Python 实现（可选）
```

### Skill 命名规范

- 使用小写字母和连字符
- 使用动词或动作名称（如 `release`, `deploy`, `test`）
- 避免使用空格和特殊字符

### 最佳实践

1. **提供清晰的文档**：在 `.md` 文件中说明用法和参数
2. **错误处理**：验证输入并提供有用的错误消息
3. **回滚机制**：如果操作失败，尝试回滚更改
4. **彩色输出**：使用颜色提高可读性
5. **详细日志**：显示正在执行的步骤

## 在 Claude Code 中使用

你可以要求 Claude Code 执行这些 skills：

```
请执行版本发布，版本号为 0.8.3
```

Claude Code 会自动识别并执行相应的 skill 脚本。
