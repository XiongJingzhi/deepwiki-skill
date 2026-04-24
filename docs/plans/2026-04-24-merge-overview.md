# 合并 index.md + architecture.md → overview.md

> **Goal:** 将概览阶段的两份输出文档合并为一份技术概览文档 `overview.md`，以架构为主线，融入项目介绍和导航。不再生成 `index.md` 和 `architecture.md`。

**Architecture:**
- `templates.md`：删除"首页骨架"和"架构文档骨架"两个章节，新增"概览文档骨架"章节（`overview.md`）
- `step6-overview.md`：文档列表从两行改为一行 `overview.md`；`progress.json` 追踪字段对应更新
- `generate_menu.py`：根文件扫描白名单从 `(index.md, architecture.md, getting-started.md, doc-map.md)` 改为 `(overview.md, getting-started.md, doc-map.md)`；`modules/` 内排除 `index.md` 的逻辑保留不变
- `init_wiki.py`：`progress.json` 初始化的 `phases.overview.documents` 改为 `{overview.md, getting-started.md, doc-map.md}`
- `SKILL.md`：输出目录树中替换文件名
- 测试文件：fixture 中的 `index.md`/`architecture.md` 替换为 `overview.md`

**Tech Stack:** Python 3.10, pytest, Markdown

---

## Task 1：更新 templates.md 骨架

**Files:**
- Modify: `references/templates.md`

将 `## 目录` 中的"首页骨架"和"架构文档骨架"条目替换为"概览文档骨架"。

删除 `## 首页骨架`（L66-L120）和 `## 架构文档骨架`（L122-L184）两个章节，替换为：

```markdown
## 概览文档骨架

> 对应输出文件 `overview.md`。以架构为主线，融入项目定位和文档导航。

```markdown
# {PROJECT_NAME}

[徽章：技术栈、版本、语言等]

> {一句话定位}

---

## 项目概述

[overview 组件：项目解决的核心问题、适用场景、关键设计理念]

---

## 技术栈

[api-table 组件：语言/框架/工具 三列表格]

---

## 系统架构

[architecture-diagram 组件：flowchart TB 分层架构图，P0 必需]

[分层说明：每层职责一句话，来自第 5 步 RelationshipSummary]

---

## 模块说明

[对每个模块：名称（链接到模块文档）、职责一句话、关键依赖]

---

## 数据流（条件：项目涉及 API 调用或跨组件数据传递）

[sequence-diagram 组件：展示最核心的一条调用链]

---

## 模块依赖图（条件：模块数 ≥ 4）

[dependency-diagram 组件：flowchart LR]

---

## 目录结构（条件：项目目录结构非平凡）

[file-structure 组件]

---

## 文档导航

[nav-links 组件：getting-started.md、doc-map.md、各模块文档入口]
```
```

同时更新 `## 目录` 中的序号列表：将条目 2（首页骨架）和条目 3（架构文档骨架）合并为一条"概览文档骨架"，其后各条顺序前移。

**Commit:**
```bash
git add references/templates.md
git commit -m "docs: replace index/architecture skeletons with unified overview.md skeleton"
```

---

## Task 2：更新 step6-overview.md

**Files:**
- Modify: `references/step6-overview.md`

当前 L7-L11 表格：

```markdown
| 文档 | 模板参考 | 内容要点 |
|------|---------|---------|
| `index.md` | `references/templates.md` → 首页 | 项目概述、技术栈徽章、快速导航、模块列表 |
| `architecture.md` | `references/templates.md` → 架构 | 系统架构图（Mermaid）、技术栈、模块依赖关系、架构分层（来自第 5 步输出） |
| `getting-started.md` | `references/templates.md` → 快速开始 | 前置条件、安装步骤、第一个示例、常见问题 |
```

替换为：

```markdown
| 文档 | 模板参考 | 内容要点 |
|------|---------|---------|
| `overview.md` | `references/templates.md` → 概览文档 | 项目定位、技术栈、系统架构图、分层说明、模块列表、依赖图（条件）、文档导航 |
| `getting-started.md` | `references/templates.md` → 快速开始 | 前置条件、安装步骤、第一个示例、常见问题 |
```

同时更新 L13 中 `progress.json` 追踪字段的描述，将 `index.md` 和 `architecture.md` 改为 `overview.md`。

**Commit:**
```bash
git add references/step6-overview.md
git commit -m "docs: update step6 overview document list to overview.md"
```

---

## Task 3：更新 generate_menu.py

**Files:**
- Modify: `scripts/generate_menu.py`
- Modify: `tests/test_generate_menu.py`

**Step 1: 写失败测试**

在 `tests/test_generate_menu.py` 的 `TestBuildMenu` 类末尾追加：

```python
def test_overview_md_in_overview_section(self, tmp_path):
    """overview.md 应出现在概览组中"""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")
    (wiki / "getting-started.md").write_text("# Getting Started\n", encoding="utf-8")
    result = generate_menu.build_menu(str(wiki), "TestProject")
    menu = result.get("menu", [])
    assert menu, "menu 不应为空"
    overview_group = menu[0]
    paths = [item.get("path") for item in overview_group.get("items", [])]
    assert "overview.md" in paths, "overview.md 应在概览组中"

def test_index_md_not_in_menu_when_absent(self, tmp_path):
    """不再扫描 index.md，即使文件存在也不放入概览组"""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# Home\nOld homepage.", encoding="utf-8")
    (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")
    result = generate_menu.build_menu(str(wiki), "TestProject")
    for group in result.get("menu", []):
        for item in group.get("items", []):
            assert item.get("path") != "index.md", \
                "index.md 不应出现在任何菜单组中（已被 overview.md 替代）"

def test_architecture_md_not_in_menu(self, tmp_path):
    """不再扫描 architecture.md，即使文件存在也不放入概览组"""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "architecture.md").write_text("# Architecture\nOld arch doc.", encoding="utf-8")
    (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")
    result = generate_menu.build_menu(str(wiki), "TestProject")
    for group in result.get("menu", []):
        for item in group.get("items", []):
            assert item.get("path") != "architecture.md", \
                "architecture.md 不应出现在任何菜单组中（已被 overview.md 替代）"
```

**Step 2: 运行测试，确认失败**

```bash
python -m pytest tests/test_generate_menu.py::TestBuildMenu::test_overview_md_in_overview_section \
               tests/test_generate_menu.py::TestBuildMenu::test_index_md_not_in_menu_when_absent \
               tests/test_generate_menu.py::TestBuildMenu::test_architecture_md_not_in_menu -v
```

**Step 3: 修改 generate_menu.py**

找到 `build_menu()` 中的两处白名单，按以下规则修改：

1. L80 的扫描元组：
   ```python
   # 修改前
   for filename in ('index.md', 'getting-started.md', 'architecture.md', 'doc-map.md'):
   # 修改后
   for filename in ('overview.md', 'getting-started.md', 'doc-map.md'):
   ```

2. L130 的 `known_top_files` 集合：
   ```python
   # 修改前
   known_top_files = {'index.md', 'getting-started.md', 'architecture.md', 'doc-map.md'}
   # 修改后
   known_top_files = {'overview.md', 'getting-started.md', 'doc-map.md'}
   ```

`modules/` 目录内排除 `index.md` 的逻辑（L101、L309）**保持不变**。

**Step 4: 更新受影响的已有测试 fixture**

在 `TestBuildMenu` 和 `TestReconcileMenu` 的各个测试中，将创建 `index.md` 的 fixture 改为创建 `overview.md`（只改 fixture，不改 assert 逻辑，除非 assert 内容涉及具体文件名）。

`conftest.py` 中的 `index.md` + `architecture.md` fixture 改为 `overview.md`。

**Step 5: 运行全量测试**

```bash
python -m pytest tests/test_generate_menu.py -v
```

**Step 6: Commit**

```bash
git add scripts/generate_menu.py tests/test_generate_menu.py tests/conftest.py
git commit -m "feat: replace index.md+architecture.md with overview.md in menu generation"
```

---

## Task 4：更新 init_wiki.py + progress-schema.json

**Files:**
- Modify: `scripts/init_wiki.py`
- Modify: `tests/test_init_wiki.py`

**Step 1: 写失败测试**

在 `tests/test_init_wiki.py` 末尾追加：

```python
def test_progress_json_overview_documents(tmp_path):
    """progress.json 的 overview.documents 应包含 overview.md 而非 index.md/architecture.md"""
    import json
    init_wiki.init_deep_wiki(str(tmp_path))
    progress_path = tmp_path / ".deepwiki" / "cache" / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    docs = progress["phases"]["overview"]["documents"]
    assert "overview.md" in docs, "overview.md 应在 overview.documents 中"
    assert "index.md" not in docs, "index.md 不应再出现在 overview.documents 中"
    assert "architecture.md" not in docs, "architecture.md 不应再出现在 overview.documents 中"
```

**Step 2: 运行测试，确认失败**

```bash
python -m pytest tests/test_init_wiki.py::test_progress_json_overview_documents -v
```

**Step 3: 修改 init_wiki.py**

将 `phases.overview.documents` 的初始化从：
```python
"documents": {
    "index.md": "pending",
    "architecture.md": "pending",
    "getting-started.md": "pending",
    "doc-map.md": "pending"
}
```
改为：
```python
"documents": {
    "overview.md": "pending",
    "getting-started.md": "pending",
    "doc-map.md": "pending"
}
```

**Step 4: 运行全量测试**

```bash
python -m pytest tests/test_init_wiki.py -v
```

**Step 5: Commit**

```bash
git add scripts/init_wiki.py tests/test_init_wiki.py
git commit -m "feat: update progress.json overview documents to overview.md"
```

---

## Task 5：更新 SKILL.md 输出目录树

**Files:**
- Modify: `SKILL.md`

找到输出目录树中的：
```
├── index.md
├── architecture.md
```
替换为：
```
├── overview.md
```

**Commit:**
```bash
git add SKILL.md
git commit -m "docs: update output directory tree in SKILL.md to overview.md"
```

---

## 验收标准

```bash
cd e:/Python/deepwiki-skill/tests
python -m pytest . -v --tb=short
```

期望：
- 所有已有测试 PASS（无回归）
- 3 个新测试（Task 3）+ 1 个新测试（Task 4）共 4 个新测试 PASS
- `templates.md` 中不再有"首页骨架"和"架构文档骨架"章节
- `step6-overview.md` 文档列表只有 `overview.md` 一行概览文档
- `generate_menu.py` 白名单不含 `index.md` 和 `architecture.md`
- `init_wiki.py` 初始化的 `overview.documents` 只有 `overview.md`

