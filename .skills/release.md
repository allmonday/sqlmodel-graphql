# Release Version Skill

发布新版本的标准化流程。

## 使用方法

```bash
# 发布新版本
/skill release <version>
```

例如：
```bash
/skill release 0.8.2
```

## 执行步骤

当用户请求发布新版本时，执行以下步骤：

### 1. 验证版本号
- 确认版本号格式正确（如 0.8.2, 1.0.0）
- 检查是否大于当前版本

### 2. 更新版本号
- 修改 `pyproject.toml` 中的 `version` 字段
- 使用 Edit tool 更新文件

### 3. 运行测试
```bash
uv run pytest
```
- 确保所有测试通过
- 如果测试失败，停止发布流程并报告错误

### 4. 创建 Git Commit
```bash
git add pyproject.toml
git commit -m "bump ver"
```

### 5. 创建并推送 Tag
```bash
git tag v<version>
git push origin v<version>
```

### 6. 确认发布
- 显示发布成功的消息
- 列出本次发布包含的主要变更（从最近的 commits）

## 注意事项

- 确保工作区干净（没有未提交的更改）
- 确保 pyproject.toml 文件存在
- 版本号应该遵循语义化版本规范（SemVer）
- 如果 push 失败，检查是否有权限或网络问题

## 示例输出

```
✅ 版本更新成功

📦 版本: v0.8.2
📝 Commit: abc1234
🏷️  Tag: v0.8.2
🚀 已推送到远程仓库

📋 本次发布包含:
- feat: add new feature
- fix: correct bug
- docs: update documentation
```
