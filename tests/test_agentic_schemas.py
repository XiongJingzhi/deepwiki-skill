import json
from pathlib import Path

from jsonschema import validate


SCHEMA_DIR = Path("schemas")


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def test_project_inventory_schema_accepts_minimal_inventory():
    inventory = {
        "cache_schema_version": 1,
        "generated_at": "2026-05-08T00:00:00+00:00",
        "project_name": "sample",
        "root_path": "/tmp/sample",
        "languages": ["python"],
        "frameworks": [],
        "package_managers": ["pip"],
        "entry_candidates": [{"path": "src/app.py", "reason": "main-like filename"}],
        "important_configs": [{"path": "pyproject.toml", "kind": "python"}],
        "docs_found": ["README.md"],
        "ignore_rules": {
            "default_ignored_dirs": ["node_modules"],
            "default_ignored_files": [],
            "gitignore_used": False,
        },
        "tree_summary": {
            "max_depth": 2,
            "top_level_dirs": ["src"],
            "top_level_files": ["README.md"],
        },
        "stats": {
            "total_files": 2,
            "code_files": 1,
            "test_files": 0,
            "config_files": 1,
            "doc_files": 1,
            "generated_files": 0,
        },
        "files": [
            {
                "path": "src/app.py",
                "name": "app.py",
                "extension": ".py",
                "size": 12,
                "hash": "abc123",
                "category": "code",
                "language": "python",
                "is_test": False,
                "is_config": False,
                "is_doc": False,
                "is_generated": False,
            }
        ],
    }

    validate(instance=inventory, schema=load_schema("project-inventory-schema.json"))


def test_semantic_analysis_schema_accepts_minimal_analysis():
    analysis = {
        "cache_schema_version": 1,
        "generated_at": "2026-05-08T00:00:00+00:00",
        "project_purpose": "Generate project documentation.",
        "architecture_model": {
            "summary": "CLI-driven agentic documentation flow.",
            "details": {"style": "agentic"},
        },
        "runtime_flows": [
            {
                "name": "Generate wiki",
                "summary": "Prepare inventory, plan pages, write docs.",
                "evidence": [{"path": "SKILL.md", "reason": "workflow definition"}],
            }
        ],
        "concepts": [{"name": "Inventory", "summary": "Directory-level facts."}],
        "modules": [{"name": "CLI", "summary": "User command entrypoint.", "source_targets": ["scripts/cli.py"]}],
        "cross_cutting_concerns": [],
        "risks": [],
        "extension_points": [],
        "source_evidence": [{"path": "SKILL.md", "reason": "main instructions"}],
        "confidence": "high",
        "open_questions": [],
    }

    validate(instance=analysis, schema=load_schema("semantic-analysis-schema.json"))


def test_page_plan_schema_accepts_minimal_plan():
    plan = {
        "cache_schema_version": 1,
        "generated_at": "2026-05-08T00:00:00+00:00",
        "sections": [{"id": "overview", "title": "Overview", "page_ids": ["overview"]}],
        "pages": [
            {
                "page_id": "overview",
                "title": "Overview",
                "output_path": "overview.md",
                "page_type": "overview",
                "purpose": "Introduce the project.",
                "source_targets": ["README.md"],
                "depends_on": [],
                "status": "planned",
            }
        ],
        "generation_order": ["overview"],
        "menu_seed": [{"title": "Overview", "page_ids": ["overview"]}],
    }

    validate(instance=plan, schema=load_schema("page-plan-schema.json"))


def test_page_context_schema_accepts_minimal_context():
    context = {
        "page_id": "overview",
        "objective": "Introduce the project.",
        "source_files": [{"path": "README.md", "reason": "project introduction"}],
        "source_excerpts": [
            {
                "path": "README.md",
                "start_line": 1,
                "end_line": 3,
                "text": "# Sample\n\nIntro",
            }
        ],
        "related_pages": [],
        "claims_to_cover": ["Project purpose"],
        "must_link_symbols": [],
        "constraints": ["Do not invent APIs."],
    }

    validate(instance=context, schema=load_schema("page-context-schema.json"))
