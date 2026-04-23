# 第 7 步：生成导航菜单与文档地图

> 工作流第七步，由 AI 直接生成 `menu.json` 和 `doc-map.md`，定义文档导航结构（此时模块文档尚未生成，脚本无法扫描，需 AI 基于结构提前生成）。

## 7.1：AI 生成 menu.json

读取 `cache/structure.json` 中的模块列表（`modules` 字段），结合第 6 步概览文档中的架构分层，直接生成 `wiki/menu.json`。

> `menu.json` 结构模板和 AI 生成菜单的 5 条规则见 [`references/templates.md`](references/templates.md) → **menu.json 模板** 章节。

**为什么要先于详细文档生成菜单**：菜单定义了每个模块文档在导航层级中的位置（所属分组、前后顺序）。详细文档生成时可以引用自身在菜单中的位置来生成精确的面包屑导航和前后文档链接，使文档网络更加连贯。

## 7.2：AI 生成 doc-map.md

基于 `menu.json` 的导航结构和 `architecture.md` 的架构信息，生成 `wiki/doc-map.md`：

| 内容 | 数据来源 |
|------|---------|
| 文档关系图（Mermaid flowchart） | `menu.json` 层级结构 |
| 推荐阅读路径 | 按读者角色（新手/架构师/API 使用者） |
| 完整文档索引 | `structure.json` 模块列表 + `menu.json` |
| 模块间依赖矩阵 | 第 5 步 `core_dependencies` 输出 |

模板参考：`references/templates.md` → 文档地图。

完成后更新 `cache/progress.json` 的 `phases.menu.status` 为 `completed`。
