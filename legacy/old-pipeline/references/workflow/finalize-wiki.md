# finalize-wiki

`generate-module-docs` 完成后执行。顺序**不可颠倒**。

输入：`wiki/`（已生成 Markdown）、`wiki/menu.json`、`cache/module-analysis.json`、`cache/doc-topology.json`
输出：校验后 `wiki/menu.json`

## 推荐入口

```bash
deepwiki finalize <项目路径>
# 未安装 console script 时：
python -m scripts.cli finalize <项目路径>
```

`deepwiki finalize` 是唯一推荐的收尾入口。它会串行执行 Mermaid 修复与校验，并保留每个子命令的退出码语义；任意步骤返回非零退出码时，整个 `finalize-wiki` 阶段失败。Agent 必须停止并报告失败，不得把文档宣称为“已完整完成”。

## 四步序列

以下命令仅用于说明 `deepwiki finalize` 的内部顺序，不建议手动拆开执行：

```bash
DEEPWIKI=<项目目录绝对路径>/.deepwiki
WIKI=$DEEPWIKI/wiki
PROJECT_NAME=<项目名称>

# 步骤 1：菜单校验
python -m scripts.wiki.generate_menu $WIKI $PROJECT_NAME --reconcile

# 步骤 2：Mermaid 语法修复（必须在 quality 前）
python -m scripts.wiki.postprocess mermaid $DEEPWIKI

# 步骤 3：Mermaid 语法校验（mmdc 不可用时会跳过校验）
python -m scripts.wiki.postprocess mermaid $DEEPWIKI --validate

# 步骤 4：文档质量检查
python -m scripts.wiki.postprocess quality $DEEPWIKI

# 步骤 5：跨模块一致性检查
python -m scripts.wiki.postprocess consistency $DEEPWIKI
```

## 失败处理

- `mermaid-fix` 返回非零时，说明修复过程本身失败或 dry-run 发现待修复内容；必须处理后重跑 `deepwiki finalize <项目路径>`。
- `mermaid-validate` 返回 1 时，读取 `.deepwiki/state/mermaid-errors.json`，对失败 block 所在页面定向重生成，或按错误报告应用 AI 修复，然后重跑 `deepwiki finalize <项目路径>`。
- `quality` 返回 1 或 2 时，按下方质量修复规则处理后重跑 `deepwiki finalize <项目路径>`。
- `consistency` 返回 1 时，必须修复跨模块一致性错误后重跑 `deepwiki finalize <项目路径>`。
- 不允许把任何非零退出码解释成“警告”“预期”或“可通过”。只要收尾步骤失败，本轮生成就未完成。

## 质量检查退出码

| 退出码 | 含义 | 处理 |
|--------|------|------|
| 0 | 全部达标 | 正常结束 |
| 1 | 存在 Basic 文档（≤50%） | 对 Basic 模块重新生成 |
| 2 | Basic 文档超过 50% | 对所有 Basic 模块从 `extract-docs` 重新执行子流程 |

## 质量修复

生成 subagent 提示词：

```bash
python scripts/subagent/build_prompt.py quality-fix --project <项目路径> --cache
# 或定向到单个 Basic 文档
python scripts/subagent/build_prompt.py quality-fix --project <项目路径> --page <wiki_path> --cache
```

模板文件：[`../subagents/quality-fix.md`](../subagents/quality-fix.md)。
输出位置：`.deepwiki/cache/prompts/quality-fix_<safe_id>.md`。

## Prompt 文件即唯一输入

派遣每个 quality-fix subagent 前，主 Agent 必须：

1. 执行上方 `build_prompt.py quality-fix ... --cache`
2. 确认 `.deepwiki/cache/prompts/manifest.json` 中存在该 `quality-fix` 记录
3. 必须读取生成的 prompt 文件完整内容：`.deepwiki/cache/prompts/quality-fix_<safe_id>.md`
4. 使用该完整内容作为 subagent prompt，不添加额外说明

禁止手写、摘要、改写或重新解释 subagent prompt。跳过此步骤视为本阶段失败。

调度规则：[`../rules/batch-scheduling.md`](../rules/batch-scheduling.md)。
