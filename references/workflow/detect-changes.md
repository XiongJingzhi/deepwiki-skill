# detect-changes

`python scripts/pipeline/detect_changes.py <项目路径>`

前置：`extract-structure` | 后置：`extract-docs`

输入：`state/checksums.json`（上次保存值，可为空）、项目源文件
输出：`state/checksums.json`（更新）、变更模块列表（stdout）

> 首次生成（checksums 为空）：所有模块排入完整生成队列。

## 文件变更分类

| change_type | 触发条件 | 处理 |
|-------------|---------|------|
| `new` | 文件在 checksums 中不存在 | 完整分析 |
| `deleted` | 文件在 checksums 中存在但磁盘不存在 | 标记废弃，删除 `module-analysis.json` 中对应 `files[]` 条目 |
| `api-change` | 哈希变更 + 含 `export`/`pub`/`public` 的声明行发生变化 | 完整重分析，触发反向依赖传播 |
| `impl-change` | 哈希变更 + 公开接口行未变 | 定向重分析：仅更新 `key_insights` |
| `doc-only-change` | 哈希变更 + 仅注释/文档字符串行变化 | 轻量更新：仅更新文件 `summary` |

无法判断时退化为 `api-change`（保守策略）。

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

