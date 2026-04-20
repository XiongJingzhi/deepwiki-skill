---
name: changelog-generator
type: generator
version: 1.0.0
description: |
  自动从 Git 提交历史生成格式化的变更日志。
  Automatically generate formatted changelog from Git commit history.
author: deepwiki
requires:
  - deepwiki >= 2.0.0
hooks:
  - after_analyze
  - after_generate
---

# Changelog Generator / 变更日志生成器

自动分析 Git 提交历史，生成结构化的 CHANGELOG.md 文件。

## 功能特性 / Features

### 1. Conventional Commits 支持

自动识别并分类提交类型：

| 类型 | 显示名称 | 图标 |
|------|----------|------|
| `feat` | ✨ 新功能 | ✨ |
| `fix` | 🐛 Bug 修复 | 🐛 |
| `docs` | 📝 文档 | 📝 |
| `style` | 💄 样式 | 💄 |
| `refactor` | ♻️ 重构 | ♻️ |
| `perf` | ⚡ 性能 | ⚡ |
| `test` | ✅ 测试 | ✅ |
| `build` | 📦 构建 | 📦 |
| `ci` | 👷 CI | 👷 |
| `chore` | 🔧 杂项 | 🔧 |

### 2. 版本分组 / Version Grouping

基于 Git 标签自动分组：

```markdown
## [2.0.0] - 2024-01-15

### ✨ 新功能
- 添加插件系统支持

### 🐛 Bug 修复
- 修复缓存失效问题

## [1.5.0] - 2024-01-01
...
```

### 3. 作用域支持 / Scope Support

支持提交作用域分组：

```
feat(plugins): add plugin system
fix(cache): resolve cache invalidation
```

### 4. Breaking Changes 高亮

自动识别并高亮重大变更：

```markdown
### ⚠️ BREAKING CHANGES
- 移除了 `oldApi()` 方法，请使用 `newApi()`
```

### 5. PR/Issue 链接

自动链接到 GitHub/GitLab：

```markdown
- 添加用户认证 (#123)
- 修复登录问题 (fixes #456)
```

## Hooks

### after_analyze

分析项目后：

1. 读取 Git 日志
2. 解析 Conventional Commits
3. 按版本标签分组
4. 识别 Breaking Changes
5. 保存到 `cache/changelog-data.json`

### after_generate

生成后：

1. 格式化变更日志
2. 添加作者信息
3. 生成版本链接
4. 写入 wiki/changelog.md

## 配置 / Configuration

在 `.deepwiki/config.yaml` 中添加：

```yaml
plugins:
  changelog-generator:
    # 仓库类型
    repo_type: github  # github | gitlab | bitbucket
    
    # 仓库地址（用于生成链接）
    repo_url: https://github.com/username/repo
    
    # 显示格式
    format:
      # 是否显示作者
      show_authors: true
      # 是否显示日期
      show_dates: true
      # 是否显示提交哈希
      show_commits: true
      # 是否使用 emoji
      use_emoji: true
      # 是否按作用域分组
      group_by_scope: false
    
    # 包含的提交类型
    include_types:
      - feat
      - fix
      - docs
      - perf
      - refactor
    
    # 排除的提交类型
    exclude_types:
      - chore
      - style
      - test
    
    # 起始版本（不分析更早的版本）
    since_version: "1.0.0"
    
    # 未发布更改标题
    unreleased_title: "🚧 开发中"
```

## 输出示例 / Output Example

```markdown
# 变更日志

所有项目的重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## 🚧 开发中

### ✨ 新功能
- 添加 i18n-sync 插件 by @developer

---

## [2.0.0] - 2024-01-15

### ⚠️ BREAKING CHANGES
- 移除 `generateDocs()` API，请使用 `WikiGenerator.generate()`

### ✨ 新功能
- 添加插件系统 ([#42](https://github.com/user/repo/pull/42)) by @author
- 支持增量更新 ([#38](https://github.com/user/repo/pull/38))

### 🐛 Bug 修复
- 修复中文路径问题 ([#35](https://github.com/user/repo/issues/35))

### 📝 文档
- 更新 README 安装说明
- 添加插件开发指南

---

## [1.5.0] - 2024-01-01

### ✨ 新功能
- 支持 Mermaid 图表自动生成

[2.0.0]: https://github.com/user/repo/compare/v1.5.0...v2.0.0
[1.5.0]: https://github.com/user/repo/compare/v1.0.0...v1.5.0
```

## 命令 / Commands

```bash
# 生成完整变更日志
python scripts/changelog_generator.py generate

# 仅生成指定版本
python scripts/changelog_generator.py generate --version 2.0.0

# 生成未发布的更改
python scripts/changelog_generator.py generate --unreleased

# 验证提交格式
python scripts/changelog_generator.py lint
```

## 提交格式指南 / Commit Format Guide

为了获得最佳效果，请使用 Conventional Commits 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

示例：
```
feat(plugins): add changelog generator plugin

- Support conventional commits parsing
- Auto-group by version tags
- Generate markdown format

BREAKING CHANGE: removed legacy API
Closes #123
```
