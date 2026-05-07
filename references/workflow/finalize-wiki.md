# finalize-wiki

命令：

```bash
deepwiki finalize <project_path>
```

检查计划页面是否存在、菜单和文档地图能否生成、Mermaid 能否修复并校验、输出质量是否达标、本地 Markdown 链接是否可解析。

## Mermaid 校验（必选）

`mmdc` 是必需依赖。运行前确保已安装：

```bash
npm install -g @mermaid-js/mermaid-cli
# 或确保 npx 可用（会自动通过 npx 调用 mmdc）
```

如果校验发现错误，脚本会生成 `.deepwiki/state/mermaid-errors.json`。此时 Agent 必须进入修复循环：

1. 读取 `mermaid-errors.json`，了解哪些文件的哪些 Mermaid 块出错
2. 修复对应的 Mermaid 代码块
3. 重新运行 `deepwiki mermaid <project_path> --validate`
4. 重复步骤 1-3 直到校验通过（`mermaid-errors.json` 被自动清除）

## 其他失败处理

停止流程，并报告失败页面、链接或检查项。
