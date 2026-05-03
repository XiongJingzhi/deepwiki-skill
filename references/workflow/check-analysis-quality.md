# check-analysis-quality：分析质量门控子步骤

> 本文档描述 `validate-analysis` 内部的质量门控规则：在 `extract-docs` 完成后，用脚本自动检查 `module-analysis.json` 是否满足最低质量标准。它通常不作为外部主流程步骤单独执行，除非需要调试质量门控。


## 契约

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/quality/check_analysis_quality.py <项目路径> [--verbose] [--json FILE]` |
| **输入** | `cache/module-analysis.json` |
| **输出** | 质量报告（stdout），退出码（0/1/2） |
| **前置** | `extract-docs` |
| **后置** | exit=0 → `validate-analysis` 继续构建证据索引；exit=1 → 增量补充后重跑本工具；exit=2 → 重跑 `extract-docs` |

## 执行方式

从技能目录运行门控脚本：

```bash
python scripts/quality/check_analysis_quality.py <项目目录绝对路径>
python scripts/quality/check_analysis_quality.py <项目目录绝对路径> --verbose
python scripts/quality/check_analysis_quality.py <项目目录绝对路径> --json gate-report.json
```

---

## 质量门控标准

### 模块级必需字段（缺失 → 该模块标记为"需补充"）

| 字段 | 失败条件 | 原因 |
|------|---------|------|
| `module_path` | 缺失或为空 | 依赖综合规则和模块文档需要此字段定位模块 |
| `module_summary` | 缺失或为空 | generate-overview/generate-module-docs 文档生成的核心输入 |
| `semantic_group` | 缺失或为空 | 菜单分组和跨模块一致性的基础 |
| `selected_components` | 缺失、为空或不是列表 | generate-module-docs 直接使用，缺失则退化为重新决策 |

### 模块级认知结构字段（缺失 → 该模块标记为"需补充"）

| 字段 | 失败条件 | 原因 |
|------|---------|------|
| `module_role` | 缺失或为空 | 文档拓扑和 overview 需要明确模块在系统中的读者视角角色 |
| `upstream_inputs` | 缺失、为空或不是列表 | 运行路径和依赖说明需要知道模块接收什么输入 |
| `downstream_outputs` | 缺失、为空或不是列表 | 运行路径和副作用说明需要知道模块产出什么 |
| `risk_points` | 缺失、为空或不是列表 | generate-module-docs 需要明确边界条件和维护风险 |
| `extension_points` | 缺失、为空或不是列表 | 文档必须帮助读者定位可扩展入口 |

### 模块级推荐字段（缺失 → 警告，不影响门控结果）

| 字段 | 缺失影响 |
|------|---------|
| `code_purpose` | generate-module-docs 组件选择可能不准确 |
| `analysis_depth` | 无法判断分析质量基线 |
| `dependency_hints` | generate-overview / generate-module-docs 的依赖综合摘要将降级为从结构化 import 关系推断 |

### 文件级必需字段（缺失 → 其所属模块标记为"需补充"）

| 字段 | 失败条件 |
|------|---------|
| `path` | 缺失或为空 |
| `summary` | 缺失或为空 |

### 文件级推荐字段（整个模块均缺失 → 警告）

- `public_interfaces`：空列表意味着generate-module-docs 无接口表格，会降级为 Basic 文档
- `public_interfaces[].line/end_line`：缺失时 generate-module-docs 无法生成精确源码范围，只能降级为文件级链接
- `core_source_ranges`：缺失时 `相关源文件` 和核心逻辑源码讲解缺少稳定输入，需从源码重新推导
- `key_insights`：缺失意味着generate-module-docs 无设计意图说明，无法解释 WHY

> **例外**：`code_purpose` 为 `Config`、`Test`、`Util` 的模块不检查 `public_interfaces` 和 `key_insights`（这类模块接口稀少属正常情况）。

---

## 退出码

| 退出码 | 含义 | 处理方式 |
|--------|------|---------|
| 0 | 全部模块通过最低质量标准 | `validate-analysis` 继续构建 `evidence-index.json` |
| 1 | 存在需补充的模块 | 对失败模块增量补充分析，再重跑门控 |
| 2 | `module-analysis.json` 不存在或格式错误 | 重新运行 extract-docs |

---

## 不通过时的增量补充流程

当门控返回退出码 1 时，**不需要全量重做extract-docs**，只需对失败模块补充缺失字段：

1. 读取门控报告，获取失败模块列表和缺失字段
2. 对每个失败模块，仅针对缺失字段重新分析：
   - 缺 `public_interfaces` → 重读该模块的核心文件，仅提取导出接口
   - 缺 `public_interfaces[].line/end_line` 或 `core_source_ranges` → 重读核心函数/类定义，补充 1-based 闭区间源码范围
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
| generate-module-docs 质量检查阶段 | generate-module-docs 之后 | `wiki/deep-dive/*.md`、`wiki/reference/*.md` 等 | 确保生成输出质量，收尾检查 |

两者互补：前置门控减少generate-module-docs 收尾质检发现问题的概率；generate-module-docs 收尾质检作为最终安全网。
