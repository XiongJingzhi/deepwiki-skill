# Agentic Flow Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Archive the current DeepWiki pipeline as legacy and rebuild the root project as a clean agentic workflow driven by project inventory, semantic analysis, page planning, and per-page context.

**Architecture:** Move the current implementation into `legacy/old-pipeline/` as reference material, then create a fresh root-level skill package. The new implementation owns a small CLI, lightweight inventory scanning, strict JSON schemas, menu/finalize helpers, and Agent-facing workflow docs. No new root module imports legacy code.

**Tech Stack:** Python 3.9+, stdlib `pathlib/json/argparse/hashlib/http.server`, `pyyaml`, `jsonschema`, pytest.

---

### Task 1: Archive Old Pipeline And Scaffold Clean Root

**Files:**
- Move: current root implementation files into `legacy/old-pipeline/`
- Create: `SKILL.md`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `scripts/__init__.py`
- Create: `scripts/cli.py`
- Create: `scripts/pipeline/__init__.py`
- Create: `scripts/wiki/__init__.py`
- Create: `scripts/serve/__init__.py`
- Create: `schemas/`
- Create: `references/workflow/`
- Create: `tests/conftest.py`

**Step 1: Record current tracked files**

Run: `git ls-files > /tmp/deepwiki-old-files.txt`

Expected: list contains old `scripts/analysis/*`, old `references/workflow/*`, old tests, and current docs.

**Step 2: Move old implementation into legacy**

Move all old implementation directories and files except `.git/` into `legacy/old-pipeline/`.

Keep the already approved plan docs in root `docs/plans/` after the move. The archived copies can also remain under `legacy/old-pipeline/docs/plans/`; root docs are the active planning docs.

Use `git mv` where possible:

```bash
mkdir -p legacy/old-pipeline
git mv README.md SKILL.md pyproject.toml assets agents references schemas scripts tests legacy/old-pipeline/
```

If `docs/` was moved, restore active plans:

```bash
mkdir -p docs/plans
git checkout HEAD -- docs/plans/2026-05-07-agentic-flow-redesign-design.md
git checkout HEAD -- docs/plans/2026-05-07-agentic-flow-redesign.md
```

**Step 3: Create clean root package skeleton**

Create fresh root files:

```text
SKILL.md
README.md
pyproject.toml
scripts/__init__.py
scripts/cli.py
scripts/pipeline/__init__.py
scripts/wiki/__init__.py
scripts/serve/__init__.py
tests/conftest.py
```

The new `pyproject.toml` should keep:

```toml
[project]
name = "deepwiki-skill"
version = "3.0.0"
description = "Agentic project wiki generation skill"
requires-python = ">=3.9"
dependencies = ["pyyaml>=6.0", "jsonschema>=4.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[project.scripts]
deepwiki = "scripts.cli:main"
```

Do not include tree-sitter dependencies in the new root package.

**Step 4: Add minimal CLI placeholder**

`tools/cli.py` is not used. Put the implementation in `scripts/cli.py`.

Start with commands:

```python
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="DeepWiki agentic helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("self-check", help="Validate the clean skill package")
    args = parser.parse_args(argv)
    if args.command == "self-check":
        print("DeepWiki skill self-check passed.")
        return 0
    return 1
```

**Step 5: Run smoke command**

Run: `python -m scripts.cli self-check`

Expected: prints `DeepWiki skill self-check passed.`

**Step 6: Commit**

```bash
git add .
git commit -m "chore: archive legacy pipeline and scaffold clean agentic root"
```

### Task 2: Add New Cache Schemas

**Files:**
- Create: `schemas/project-inventory-schema.json`
- Create: `schemas/semantic-analysis-schema.json`
- Create: `schemas/page-plan-schema.json`
- Create: `schemas/page-context-schema.json`
- Test: `tests/test_agentic_schemas.py`

**Step 1: Write failing schema tests**

Create `tests/test_agentic_schemas.py` with minimal valid objects for all four schemas and validate them with `jsonschema.validate`.

Include these stable enum values:

```python
PAGE_TYPES = ["overview", "getting-started", "concept", "deep-dive", "reference", "doc-map", "custom"]
PAGE_STATUSES = ["planned", "in_progress", "completed", "failed", "skipped"]
CONFIDENCE = ["high", "medium", "low"]
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_agentic_schemas.py -v`

Expected: FAIL because schemas are missing.

**Step 3: Create schemas**

Create strict top-level schemas:

- `project-inventory-schema.json`: directory facts, file list, stats, language hints
- `semantic-analysis-schema.json`: Agent-authored project mental model and evidence
- `page-plan-schema.json`: sections, pages, generation order, menu seed
- `page-context-schema.json`: one page's objective, source files, excerpts, related pages, claims, symbols, constraints

Use `additionalProperties: false` at top-level. Use nested `additionalProperties: true` only for Agent-authored flexible content fields such as `architecture_model.details`.

**Step 4: Run tests**

Run: `pytest tests/test_agentic_schemas.py -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add schemas tests/test_agentic_schemas.py
git commit -m "feat: define clean agentic cache schemas"
```

### Task 3: Implement `init` And `prepare-inventory`

**Files:**
- Create: `scripts/wiki/init_wiki.py`
- Create: `scripts/pipeline/prepare_inventory.py`
- Modify: `scripts/cli.py`
- Test: `tests/test_init_wiki.py`
- Test: `tests/test_prepare_inventory.py`

**Step 1: Write failing init tests**

Create `tests/test_init_wiki.py`:

```python
from scripts.wiki.init_wiki import init_wiki


def test_init_wiki_creates_clean_layout(tmp_path):
    result = init_wiki(tmp_path)
    assert result["success"] is True
    assert (tmp_path / ".deepwiki" / "cache" / "page-context").is_dir()
    assert (tmp_path / ".deepwiki" / "state").is_dir()
    assert (tmp_path / ".deepwiki" / "wiki").is_dir()
    assert (tmp_path / ".deepwiki" / "config.yaml").exists()
```

**Step 2: Write failing inventory tests**

Create `tests/test_prepare_inventory.py`:

```python
import json

from scripts.pipeline.prepare_inventory import prepare_inventory


def test_prepare_inventory_classifies_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "app.py").write_text("def main(): pass\n", encoding="utf-8")
    (tmp_path / "tests" / "test_app.py").write_text("def test_app(): pass\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Sample\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")

    inventory = prepare_inventory(tmp_path)
    by_path = {item["path"]: item for item in inventory["files"]}

    assert by_path["src/app.py"]["category"] == "code"
    assert by_path["tests/test_app.py"]["is_test"] is True
    assert by_path["README.md"]["is_doc"] is True
    assert by_path["pyproject.toml"]["is_config"] is True
    assert "python" in inventory["languages"]
    assert "pip" in inventory["package_managers"]
    assert inventory["entry_candidates"]


def test_prepare_inventory_writes_cache_file(tmp_path):
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")
    inventory = prepare_inventory(tmp_path, save_to_cache=True)
    output = tmp_path / ".deepwiki" / "cache" / "project-inventory.json"
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["project_name"] == inventory["project_name"]
```

**Step 3: Run tests to verify failure**

Run: `pytest tests/test_init_wiki.py tests/test_prepare_inventory.py -v`

Expected: FAIL because modules are missing.

**Step 4: Implement `init_wiki`**

Create `.deepwiki/cache/page-context`, `.deepwiki/state`, `.deepwiki/wiki`, and `config.yaml`.

The config can be minimal:

```yaml
generation:
  language: zh
  mode: agentic
```

**Step 5: Implement `prepare_inventory`**

Use only stdlib scanning:

```python
LANG_BY_EXT = {".py": "python", ".ts": "typescript", ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript", ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin"}
CONFIG_NAMES = {"pyproject.toml", "package.json", "pnpm-lock.yaml", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "vite.config.ts", "next.config.js"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst"}
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".tar", ".gz", ".mp4", ".mp3", ".woff", ".woff2"}
IGNORE_DIRS = {".git", ".deepwiki", "node_modules", "dist", "build", "__pycache__", ".venv", "venv"}
```

Hash files with `hashlib.sha256`, capped reading is acceptable for very large files if documented.

Do not import from `legacy/old-pipeline`.

**Step 6: Add CLI commands**

Add:

```bash
deepwiki init <project_path>
deepwiki prepare-inventory <project_path>
```

**Step 7: Run tests**

Run: `pytest tests/test_init_wiki.py tests/test_prepare_inventory.py -v`

Expected: PASS.

**Step 8: Commit**

```bash
git add scripts tests
git commit -m "feat: add clean init and inventory preparation"
```

### Task 4: Implement Page Plan Validation

**Files:**
- Create: `scripts/pipeline/validate_page_plan.py`
- Modify: `scripts/cli.py`
- Test: `tests/test_validate_page_plan.py`

**Step 1: Write failing tests**

Create tests for:

- Valid plan passes
- Duplicate `page_id` fails
- Duplicate `output_path` fails
- Missing `generation_order` page fails
- Absolute or parent-relative `output_path` fails
- Non-Markdown `output_path` fails

Expected return shape:

```python
{"ok": False, "errors": ["..."]}
```

**Step 2: Run tests**

Run: `pytest tests/test_validate_page_plan.py -v`

Expected: FAIL because module is missing.

**Step 3: Implement validator**

Create:

```python
def validate_page_plan(plan: dict) -> dict:
    errors = []
    pages = plan.get("pages", [])
    ids = [page.get("page_id") for page in pages]
    paths = [page.get("output_path") for page in pages]
    # missing field checks
    # duplicate checks
    # reject absolute paths
    # reject paths with ".."
    # require .md suffix
    # require generation_order to reference exactly known ids
    return {"ok": not errors, "errors": errors}
```

**Step 4: Add CLI command**

Add:

```bash
deepwiki validate-page-plan <project_path>
```

It reads `.deepwiki/cache/page-plan.json`.

**Step 5: Run tests**

Run: `pytest tests/test_validate_page_plan.py -v`

Expected: PASS.

**Step 6: Commit**

```bash
git add scripts/pipeline/validate_page_plan.py scripts/cli.py tests/test_validate_page_plan.py
git commit -m "feat: validate agentic page plans"
```

### Task 5: Implement Agentic Page Context Helper

**Files:**
- Create: `scripts/pipeline/page_context.py`
- Modify: `scripts/cli.py`
- Test: `tests/test_page_context.py`

**Step 1: Write failing tests**

Test that `build_page_context(project_path, page_id, save_to_cache=True)`:

- Reads `.deepwiki/cache/page-plan.json`
- Finds the requested page
- Reads files listed in `source_targets`
- Caps excerpts by `max_excerpt_chars`
- Writes `.deepwiki/cache/page-context/<safe_page_id>.json`
- Includes related pages from `depends_on` and reverse dependencies

**Step 2: Run tests**

Run: `pytest tests/test_page_context.py -v`

Expected: FAIL because helper is missing.

**Step 3: Implement helper**

Use:

```python
def build_page_context(project_path: Path, page_id: str, max_excerpt_chars: int = 12000, save_to_cache: bool = False) -> dict:
    ...
```

Do not parse AST. Read text with `errors="replace"` and skip files that cannot be read, recording them in `constraints` or `warnings`.

**Step 4: Add CLI command**

Add:

```bash
deepwiki page-context <project_path> <page_id>
```

It writes the context file and prints its path.

**Step 5: Run tests**

Run: `pytest tests/test_page_context.py -v`

Expected: PASS.

**Step 6: Commit**

```bash
git add scripts/pipeline/page_context.py scripts/cli.py tests/test_page_context.py
git commit -m "feat: build per-page agentic context"
```

### Task 6: Implement Menu Generation And Finalization

**Files:**
- Create: `scripts/wiki/generate_menu.py`
- Create: `scripts/wiki/finalize.py`
- Modify: `scripts/cli.py`
- Test: `tests/test_generate_menu.py`
- Test: `tests/test_finalize.py`

**Step 1: Write failing menu tests**

Test that `generate_menu(project_path, project_name)`:

- Reads `.deepwiki/cache/page-plan.json`
- Uses `menu_seed` when present
- Falls back to grouping by `page_type`
- Writes `.deepwiki/wiki/menu.json`
- Writes `.deepwiki/wiki/doc-map.md`

**Step 2: Write failing finalize tests**

Test that `finalize_wiki(project_path)`:

- Fails when a planned page is missing
- Passes when planned pages exist
- Reports broken local Markdown links

Keep Mermaid validation lightweight in this clean version: regex repair can be separate later unless needed for current tests.

**Step 3: Run tests**

Run: `pytest tests/test_generate_menu.py tests/test_finalize.py -v`

Expected: FAIL because modules are missing.

**Step 4: Implement menu generation**

Function:

```python
def generate_menu(project_path: Path, project_name: str | None = None, reconcile: bool = False) -> dict:
    ...
```

Use page plan first. Normalize paths relative to `.deepwiki/wiki`.

**Step 5: Implement finalize**

Function:

```python
def finalize_wiki(project_path: Path) -> int:
    ...
```

Checks:

- `page-plan.json` exists
- every non-skipped page file exists
- local Markdown links point to existing wiki files or source files
- `menu.json` can be regenerated

**Step 6: Add CLI commands**

Add:

```bash
deepwiki generate-menu <project_path>
deepwiki finalize <project_path>
```

**Step 7: Run tests**

Run: `pytest tests/test_generate_menu.py tests/test_finalize.py -v`

Expected: PASS.

**Step 8: Commit**

```bash
git add scripts/wiki scripts/cli.py tests/test_generate_menu.py tests/test_finalize.py
git commit -m "feat: add clean menu generation and finalize checks"
```

### Task 7: Add Preview Server

**Files:**
- Create: `scripts/serve/server.py`
- Modify: `scripts/cli.py`
- Test: `tests/test_serve_wiki.py`

**Step 1: Write failing server test**

Test that the server module can locate `.deepwiki/wiki`, bind to an available port, and return the selected URL without requiring old templates.

**Step 2: Run tests**

Run: `pytest tests/test_serve_wiki.py -v`

Expected: FAIL because server is missing.

**Step 3: Implement minimal static server**

Use stdlib `http.server.ThreadingHTTPServer` and serve files from `.deepwiki/wiki`.

Keep auto-increment port behavior:

```python
def find_available_port(host: str, start_port: int) -> int:
    ...
```

**Step 4: Add CLI command**

Add:

```bash
deepwiki serve <project_path> --host 127.0.0.1 --port 8742
```

**Step 5: Run tests**

Run: `pytest tests/test_serve_wiki.py -v`

Expected: PASS.

**Step 6: Commit**

```bash
git add scripts/serve scripts/cli.py tests/test_serve_wiki.py
git commit -m "feat: add clean wiki preview server"
```

### Task 8: Write New Skill And Workflow Docs

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Create: `references/system-reference.md`
- Create: `references/workflow/init-wiki.md`
- Create: `references/workflow/prepare-inventory.md`
- Create: `references/workflow/agentic-analysis.md`
- Create: `references/workflow/plan-pages.md`
- Create: `references/workflow/generate-menu.md`
- Create: `references/workflow/generate-pages.md`
- Create: `references/workflow/finalize-wiki.md`

**Step 1: Write `SKILL.md`**

The main workflow must be:

```text
init-wiki → prepare-inventory → agentic-analysis → plan-pages
→ generate-menu → generate-pages → finalize-wiki
```

State that:

- `prepare-inventory` is the only mandatory preparation script
- `agentic-analysis`, `plan-pages`, and `generate-pages` are Agent stages
- `legacy/old-pipeline/` is reference-only
- no stage should import or depend on legacy cache files
- page generation is split by page, not by old module-analysis units

**Step 2: Write workflow references**

Keep each reference concise and operational:

- command or Agent action
- inputs
- outputs
- failure behavior
- required cache files

**Step 3: Write `references/system-reference.md`**

Document:

- `.deepwiki/cache/project-inventory.json`
- `.deepwiki/cache/semantic-analysis.json`
- `.deepwiki/cache/page-plan.json`
- `.deepwiki/cache/page-context/<page_id>.json`
- `.deepwiki/state/progress.json`
- `.deepwiki/wiki/*`
- legacy archive policy

**Step 4: Write `README.md`**

Describe the clean agentic version. Do not advertise tree-sitter, AST parsing, old module analysis, or old quality gates as main-path behavior.

**Step 5: Commit**

```bash
git add SKILL.md README.md references
git commit -m "docs: document clean agentic workflow"
```

### Task 9: Add Package Validation And End-To-End Smoke Test

**Files:**
- Create: `scripts/quality/__init__.py`
- Create: `scripts/quality/validate_skill.py`
- Modify: `scripts/cli.py`
- Test: `tests/test_validate_skill.py`
- Test: `tests/test_integration.py`

**Step 1: Write failing validation tests**

Validate that required clean-root files exist:

- `SKILL.md`
- `README.md`
- `pyproject.toml`
- `scripts/cli.py`
- all four schemas
- all workflow references

Also assert no root workflow doc points to `legacy/old-pipeline` as an executable dependency.

**Step 2: Write failing integration test**

Smoke flow:

1. Create fixture project
2. Run `init_wiki`
3. Run `prepare_inventory`
4. Write fixture `semantic-analysis.json`
5. Write fixture `page-plan.json`
6. Run `validate_page_plan`
7. Write fixture Markdown pages
8. Run `generate_menu`
9. Run `finalize_wiki`

**Step 3: Run tests**

Run: `pytest tests/test_validate_skill.py tests/test_integration.py -v`

Expected: FAIL because validator/integration support is incomplete.

**Step 4: Implement package validator**

Expose:

```python
def validate_skill(skill_dir: Path) -> dict:
    ...
```

Return:

```python
{"ok": bool, "errors": list[str]}
```

Wire `deepwiki self-check` to this validator.

**Step 5: Run tests**

Run: `pytest tests/test_validate_skill.py tests/test_integration.py -v`

Expected: PASS.

**Step 6: Commit**

```bash
git add scripts/quality scripts/cli.py tests/test_validate_skill.py tests/test_integration.py
git commit -m "test: add clean workflow validation and smoke coverage"
```

### Task 10: Final Verification

**Files:**
- No code changes expected unless verification finds issues.

**Step 1: Confirm legacy archive exists**

Run: `test -d legacy/old-pipeline && test -f legacy/old-pipeline/SKILL.md`

Expected: exit 0.

**Step 2: Confirm clean root does not import legacy**

Run: `rg "legacy/old-pipeline|legacy\\.old_pipeline|old-pipeline" scripts schemas references SKILL.md README.md`

Expected: only documentation mentions are present; no Python import references.

**Step 3: Run self-check**

Run: `python -m scripts.cli self-check`

Expected: `DeepWiki skill self-check passed.`

**Step 4: Run tests**

Run: `pytest -q`

Expected: PASS.

**Step 5: Inspect git status**

Run: `git status --short`

Expected: clean after final commit.

**Step 6: Commit any verification fixes**

If fixes were needed:

```bash
git add <fixed-files>
git commit -m "fix: complete clean agentic migration"
```

**Step 7: Summarize completion**

Record:

- Legacy archive path
- New root commands
- New cache files
- Test results
