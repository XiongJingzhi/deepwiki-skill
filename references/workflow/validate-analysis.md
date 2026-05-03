# validate-analysis

```bash
python3 scripts/cli.py validate-analysis <项目路径>
```

前置：`extract-docs` | 后置：`plan-doc-topology`、`generate-overview`、`generate-module-docs`

输入：`cache/module-analysis.json`
输出：质量门禁结果、`cache/evidence-index.json`

执行：检查模块必需字段、认知结构字段、文件摘要与接口洞察 → 通过后构建证据索引。

## 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 通过，证据索引已生成 |
| `1` | 存在模块质量问题，需要补充分析 |
| `2` | 输入缺失或格式错误 |

## 调试子步骤

```bash
python3 scripts/quality/check_analysis_quality.py <项目路径>
python3 scripts/quality/build_evidence_index.py <项目路径>
```

## 缓存失效

`scripts/cli.py validate-analysis` 会在进入门控时主动删除旧的 `cache/relationship-summary.json`。这样即使 `module-analysis.json` 只做了局部增量更新，下游 `synthesize-deps` 也会重新综合依赖摘要。

## 重试流程

exit=1 时，主 Agent 应：

1. 查看 check-analysis-quality 报告中的 `failed_modules` 列表
2. 对每个失败模块重新运行 `extract-docs`（仅该模块）
3. 再次运行 `validate-analysis`

建议最多重试 2 次。超过后仍失败则跳过该模块并记录警告。
