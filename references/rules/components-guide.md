# 文档组件指南

> **本文聚焦于组件选择策略**：如何根据 CodePurpose、Archetype 和模块特征决定生成哪些组件。
>
> 各组件的完整定义（触发条件、格式变体、生成规范、降级方案、源码追渃要求）见 [`module-page-components.md`](../generation/module-page-components.md)。

---

## 目录

1. [组件优先级总览](#组件优先级总览)
2. [CodePurpose 组件映射](#codepurpose-组件映射)
3. [组件选择双层策略](#组件选择双层策略)
4. [降级策略](#降级策略)
5. [组件选择流程](#组件选择流程)
6. [Archetype 覆写规则](#archetype-覆写规则)

---

## 组件优先级总览

> 组件优先级（P0/P1/P2/P3）权威定义见 [`module-page-components.md`](module-page-components.md) 的 `priority` 字段，本文仅提供使用指南。

---

## CodePurpose 组件映射

> CodePurpose 到默认组件集的完整映射表见 [`module-page-components.md`](module-page-components.md) 的 `archetype_defaults` 字段。

### 图例

- ✅ 必需：该 CodePurpose 下必须生成此组件
- 可选：根据实际内容判断是否生成
- AI 推荐：由第二层 AI 分析决定
- `-`：通常不需要

---

## 组件选择双层策略

### 第一层：规则触发（快速、确定性）

**执行时机**：读取 structure.json 后立即执行
**输入**：CodePurpose、复杂度、依赖数、文件结构
**输出**：必需组件列表 + 条件组件候选

规则触发由 [`module-page-components.md`](module-page-components.md) 的组件 `trigger` 字段和 `archetype_overrides` 统一维护。本文只说明选择流程，不重复定义条件逻辑。

### 第二层：AI 推荐（补充、语义性）

**执行时机**：深度阅读源码后
**输入**：源码内容、第一层结果、项目上下文
**输出**：推荐组件列表 + 生成参数

```
分析以下模块，推荐应生成的文档组件：

模块：{module_name}
用途：{code_purpose}
复杂度：{complexity}
核心职责：{responsibilities}

已选组件：{selected_components}

可选组件：[architecture-fit, design-rationale, internal-structure, execution-flow, data-flow, side-effects, invariants, design-patterns, performance-tradeoffs, tradeoff-analysis, usage-patterns, error-table, file-structure, decision-table]

请返回 JSON：
{
  "add_components": ["组件名", ...],
  "remove_components": ["组件名", ...],
  "reasoning": "原因说明"
}
```

**Layer 3：Archetype 覆写**

读取当前项目的 archetype，按 `module-page-components.md` 的 `archetype_overrides` 增删组件：

1. 若 archetype 有对应的 `add` 规则，且 `trigger` 条件满足（`always` 或 CodePurpose 匹配），则添加对应组件
2. 若 archetype 有对应的 `remove` 规则，且 `trigger` 条件满足，则移除对应组件（除非 Layer 1/2 已将其标记为 Required）
3. `remove` 不会覆盖 Required 组件（P0），仅影响 Recommended 和 Optional 组件
   注意：P0 组件的触发条件豁免（如 Test 模块的 overview、无导出模块的 api-table）不受此保护，archetype 覆写可基于 trigger 条件跳过这些 P0 组件。

示例：`agent-project` archetype 下，`state-diagram` 对所有模块添加；`sequence-diagram` 对非 API/Entry/Service 模块移除。

---

## 降级策略

> 组件降级方案（LLM 失败时的降级行为）权威定义见 [`module-page-components.md`](module-page-components.md) 各组件的 `fallback` 字段。

---

## 组件选择流程

> **重要**：在生成任何文档之前，必须先执行组件选择流程。
>
> **检测规则**：CodePurpose 检测信号和条件组件触发规则详见 [`codepurpose-detection.md`](codepurpose-detection.md)。
>
> **组件定义**：各组件的完整定义见 [`module-page-components.md`](module-page-components.md)。

1. **识别 CodePurpose**：根据文件路径和内容特征，参考 [`codepurpose-detection.md`](codepurpose-detection.md) 的检测信号表
2. **选择默认组件集**：根据 CodePurpose 选择必需组件，参考上方映射表
3. **添加条件组件**：根据模块特征（复杂度、依赖数、类定义等）添加条件组件
4. **AI 补充推荐**：对于复杂模块，可让 AI 分析后推荐额外组件
5. **排序输出**：模块文档优先按"自上而下理解 → 中层运行模型 → 深入源码 → 操作与导航"排序，而不是按源码文件顺序排序（推荐顺序详见 [`module-page-components.md`](../generation/module-page-components.md) 顶部排序原则）

---

## Archetype 覆写规则

> 8 种 Archetype 的完整覆写规则见 [`components-guide-archetypes.md`](components-guide-archetypes.md)。当项目 archetype 非 `generic` 时，需按需加载该文件获取对应的组件增删规则。
>
> **优先级**：archetype_overrides > CodePurpose 基础映射 > 条件触发。
> - `add` 规则：若 `trigger` 条件满足（`always` 或 CodePurpose 匹配），则添加对应组件。
> - `remove` 规则：若 `trigger` 条件满足，则移除对应组件（不会覆盖 P0 必需组件）。
>   注意：P0 组件的触发条件豁免（如 Test 模块的 overview、无导出模块的 api-table）不受保护，archetype 覆写可基于 trigger 条件跳过这些 P0 组件。
