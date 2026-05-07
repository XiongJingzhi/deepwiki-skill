# prepare-inventory

命令：

```bash
deepwiki prepare-inventory <project_path>
```

输出：`.deepwiki/cache/project-inventory.json`。

收集文件路径、文件分类、语言提示、配置文件、已有文档、入口候选和基础统计。不要解析 AST，不要构建调用图，不要生成模块分析。
