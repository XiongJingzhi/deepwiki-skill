# 变更检测详细规则

> 本文档对应工作流detect-changes：在代码结构提取之后、深度阅读之前执行，通过对比文件校验和确定哪些模块发生了变更，避免在未变更模块上浪费 Token。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/detect_changes.py <项目路径>` |
| **输入** | `cache/checksums.json`（上次保存值，可为空）、项目源文件 |
| **输出** | `cache/checksums.json`（更新）、变更模块列表（stdout） |
| **前置** | `extract-structure` |
| **后置** | `extract-docs` |

## 文件分类

运行 `python scripts/detect_changes.py <项目目录绝对路径>` 后，将文件按变更类型分类：

| 分类 | 判断依据 | 处理方式 |
|------|---------|---------|
| **新增文件** | 文件不在 `checksums.json` 中 | 排入完整文档生成队列 |
| **删除文件** | 文件在 `checksums.json` 中但已不存在 | 将现有文档标记为废弃 |
| **修改文件（api-change）** | 哈希变更 + 含 `export`/`pub`/`public` 的声明行发生变化 | 完整重分析队列 + 触发反向依赖传播 |
| **修改文件（impl-change）** | 哈希变更 + 公开接口行未变 + 非注释行有变化 | 定向重分析队列：仅更新 `key_insights` |
| **修改文件（doc-only-change）** | 哈希变更 + 仅注释/文档字符串行变化 | 轻量更新队列：仅更新文件 `summary` |

> **变更类型判断是尽力而为（best-effort）**：脚本通过对比前后版本的"重要行"（含 `export`/`def`/`fn`/`class`/`public` 的行）是否变化来区分 `api-change` 与 `impl-change`。无法判断时退化为 `api-change`（保守策略，确保不遗漏重要变更）。

脚本运行后会**自动保存**当前校验和到 `cache/checksums.json`。

## 模块关联

根据 `cache/structure.json` 中的模块与文件映射，将变更文件关联到具体模块，确定**需要深度阅读的模块列表**。

## 首次生成 vs 增量更新

- **首次生成**：`cache/checksums.json` 为空时，所有模块都排入完整文档生成队列，等效于全量生成。
- **增量更新**：仅对有文件变更的模块执行深度阅读和文档更新，显著节省大型项目的处理时间。

## 反向依赖传播

脚本自动分析模块间的导入关系，当模块 A 变更时，将依赖 A 的其他模块也排入更新队列。

输出 `affected_modules`（直接变更的模块）和 `reverse_affected_modules`（因依赖关系受影响的模块）字段。

## 输出字段扩展

脚本在变更列表中为每个修改文件附带 `change_type` 字段：

```json
{
  "affected_modules": ["auth", "api"],
  "reverse_affected_modules": ["core"],
  "changed_files": [
    {"path": "src/auth/service.py", "change_type": "api-change"},
    {"path": "src/auth/utils.py", "change_type": "impl-change"},
    {"path": "docs/auth.md", "change_type": "doc-only-change"}
  ]
}
```

`extract-docs` 根据 `change_type` 决定每个文件的最小重分析深度（见 `extract-docs.md` → 变更筛选章节）。
