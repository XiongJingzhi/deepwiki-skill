# finalize-wiki

`generate-module-docs` 完成后执行。顺序**不可颠倒**。

输入：`wiki/`（已生成 Markdown）、`wiki/menu.json`、`cache/module-analysis.json`、`cache/doc-topology.json`
输出：校验后 `wiki/menu.json`

## 四步序列

```bash
DEEPWIKI=<项目目录绝对路径>/.deepwiki
WIKI=$DEEPWIKI/wiki
PROJECT_NAME=<项目名称>

# 步骤 1：菜单校验
python scripts/wiki/generate_menu.py $WIKI $PROJECT_NAME --reconcile

# 步骤 2：Mermaid 语法修复（必须在 quality 前）
python scripts/postprocess.py mermaid $DEEPWIKI

# 步骤 3：文档质量检查
python scripts/postprocess.py quality $DEEPWIKI

# 步骤 4：跨模块一致性检查（非阻塞）
python scripts/postprocess.py consistency $DEEPWIKI
```

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
输出位置：`.deepwiki/cache/prompts/quality-fix.md`。
调度规则：[`../rules/batch-scheduling.md`](../rules/batch-scheduling.md)。
