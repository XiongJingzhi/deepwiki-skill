# build-evidence-index：构建源码证据索引子步骤

> `build-evidence-index` 是 `validate-analysis` 内部的第二个子步骤。它从已通过质量门控的 `module-analysis.json` 中抽取关键 claim，并把 claim 关联到可验证的源码文件证据，输出 `cache/evidence-index.json`。

## 位置

| 项 | 内容 |
|----|------|
| **前置** | `check-analysis-quality` 通过；对外等价于 `validate-analysis` |
| **后置** | `plan-doc-topology`、`generate-overview`、`generate-module-docs`、`finalize quality`、跨页面一致性检查 |
| **输入** | `cache/module-analysis.json` |
| **输出** | `cache/evidence-index.json` |

## 执行命令

```bash
python3 scripts/build_evidence_index.py <项目路径>
```

也可以通过统一入口运行：

```bash
python3 scripts/cli.py build-evidence-index <项目路径>
```

## 输出语义

`evidence-index.json` 的核心字段：

- `claims[]`：可被文档引用或验证的关键结论
- `claims[].page_id`：该 claim 对应的页面，例如 `module:auth`
- `claims[].claim_text`：结论文本
- `claims[].evidence[]`：源码证据列表，至少包含文件路径
- `claims[].confidence`：证据充分性提示，当前为 `high` 或 `low`

## 降级策略

- 如果 `module-analysis.json` 缺失，应停止执行并提示先完成模块分析。
- 如果某个模块没有文件证据，仍可生成 claim，但 `confidence` 应为 `low`。
- 如果 `evidence-index.json` 缺失，`finalize quality` 会继续运行，但会报告“跳过证据一致性校验”。
