# refine-modules

基于入口链路、import 连通分量和共享依赖边界分析，给出模块边界修正建议。

> `refine-modules` 不是外部 9 步主路径中的独立必经步骤。它作为 `analyze-project` 的可选 refine pass 使用，适合模块边界明显失真、目录结构不能反映语义边界的大型项目。

## 契约

| 项目 | 值 |
|------|-----|
| 脚本 | `python -m scripts.analysis.module_discovery refine <project_path>` |
| 输入 | `cache/structure.json` (modules)、`cache/code-structure.json` (import_relations) |
| 输出 | 标准输出（修正建议） |
| 前置 | `analyze-project` 已生成候选模块；如需 import 密度建议，可在 `extract-structure` 后执行 |
| 后续 | 可人工调整 `structure.json`，否则直接继续 `generate-skeleton` |
| ⚠️ 顺序约束 | **必须在 `generate-skeleton` 之前完成**；骨架的 `module_groups.modules` 依赖稳定的模块列表，若骨架已生成后再修改 `structure.json`，骨架会引用过时模块名，需重新运行 `generate-skeleton` |

## 执行规则

1. 运行脚本，读取修正建议
2. 如果有合并建议（两个模块间 import 密度高，或被同一入口链路共同驱动），评估是否应合并：合并后文档更内聚，但模块粒度变粗
3. 如果有拆分建议，默认应拆分；拆分后文档更聚焦，但模块数量增加。拆分需满足以下任一语义条件：
   - 模块内存在不连通分量（各子集间无相互 import 引用）
   - 应用容器目录包含入口 + 多个内部能力子目录
   - 内部有 2+ 个职责明确独立的子能力域
   - **兜底**：模块源码文件总行数超过 1500 行，且可识别出独立子能力
   - 注意：已在第 3 层时不再拆子模块，改用页面内章节聚合各子能力
4. > 模块拆分核心原则（深度上限、共享依赖保留等）见 [`analyze-project.md`](analyze-project.md) 模块拆分原则章节。
6. 对于小型项目（< 10 个模块），也不要默认保持目录结构；若目录结构只是 `app/ + shared/` 这类容器形态，应按入口和依赖边界拆分
7. 修正决策通过修改 `cache/structure.json` 的 modules 数组实现
8. 非阻塞：即使有 refine 建议，也可以跳过此步骤继续后续流程

## 边界判断优先级

| 信号 | 权重 | 说明 |
|------|------|------|
| 入口文件和运行链路 | 高 | `main.py`、`index.ts`、CLI/HTTP/worker 启动点定义应用能力的阅读起点 |
| 文件级 import / 调用图 | 高 | 强依赖、双向依赖、同一调用链通常应聚合 |
| 共享依赖被多个模块引用 | 高 | `common/shared/pycommon/lib/sdk` 应保留为依赖模块 |
| 语义能力一致 | 中 | 同一业务能力或技术能力可跨目录合并 |
| 目录同父关系 | 低 | 仅作为候选信号，不直接决定模块边界 |
