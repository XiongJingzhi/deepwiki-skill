# 分析质量门控

> 本文档描述分析质量门控的完整规则：在extract-docs 完成后、synthesize-deps 开始前，用脚本自动检查 `module-analysis.json` 是否满足最低质量标准，消除"事后大规模返工"循环。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/check_analysis_quality.py <项目路径> [--verbose] [--json FILE]` |
| **输入** | `cache/module-analysis.json` |
| **输出** | 质量报告（stdout），退出码（0/1/2） |
| **前置** | `extract-docs` |
| **后置** | exit=0 → `synthesize-deps`；exit=1 → 增量补充后重跑本工具；exit=2 → 重跑 `extract-docs` |

## 目标与收益

### 当前问题

```
extract-docs（分析） → generate-module-docs（文档生成） → generate-module-docs 收尾质检（质检）
                                              │
                                   发现 50% 文档是 Basic
                                              │
                              ◀── 回到 extract-docs 重做（巨大浪费）
```

当 `finalize.py quality` 在generate-module-docs 收尾质检发现大量 Basic 文档时，整个后半段流水线需要重头执行。根本原因是分析质量标准是在生成后检查的，而不是在生成前强制约束的。

### 优化后流程

```
extract-docs（分析）→ module-analysis.json
                       │
                  check-analysis-quality（门控）← 新增：脚本检查，零 AI 成本
                       │
          ┌────通过────┤
          │           └───不通过→ 增量补充分析（只补缺失字段）
          ▼
      synthesize-deps→ 继续流水线
```

### 预期收益

- 消除generate-module-docs 收尾质检 → extract-docs的大规模返工循环
- 单模块补充分析的 token 成本远低于全量重做
- 质量达标确定性提升：前置门控 + 即时生成校验 = 双重保障，质量达标率从 ~60% 提升到 ~90%

---

## 执行方式

从技能目录运行门控脚本：

```bash
python scripts/check_analysis_quality.py <项目目录绝对路径>
python scripts/check_analysis_quality.py <项目目录绝对路径> --verbose
python scripts/check_analysis_quality.py <项目目录绝对路径> --json gate-report.json
```

---

## 质量门控标准

### 模块级必需字段（缺失 → 该模块标记为"需补充"）

| 字段 | 失败条件 | 原因 |
|------|---------|------|
| `module_path` | 缺失或为空 | synthesize-deps依赖关系综合需要此字段定位模块 |
| `module_summary` | 缺失或为空 | generate-overview/generate-module-docs 文档生成的核心输入 |
| `semantic_group` | 缺失或为空 | 菜单分组和跨模块一致性的基础 |
| `selected_components` | 缺失、为空或不是列表 | generate-module-docs 直接使用，缺失则退化为重新决策 |

### 模块级推荐字段（缺失 → 警告，不影响门控结果）

| 字段 | 缺失影响 |
|------|---------|
| `code_purpose` | generate-module-docs 组件选择可能不准确 |
| `analysis_depth` | 无法判断分析质量基线 |
| `dependency_hints` | synthesize-deps综合将依赖 AI 重新推断 |

### 文件级必需字段（缺失 → 其所属模块标记为"需补充"）

| 字段 | 失败条件 |
|------|---------|
| `path` | 缺失或为空 |
| `summary` | 缺失或为空 |

### 文件级推荐字段（整个模块均缺失 → 警告）

- `public_interfaces`：空列表意味着generate-module-docs 无接口表格，会降级为 Basic 文档
- `key_insights`：缺失意味着generate-module-docs 无设计意图说明，无法解释 WHY

> **例外**：`code_purpose` 为 `Config`、`Test`、`Util` 的模块不检查 `public_interfaces` 和 `key_insights`（这类模块接口稀少属正常情况）。

---

## 退出码

| 退出码 | 含义 | 处理方式 |
|--------|------|---------|
| 0 | 全部模块通过最低质量标准 | 继续synthesize-deps |
| 1 | 存在需补充的模块 | 对失败模块增量补充分析，再重跑门控 |
| 2 | `module-analysis.json` 不存在或格式错误 | 重新运行 extract-docs |

---

## 不通过时的增量补充流程

当门控返回退出码 1 时，**不需要全量重做extract-docs**，只需对失败模块补充缺失字段：

1. 读取门控报告，获取失败模块列表和缺失字段
2. 对每个失败模块，仅针对缺失字段重新分析：
   - 缺 `public_interfaces` → 重读该模块的核心文件，仅提取导出接口
   - 缺 `key_insights` → 重读主文件，补充 2-3 条设计意图说明
   - 缺 `semantic_group` → 根据模块名+文件角色，直接标注语义分组
3. 将补充结果**增量更新**到 `module-analysis.json`（不覆盖已通过模块的数据）
4. 重新运行门控脚本验证是否通过

### 关键原则

> **只补缺失字段，不重做已完成的分析。**

例如，若某模块缺少 `semantic_group` 但 `public_interfaces` 完整，则只需用 1-2 句话补充语义分组，而无需重新读取源码。

---

## 与generate-module-docs 收尾质检质检的关系

| 检查点 | 执行阶段 | 检查对象 | 目的 |
|--------|---------|---------|------|
| check-analysis-quality（分析质量门控） | extract-docs 之后 | `module-analysis.json` | 确保生成输入质量，前置拦截 |
| generate-module-docs 质量检查阶段 | generate-module-docs 之后 | `wiki/modules/*.md` 等 | 确保生成输出质量，收尾检查 |

两者互补：前置门控减少generate-module-docs 收尾质检发现问题的概率；generate-module-docs 收尾质检作为最终安全网。
