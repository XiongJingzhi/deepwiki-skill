# DeepWiki Source Intelligence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 deepwiki-skill 从“文档生成型 skill”升级为“源码认知编译型 skill”，补齐文档拓扑规划、证据索引、增量重编译与最小工程化闭环。

**Architecture:** 保留现有 `analyze_project -> extract_structure -> detect_changes` 主骨架，在其上新增 Documentation Planning Layer，并把后半段生成流程改为“先规划、后编译、再验证”。实现重点是收紧缓存契约、引入 `doc-topology.json` / `generation-plan.json` / `evidence-index.json`，并让 skill 文档与脚本行为对齐。

**Tech Stack:** Python 3.9+、pytest、Markdown workflow docs、JSON cache contracts、tree-sitter language bindings、现有 `scripts/` CLI。

**Implementation Status:** 第一轮基线已合并到 `master` 并通过完整测试。Task 1-10 均已落地，后续增强可继续围绕正文编译器、跨语言语义提取深度和更严格的证据覆盖率展开。

---

### Task 1: 明确缓存契约与系统索引

**Files:**
- Modify: `references/system-reference.md`
- Modify: `references/rules/analysis-output-spec.md` or create if absent
- Modify: `schemas/meta-schema.json`

**Step 1: 为缓存文件建立统一索引表**

在 `references/system-reference.md` 中新增或重写 `.deepwiki/cache/` 章节，列出：

- `structure.json`
- `code-structure.json`
- `module-analysis.json`
- `doc-topology.json`
- `generation-plan.json`
- `evidence-index.json`

每个文件要写明：

- 生产阶段
- 消费阶段
- 是否允许 AI 写入
- 是否允许增量复用

**Step 2: 为新增缓存文件补规范文档**

在输出规范文档里新增 3 个新契约的小节：

- `doc-topology.json`
- `generation-plan.json`
- `evidence-index.json`

每节至少写：

- 最小字段
- 字段语义
- 降级策略

**Step 3: 如 schema 需要索引缓存元信息，补到 schema**

如果 `meta-schema.json` 承担输出目录约束，则补充缓存文件枚举或说明字段。

**Step 4: 验证**

Run: `rg -n "doc-topology|generation-plan|evidence-index" references schemas`
Expected: 新缓存文件在规范文档中均可被检索到

**Step 5: Commit**

```bash
git add references/system-reference.md references/rules/analysis-output-spec.md schemas/meta-schema.json
git commit -m "docs: define source intelligence cache contracts"
```

### Task 2: 将模块发现降级为候选发现

**Files:**
- Modify: `scripts/module_discovery.py`
- Modify: `scripts/analyze_project.py`
- Test: `tests/test_module_discovery.py`

**Step 1: 先写失败测试，覆盖候选模块语义**

在 `tests/test_module_discovery.py` 中新增测试，期望 `discover_modules()` 输出包含候选标记，例如：

```python
def test_discover_modules_marks_candidates(fake_project):
    modules = discover_modules(fake_project, all_files=[])
    assert all("is_candidate" in mod for mod in modules)
```

**Step 2: 运行单测确认失败**

Run: `pytest tests/test_module_discovery.py -q`
Expected: FAIL，提示缺少 `is_candidate` 或相关字段

**Step 3: 最小实现**

在 `scripts/module_discovery.py` 中：

- 将当前目录发现结果明确标记为 `is_candidate: true`
- 增加 `discovery_basis`，值可为 `directory`, `workspace`, `fallback-root`
- 为后续修正预留 `refined_by` 空列表

在 `scripts/analyze_project.py` 中保留现有 `modules` 输出，但补充 `module_candidates` 或让 `modules` 含候选语义。

**Step 4: 运行单测**

Run: `pytest tests/test_module_discovery.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/module_discovery.py scripts/analyze_project.py tests/test_module_discovery.py
git commit -m "feat: mark discovered modules as candidates"
```

### Task 3: 扩展 `code-structure.json` 的事实层能力

**Files:**
- Modify: `scripts/extract_structure.py`
- Modify: `scripts/parsers.py` if needed
- Test: `tests/test_extract_structure.py`

**Step 1: 写失败测试，验证新字段存在**

在 `tests/test_extract_structure.py` 中新增断言，至少检查返回值含：

- `registration_points`
- `state_access_paths`
- `config_entry_points`
- `cross_module_bridges`

**Step 2: 运行单测确认失败**

Run: `pytest tests/test_extract_structure.py -q`
Expected: FAIL，提示字段不存在

**Step 3: 最小实现**

在 `scripts/extract_structure.py` 中先实现保底版本：

- 输出空数组或空字典作为新字段
- 为后续真实提取留出函数接口

然后逐步把现有模式检测结果映射成基础事实：

- 从入口和 manifest 推导 `config_entry_points`
- 从 import / call graph 边界推导 `cross_module_bridges`

**Step 4: 运行单测**

Run: `pytest tests/test_extract_structure.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/extract_structure.py tests/test_extract_structure.py
git commit -m "feat: expand code structure facts for planning"
```

### Task 4: 新增文档拓扑规划阶段

**Files:**
- Create: `scripts/plan_doc_topology.py`
- Modify: `SKILL.md`
- Modify: `references/workflow/` add `plan-doc-topology.md`
- Test: `tests/test_plan_doc_topology.py`

**Step 1: 写失败测试**

新建 `tests/test_plan_doc_topology.py`，断言脚本运行后生成 `doc-topology.json` 和 `generation-plan.json`。

```python
def test_plan_doc_topology_generates_outputs(fake_python_project):
    result = plan_doc_topology(fake_python_project)
    assert "pages" in result["doc_topology"]
    assert "pages" in result["generation_plan"]
```

**Step 2: 运行单测确认失败**

Run: `pytest tests/test_plan_doc_topology.py -q`
Expected: FAIL，模块或函数不存在

**Step 3: 最小实现**

创建 `scripts/plan_doc_topology.py`：

- 读取 `structure.json`、`code-structure.json`
- 生成基础页面集合：
  - `overview`
  - `getting-started`
  - `doc-map`
  - `modules/<module>.md`
  - `api/<module>.md`
- 产出 `doc-topology.json`
- 产出 `generation-plan.json`

**Step 4: 将新阶段接入 skill 文档**

在 `SKILL.md` 中把主路径改为：

`... -> extract-docs -> plan-doc-topology -> check-analysis-quality -> ...`

并新增对应 workflow 索引。

**Step 5: 运行单测**

Run: `pytest tests/test_plan_doc_topology.py -q`
Expected: PASS

**Step 6: Commit**

```bash
git add scripts/plan_doc_topology.py SKILL.md references/workflow/plan-doc-topology.md tests/test_plan_doc_topology.py
git commit -m "feat: add document topology planning stage"
```

### Task 5: 让菜单生成改为 topology-first

**Files:**
- Modify: `scripts/generate_menu.py`
- Test: `tests/test_generate_menu.py`

**Step 1: 写失败测试**

在 `tests/test_generate_menu.py` 中新增测试，给出 `doc-topology.json`，期望菜单优先使用 topology 中的页面分组。

**Step 2: 运行单测确认失败**

Run: `pytest tests/test_generate_menu.py -q`
Expected: FAIL，仍按磁盘扫描逻辑分组

**Step 3: 最小实现**

在 `scripts/generate_menu.py` 中加入：

- 优先读取 `doc-topology.json`
- 若存在则基于 topology 构建分区与排序
- 磁盘扫描只作为校验和回退

**Step 4: 运行单测**

Run: `pytest tests/test_generate_menu.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/generate_menu.py tests/test_generate_menu.py
git commit -m "feat: make menu generation topology-first"
```

### Task 6: 升级分析质量门控为认知结构门控

**Files:**
- Modify: `scripts/check_analysis_quality.py`
- Modify: `schemas/module-analysis-schema.json`
- Test: `tests/test_check_quality.py`

**Step 1: 写失败测试**

新增测试，要求模块分析最少包含：

- `module_role`
- `upstream_inputs`
- `downstream_outputs`
- `risk_points`
- `extension_points`

**Step 2: 运行单测确认失败**

Run: `pytest tests/test_check_quality.py -q`
Expected: FAIL，当前字段检查不足

**Step 3: 最小实现**

在 `scripts/check_analysis_quality.py` 中：

- 区分“最低必需字段”和“deepwiki 认知字段”
- 对缺失认知字段给出 error 或 warning
- 输出更易读的缺失结构摘要

同步更新 `schemas/module-analysis-schema.json`。

**Step 4: 运行单测**

Run: `pytest tests/test_check_quality.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/check_analysis_quality.py schemas/module-analysis-schema.json tests/test_check_quality.py
git commit -m "feat: strengthen module analysis quality gate"
```

### Task 7: 新增证据索引与文档一致性检查

**Files:**
- Create: `scripts/build_evidence_index.py`
- Modify: `scripts/check_doc_quality.py`
- Test: `tests/test_check_quality.py`

**Step 1: 写失败测试**

新增测试，要求文档质量检查可识别无证据结论或至少读取 `evidence-index.json`。

**Step 2: 运行单测确认失败**

Run: `pytest tests/test_check_quality.py -q`
Expected: FAIL，当前检查未读取证据索引

**Step 3: 最小实现**

创建 `scripts/build_evidence_index.py`：

- 从 `module-analysis.json`、`code-structure.json` 生成基础证据索引

在 `scripts/check_doc_quality.py` 中：

- 读取 `evidence-index.json`
- 对关键页面缺证据时给出 warning 或 error

**Step 4: 运行单测**

Run: `pytest tests/test_check_quality.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/build_evidence_index.py scripts/check_doc_quality.py tests/test_check_quality.py
git commit -m "feat: add evidence-aware doc validation"
```

### Task 8: 让增量更新升级为页面级重编译计划

**Files:**
- Modify: `scripts/detect_changes.py`
- Modify: `scripts/plan_doc_topology.py`
- Test: `tests/test_detect_changes.py`

**Step 1: 写失败测试**

在 `tests/test_detect_changes.py` 中新增测试，期望变更检测输出受影响页面列表或受影响页面分组。

**Step 2: 运行单测确认失败**

Run: `pytest tests/test_detect_changes.py -q`
Expected: FAIL，当前结果只有文件和模块层信息

**Step 3: 最小实现**

在 `scripts/detect_changes.py` 中：

- 读取 `generation-plan.json`
- 把变更模块映射为受影响页面
- 新增输出字段：
  - `affected_pages`
  - `recompile_all`

**Step 4: 运行单测**

Run: `pytest tests/test_detect_changes.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/detect_changes.py scripts/plan_doc_topology.py tests/test_detect_changes.py
git commit -m "feat: make incremental updates page-aware"
```

### Task 9: 补齐 skill 的最小工程化闭环

**Files:**
- Create: `scripts/cli.py`
- Create: `scripts/check_dependencies.py`
- Modify: `README.md`
- Test: `tests/test_integration.py`

**Step 1: 写失败测试**

新增 integration test，要求 CLI 至少支持：

- `init`
- `analyze`
- `extract-structure`
- `plan-doc-topology`
- `quality`

**Step 2: 运行单测确认失败**

Run: `pytest tests/test_integration.py -q`
Expected: FAIL，CLI 不存在

**Step 3: 最小实现**

创建 `scripts/cli.py`：

- 用 `argparse` 封装现有脚本入口

创建 `scripts/check_dependencies.py`：

- 检查 `tree_sitter` 与各语言绑定是否可导入
- 输出明确安装建议

更新 `README.md` 的本地验证说明。

**Step 4: 运行单测**

Run: `pytest tests/test_integration.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/cli.py scripts/check_dependencies.py README.md tests/test_integration.py
git commit -m "feat: add CLI and dependency self-check for skill workflow"
```

### Task 10: 端到端校验与收尾

**Files:**
- Modify: `docs/plans/2026-04-24-source-intelligence-design.md`
- Modify: `docs/plans/2026-04-24-source-intelligence-implementation.md`

**Step 1: 运行 targeted tests**

Run:

```bash
pytest tests/test_module_discovery.py tests/test_extract_structure.py tests/test_generate_menu.py tests/test_detect_changes.py tests/test_check_quality.py tests/test_integration.py -q
```

Expected: PASS

**Step 2: 运行依赖自检**

Run: `python scripts/check_dependencies.py`
Expected: 清晰列出依赖状态；缺失时返回非零并给出修复提示

**Step 3: 运行 fake-project smoke flow**

Run:

```bash
python scripts/cli.py init /tmp/fake-project
python scripts/cli.py analyze /tmp/fake-project
python scripts/cli.py extract-structure /tmp/fake-project
python scripts/cli.py plan-doc-topology /tmp/fake-project
python scripts/cli.py quality /tmp/fake-project/.deepwiki
```

Expected: 成功生成缓存，失败时提示明确

**Step 4: 更新设计与计划状态**

将设计文档和计划文档中的状态更新为实施中或已完成的阶段摘要。

**Step 5: Commit**

```bash
git add docs/plans/2026-04-24-source-intelligence-design.md docs/plans/2026-04-24-source-intelligence-implementation.md
git commit -m "docs: finalize source intelligence rollout plan"
```
