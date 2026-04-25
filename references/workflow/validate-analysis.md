# validate-analysis：分析质量门禁与证据索引

> `validate-analysis` 是对外主路径中的分析验证阶段。它封装 `check-analysis-quality` 与 `build-evidence-index`，让用户只需要理解一个质量门控步骤，同时保留底层脚本供调试。

## 位置

| 项 | 内容 |
|----|------|
| **前置** | `extract-docs` |
| **后置** | `plan-doc-topology`、`generate-overview`、`generate-module-docs` |
| **输入** | `cache/module-analysis.json` |
| **输出** | 质量门禁结果、`cache/evidence-index.json` |

## 执行命令

```bash
python3 scripts/cli.py validate-analysis <项目路径>
```

如需只调试单个子步骤，可继续使用：

```bash
python3 scripts/check_analysis_quality.py <项目路径>
python3 scripts/build_evidence_index.py <项目路径>
```

## 行为

1. 读取 `cache/module-analysis.json`。
2. 执行分析质量门禁，检查模块必需字段、认知结构字段、文件摘要与接口洞察。
3. 如果质量门禁失败，返回非零退出码，不构建证据索引。
4. 如果质量门禁通过，构建 `cache/evidence-index.json`。

## 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 分析质量通过，证据索引已生成或无需生成 |
| `1` | 存在模块质量问题，需要补充分析 |
| `2` | 输入缺失、格式错误或项目目录无效 |

