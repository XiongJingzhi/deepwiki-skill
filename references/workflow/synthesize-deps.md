# synthesize-deps（内部规则）

由 `generate-overview`、`generate-menu`、`generate-module-docs` 内联执行，非独立步骤。

输入：`cache/code-structure.json`（`import_relations`）、`cache/module-analysis.json`（`dependency_hints`）、`cache/architecture-skeleton.json`（可选）
输出：`cache/relationship-summary.json`（持久化缓存，mtime 对比自动失效）

## 执行步骤

1. 读取 `code-structure.json.import_relations`（AST 文件级导入图，可信基线）
2. 读取 `module-analysis.json` 各模块的 `dependency_hints.imports` 和 `dependency_hints.imported_by`
3. 以 `import_relations` 为基准聚合模块级有向依赖边；`dependency_hints` 作为语义标注，与 AST 基线比对验证
4. 按验证规则处理冲突
5. 输出 `relationship-summary.json`

## 验证规则

| 情况 | 处理 |
|------|------|
| AST 有边，`dependency_hints` 也有 → 方向一致 | ✅ 高置信度，保留 |
| AST 有边，`dependency_hints` 无 | ✅ 保留 AST 边，标注 `source: ast_only` |
| AST 有边，`dependency_hints` 方向相反 | ⚠️ 保留 AST 边，记录冲突（AI 分析可能有误） |
| AST 无边，`dependency_hints` 有 | 🔍 检查：动态调用/抽象依赖 → 标注 `source: semantic_only`；明显错误 → 丢弃 |

## 骨架验证（可选）

若 `architecture-skeleton.json` 存在，用 `cross_domain_dependencies` 验证跨域边方向一致性；`architecture_layers` 校验分层方向（上层 → 下层）。不一致时记录到 `relationship-summary.json` 的 `conflicts` 字段，不阻断流程。

## 缓存控制

1. 若 `cache/relationship-summary.json` 存在，读取并使用，跳过重算
2. 若不存在，执行完整流程后写入缓存
3. 若 `module-analysis.json` 的 mtime 晚于 `relationship-summary.json`，视为缓存失效，重算并覆写

### 缓存失效

`relationship-summary.json` 通过 mtime 自动失效：若 `module-analysis.json` 的修改时间晚于 `relationship-summary.json`，视为缓存失效，重算并覆写。无需外部步骤主动删除此文件。
