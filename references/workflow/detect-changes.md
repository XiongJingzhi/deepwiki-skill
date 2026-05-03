# detect-changes

`python scripts/pipeline/detect_changes.py <项目路径>`

前置：`extract-structure` | 后置：`extract-docs`

输入：`state/checksums.json`（上次保存值，可为空）、项目源文件
输出：`state/checksums.json`（更新）、`changed_files[]`、变更模块列表（stdout）

> 首次生成（checksums 为空）：所有模块排入完整生成队列。

## 文件变更分类

| change_type | 触发条件 | 处理 |
|-------------|---------|------|
| `new` | 文件在 checksums 中不存在 | 完整分析 |
| `deleted` | 文件在 checksums 中存在但磁盘不存在 | 标记废弃，删除 `module-analysis.json` 中对应 `files[]` 条目 |
| `api-change` | 代码文件哈希变更，当前内容含公开声明特征（`export` / `pub` / `public` / `def` / `class`） | 完整重分析，触发反向依赖传播 |
| `impl-change` | 代码文件哈希变更，但未检测到公开声明特征 | 定向重分析：仅更新 `key_insights` |
| `doc-only-change` | 文档文件哈希变更 | 轻量更新：仅更新文件 `summary` |

当前校验和缓存只保存 hash，不保存历史源码快照；因此修改分类是基于**当前文件内容**的保守启发式，而不是精确 diff。无法判断时退化为 `api-change`。

## 输出字段

```json
{
  "affected_modules": ["auth", "api"],
  "reverse_affected_modules": ["core"],
  "changed_files": [
    {"path": "src/auth/service.py", "change_type": "api-change"},
    {"path": "src/auth/utils.py", "change_type": "impl-change"},
    {"path": "docs/auth.md", "change_type": "doc-only-change"},
    {"path": "src/auth/new_handler.py", "change_type": "new"},
    {"path": "src/auth/deprecated.py", "change_type": "deleted"}
  ]
}
```

