# DeepWiki 优化设计方案

> 设计日期：2026-04-23
> 状态：待实现

## 背景

基于对 DeepWiki 项目全量源码的第一性原理分析，识别出以下核心问题：

| 优先级 | 问题 | 影响 |
|--------|------|------|
| **P0** | Context Budget 无管控 | 大项目（80+ 文件）可能静默截断 |
| **P1** | 文件重要性评分归一化缺陷 | `constants.py` 可能被误判为高优先级 |
| **P1** | 第 5 步依赖综合无验证 | 架构图准确性存疑 |
| **P2** | 源码追溯行号不验证 | `file://` 链接行号可能错误 |
| **P2** | AI 生成模板无抗幻觉机制 | 推断与事实难以区分 |

---

## 方案一：Context Budget 管控（P0）

### 问题诊断

当前 `SKILL.md` 第 4 步让 AI 深度阅读"每个文件"，但没有文件数量上限或分批策略。大项目会导致：
- 静默截断（后面文件未分析）
- 质量参差不齐

### 解决方案：三阶段漏斗 + 显式 Budget 约束

```
阶段 1：快速扫描（所有核心文件）
  - 仅读取文件元数据 + extract_docs.py 输出
  - 不读完整源码
  - 产出：每模块的"文档骨架"

阶段 2：重点深入（Budget 允许范围内）
  - 按 importance_score 排序
  - 预估每个文件的 token 消耗（字符数 / 4）
  - 动态计算可处理文件数

阶段 3：按需补读（生成阶段发现缺口时）
  - 回读具体文件（按需加载）
```

### 实现载体

在 `structure.json` 新增字段：

```json
{
  "context_budget": {
    "total_tokens": 120000,
    "reserved_for_generation": 40000,
    "available_for_analysis": 80000,
    "estimated_file_costs": {
      "src/engine/core.py": 3200,
      "src/utils/helper.py": 800
    }
  }
}
```

### 修改文件

- `scripts/analyze_project.py`：新增 `estimate_token_cost()` 和 `compute_context_budget()`
- `SKILL.md`：第 4 步增加分阶段处理指令

---

## 方案二：文件重要性评分归一化优化（P1）

### 问题诊断

当前代码：
```python
if 'src' in parts or 'lib' in parts:
    path_score = 1.0  # 所有 src/ 下的文件同分
```

结果：`src/constants.py` 可能被误判为高优先级。

### 解决方案：模块内百分位归一化

```
步骤 1：首次扫描，计算所有文件的原始 4 组分数
步骤 2：按模块分组（src/core/, src/utils/, src/config/...）
步骤 3：在每个模块内部，计算 path_score 的百分位
        - P90 以上 → path_score_normalized = 1.0
        - P70-P90  → path_score_normalized = 0.8
        - P50-P70  → path_score_normalized = 0.6
        - P30-P50  → path_score_normalized = 0.4
        - P30 以下 → path_score_normalized = 0.2
步骤 4：用归一化后的 path_score 重新计算总重要性
```

### 实现载体

新增 `normalize_path_scores()` 函数：

```python
def normalize_path_scores(files: List[Dict], modules: List[Dict]) -> List[Dict]:
    """模块内百分位归一化 path_score"""
    for mod in modules:
        mod_files = [f for f in files if f['path'].startswith(mod['path'])]
        if not mod_files:
            continue
        path_scores = [f['raw_path_score'] for f in mod_files]
        for f in mod_files:
            percentile = sum(1 for s in path_scores if s < f['raw_path_score']) / len(path_scores)
            f['path_score_normalized'] = _percentile_to_score(percentile)
            f['importance_score'] = _recalculate(f)
    return files
```

### 修改文件

- `scripts/analyze_project.py`：新增归一化逻辑
- `tests/test_analyze_project.py`：新增测试用例

---

## 方案三：第 5 步依赖综合验证机制（P1）

### 问题诊断

- 完全依赖 AI 的"理解"，无 Python 辅助验证
- 输出 JSON 格式不对时，后续步骤无容错
- `detect_changes.py` 的反向依赖与第 5 步可能矛盾

### 解决方案：双轨交叉验证 + Schema 强校验

**轨道 A：Python 预分析（可信基线）**

```python
def extract_import_relations(files: List[Path], project_root: Path) -> Dict[str, List[str]]:
    """基于正则提取文件级 import 关系（作为基线）"""
    relations = {}
    for fpath in files:
        content = fpath.read_text(encoding='utf-8', errors='ignore')
        imports = _extract_imports(content, fpath.suffix)
        resolved = _resolve_import_to_module(imports, fpath, project_root)
        relations[str(fpath.relative_to(project_root))] = resolved
    return relations
```

输出到 `cache/import-relations.json`。

**轨道 B：AI 综合分析（语义理解）**

AI 输出依赖关系时，要求解释证据来源：

```json
{
  "core_dependencies": [
    {
      "from": "auth",
      "to": "user",
      "type": "Import",
      "importance": 4,
      "evidence": "src/auth/login.py:12: from user.service import get_user"
    }
  ]
}
```

**交叉验证规则**：

| 情况 | 处理 |
|------|------|
| AI + Python 都有 | ✅ 高置信度，采纳 |
| 仅 AI 有 | ⚠️ 标记为"推断依赖" |
| 仅 Python 有 | ⚠️ AI 可能遗漏 |
| AI 与 Python 冲突 | ❌ 标记为"待确认" |

**Schema 强校验**：

新增 `schemas/dependency-schema.json`：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["core_dependencies", "architecture_layers", "reverse_dependencies"],
  "properties": {
    "core_dependencies": {
      "type": "array",
      "maxItems": 50,
      "items": {
        "type": "object",
        "required": ["from", "to", "type", "importance"],
        "properties": {
          "type": {"enum": ["Import", "FunctionCall", "Inheritance", "Composition", "DataFlow", "Module"]},
          "importance": {"type": "integer", "minimum": 1, "maximum": 5}
        }
      }
    }
  }
}
```

### 修改文件

- `scripts/extract_structure.py`：新增 `extract_import_relations()`
- 新增 `schemas/dependency-schema.json`
- `references/prompts.md`：增加证据来源要求

---

## 方案四：源码追溯行号验证（P2）

### 问题诊断

`check_quality.py` 只验证文件存在，不验证行号是否正确。

### 解决方案：行号范围验证 + 自动修正

```python
def validate_source_link(file_path: str, line_start: int, line_end: int, 
                         expected_content: str = None) -> Tuple[bool, Optional[int], Optional[int]]:
    """
    验证行号范围是否有效，并尝试定位正确行号。
    Returns: (is_valid, corrected_start, corrected_end)
    """
    try:
        lines = Path(file_path).read_text(encoding='utf-8', errors='ignore').splitlines()
    except:
        return False, None, None
    
    if line_start < 1 or line_end > len(lines):
        return False, None, None
    
    if expected_content:
        for i, line in enumerate(lines, 1):
            if expected_content.strip() in line.strip():
                return False, i, i + (line_end - line_start)
    
    return True, line_start, line_end
```

### 修改文件

- `scripts/check_quality.py`：增强验证逻辑
- `tests/test_check_quality.py`：新增测试用例

---

## 方案五：AI 生成模板抗幻觉机制（P2）

### 问题诊断

`prompts.md` 模板是写作指令而非约束，AI 会幻觉填充。

### 解决方案：置信度标注 + 三级证据链

**模板改造**：

```markdown
## 1. 模块概述

### 核心职责
{{ CORE_RESPONSIBILITY }}

**证据来源**：
- [ ] 直接来自代码注释（高置信）
- [ ] 从代码结构推断（中置信）
- [ ] 从命名约定推断（低置信）
- [ ] 无明确证据（需人工确认）

**置信度**：🟢 高 / 🟡 中 / 🔴 低
```

**生成规则**（嵌入 `prompts.md`）：

```
## 置信度标注规范

1. **高置信（🟢）**：断言直接来自源码或文档注释
2. **中置信（🟡）**：断言从代码结构推断
3. **低置信（🔴）**：断言从命名约定或常见模式推断

**禁止**：无证据来源的高置信断言。
**优先级**：文档优先呈现高置信内容，低置信内容折叠或标注"待确认"。
```

### 修改文件

- `references/prompts.md`：增加置信度标注规范
- `references/templates.md`：模板改造

---

## 方案六：模板组件化重构（P1）

### 问题诊断

当前 `templates.md` 存在以下问题：

| 问题 | 具体表现 | 根因 |
|------|----------|------|
| **结构固化** | 每个项目都生成相同的章节结构 | 模板是"填空题"而非"作文题" |
| **占位符过细** | `{{ FEATURE_1_NAME }}` 等要求 AI 按固定数量填充 | 假设项目一定有 N 个特性 |
| **项目类型无感知** | SDK 和前端 SPA 用同一套模板 | 缺少"认知框架"分支 |
| **扩展性差** | 新增文档类型需要修改模板文件 | 模板是硬编码的 Markdown |

### 解决方案：组件化模板系统

#### 核心设计思想

借鉴 deepwiki-rs 的架构模式：

1. **双层处理策略**：规则层快速筛选必需组件 + AI 层补充语义推荐
2. **CodePurpose 映射**：25 种文件角色 → 默认组件集
3. **韧性降级**：每个组件都有 fallback 方案
4. **标准化定义**：每个组件有 name/purpose/format/trigger/fallback 5 个属性

#### 组件清单（15 个）

| 优先级 | 组件 | 用途 | 触发方式 |
|:------:|------|------|----------|
| P0 | `overview` | 模块概述 | 必需 |
| P0 | `nav-links` | 导航链接 | 必需 |
| P0 | `api-table` | 接口总览 | 必需 |
| P1 | `sequence-diagram` | 时序图 | 规则 + AI 补充 |
| P1 | `code-walkthrough` | 核心代码讲解 | 规则（复杂度阈值） |
| P1 | `architecture-diagram` | 架构图 | 规则（模块数阈值） |
| P2 | `class-diagram` | 类图 | 规则（有类定义） |
| P2 | `state-diagram` | 状态图 | 规则（有状态管理） |
| P2 | `dependency-diagram` | 依赖图 | 规则（依赖数阈值） |
| P2 | `decision-table` | 决策表 | 规则（有策略分支） |
| P2 | `code-example` | 代码示例 | 规则（接口数阈值） |
| P3 | `error-table` | 错误处理表 | 规则（有错误定义） |
| P3 | `file-structure` | 文件结构 | 规则（文件数阈值） |
| P3 | `usage-patterns` | 使用模式 | AI 推荐 |

#### 组件标准化定义

每个组件必须定义以下属性：

```yaml
name: sequence-diagram
purpose: 展示跨组件/模块的交互流程和时序
format: Mermaid sequenceDiagram / 流程表格 / 文字列表
trigger:
  - CodePurpose in [Api, Service, Agent, Entry, Command]
  - OR 模块有跨组件数据流
fallback:
  - 若参与者 > 8，拆分为多张子图
  - 若 LLM 生成失败，使用流程表格替代
required_context:
  - 接口签名
  - 依赖关系
  - 关键函数调用链
```

#### CodePurpose → 组件映射

| CodePurpose | 默认组件集 |
|-------------|-----------|
| Entry | overview → architecture-diagram → sequence-diagram → nav-links |
| Agent | overview → sequence-diagram → code-walkthrough → state-diagram → nav-links |
| Page | overview → architecture-diagram → api-table → code-example → nav-links |
| Service | overview → api-table → sequence-diagram → code-walkthrough → nav-links |
| Api | overview → api-table → sequence-diagram → code-walkthrough → error-table → nav-links |
| Model | overview → class-diagram → api-table → nav-links |
| Util | overview → api-table → code-example → nav-links |

#### 时序图生成规范（重点）

**触发条件矩阵**：

| 模块特征 | 必需生成时序图 | 可选生成 |
|---------|:--------------:|:--------:|
| API 端点/路由处理 | ✅ | |
| 中间件链 | ✅ | |
| Agent 决策流程 | ✅ | |
| 多 Agent 协作 | ✅ | |
| 前后端交互 | ✅ | |
| 数据库操作 | | ✅ |
| 状态管理 | | ✅ |

**格式变体**：

- **变体A**：Mermaid sequenceDiagram（参与者 <= 6）
- **变体B**：流程表格（参与者 > 6，或流水线）
- **变体C**：文字步骤列表（简单线性流程）

#### 核心代码讲解规范

**触发条件**：

- 函数复杂度 >= 50
- OR CodePurpose in [Agent, Service, Api, Command]
- OR 文件包含设计模式实现
- OR 核心算法

**格式**：

- 代码块 + 行内注释 + 逐块讲解表格
- 或：带注释代码 + 关键点说明

### 实现载体

新增 `references/components.md`：组件注册表

修改 `references/templates.md`：重构为"骨架 + 组件引用"

修改 `references/prompts.md`：更新生成逻辑

### 预期收益

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| 模板灵活性 | 固定章节结构 | 动态组装，按需生成 |
| 项目类型支持 | 无差异 | 25 种 CodePurpose 各有默认配置 |
| 时序图支持 | 可选 | Agent/API/Service 必需生成 |
| 代码讲解 | 无专门组件 | 核心算法/复杂逻辑必讲 |
| 扩展性 | 新增类型需改模板 | 新增组件即可 |

---

## 预期收益

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| 大项目支持 | 80+ 文件可能溢出 | 显式 Budget 管控，可处理 200+ 文件 |
| 核心文件识别 | `constants.py` 可能误判 | 模块内归一化，准确区分 |
| 依赖图可信度 | 纯 AI 推断 | 双轨交叉验证，标注置信度 |
| 源码追溯 | 只验证文件存在 | 验证行号范围，可自动修正 |
| 文档可信度 | 无法区分推断与事实 | 三级置信度标注 |
| 模板灵活性 | 固定章节结构 | 组件化，动态组装 |

---

## 实现顺序

```
1. P1 归一化（独立，无依赖）
2. P1 依赖验证（独立）
3. P1 模板组件化（独立）
4. P0 Context Budget（依赖 P1 的排序输出）
5. P2 行号验证（独立）
6. P2 抗幻觉（依赖 P0 的分阶段输出）
```
