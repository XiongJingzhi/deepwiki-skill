# refine-modules

基于 import 连通分量分析，给出模块边界修正建议。

> `refine-modules` 不是外部 9 步主路径中的独立必经步骤。它作为 `analyze-project` 的可选 refine pass 使用，适合模块边界明显失真、目录结构不能反映语义边界的大型项目。

## 契约

| 项目 | 值 |
|------|-----|
| 脚本 | `python scripts/module_discovery.py refine <project_path>` |
| 输入 | `cache/structure.json` (modules)、`cache/code-structure.json` (import_relations) |
| 输出 | 标准输出（修正建议） |
| 前置 | `analyze-project` 已生成候选模块；如需 import 密度建议，可在 `extract-structure` 后执行 |
| 后续 | 可人工调整 `structure.json`，否则直接继续 `generate-skeleton` |

## 执行规则

1. 运行脚本，读取修正建议
2. 如果有合并建议（两个模块间 import 密度高），评估是否应合并：合并后文档更内聚，但模块粒度变粗
3. 如果有拆分建议（模块内存在不连通子分量），评估是否应拆分：拆分后文档更聚焦，但模块数量增加
4. 对于小型项目（< 10 个模块），通常可以忽略 refine 建议，保持目录结构作为模块边界
5. 修正决策通过修改 `cache/structure.json` 的 modules 数组实现
6. 非阻塞：即使有 refine 建议，也可以跳过此步骤继续后续流程
