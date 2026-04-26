"""Tests for scripts/plan_doc_topology.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import CACHE_SCHEMA_VERSION, cache_path
from analyze_project import analyze_project
from extract_structure import run_extract_structure
from init_wiki import init_deep_wiki
from plan_doc_topology import plan_doc_topology


class TestPlanDocTopology:
    def test_plan_doc_topology_generates_outputs(self, fake_python_project):
        init_deep_wiki(str(fake_python_project))
        analyze_project(str(fake_python_project), save_to_cache=True)
        run_extract_structure(fake_python_project)

        result = plan_doc_topology(fake_python_project)

        assert "doc_topology" in result
        assert "generation_plan" in result
        assert result["doc_topology"]["pages"]
        assert result["generation_plan"]["pages"]

        topology_path = cache_path(fake_python_project, "doc-topology.json")
        plan_path = cache_path(fake_python_project, "generation-plan.json")
        assert topology_path.exists()
        assert plan_path.exists()

        topology = json.loads(topology_path.read_text(encoding="utf-8"))
        generation_plan = json.loads(plan_path.read_text(encoding="utf-8"))
        assert any(page["id"] == "overview" for page in topology["pages"])
        page_titles = {page["id"]: page["title"] for page in topology["pages"]}
        assert page_titles["overview"] == "项目概览"
        assert page_titles["getting-started"] == "快速开始"
        assert page_titles["doc-map"] == "文档地图"
        assert any(page["page_id"] == "overview" for page in generation_plan["pages"])

    def test_module_pages_use_deep_dive_group_and_directory(self, fake_python_project):
        init_deep_wiki(str(fake_python_project))
        analyze_project(str(fake_python_project), save_to_cache=True)
        run_extract_structure(fake_python_project)

        result = plan_doc_topology(fake_python_project)
        topology = result["doc_topology"]

        module_pages = [
            page
            for page in topology["pages"]
            if page["type"] in {"capability", "internal"}
        ]
        assert module_pages
        assert all(page["output_path"].startswith("wiki/deep-dive/") for page in module_pages)
        assert "deep-dive" in topology["groupings"]
        assert "capabilities" not in topology["groupings"]
        assert "internals" not in topology["groupings"]

    def test_module_pages_include_relevant_source_file_manifest(self, tmp_path):
        init_deep_wiki(str(tmp_path))
        cache = tmp_path / ".deepwiki" / "cache"
        (cache / "structure.json").write_text(
            json.dumps(
                {
                    "cache_schema_version": CACHE_SCHEMA_VERSION,
                    "project_name": "demo",
                    "modules": [{"name": "auth", "path": "src/auth"}],
                }
            ),
            encoding="utf-8",
        )
        (cache / "module-analysis.json").write_text(
            json.dumps(
                {
                    "cache_schema_version": CACHE_SCHEMA_VERSION,
                    "modules": {
                        "auth": {
                            "module_path": "src/auth",
                            "semantic_group": "认证",
                            "code_purpose": "Service",
                            "files": [
                                {
                                    "path": "src/auth/service.py",
                                    "summary": "认证主流程。",
                                    "public_interfaces": [
                                        {"name": "login", "line": 10, "end_line": 24}
                                    ],
                                    "core_source_ranges": [
                                        {
                                            "label": "login flow",
                                            "start_line": 10,
                                            "end_line": 24,
                                            "reason": "登录主路径。",
                                        }
                                    ],
                                }
                            ],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        result = plan_doc_topology(tmp_path)
        page = next(
            page
            for page in result["doc_topology"]["pages"]
            if page["id"] == "deep-dive:auth"
        )
        assert page["source_files"] == [
            {
                "path": "src/auth/service.py",
                "summary": "认证主流程。",
                "ranges": [
                    {
                        "start_line": 10,
                        "end_line": 24,
                        "label": "login flow",
                        "reason": "登录主路径。",
                    },
                    {
                        "start_line": 10,
                        "end_line": 24,
                        "label": "login",
                        "reason": "public interface",
                    },
                ],
            }
        ]

        planned = next(
            page
            for page in result["generation_plan"]["pages"]
            if page["page_id"] == "deep-dive:auth"
        )
        assert planned["source_files"] == page["source_files"]

    def test_module_pages_fall_back_to_structure_core_files(self, tmp_path):
        init_deep_wiki(str(tmp_path))
        cache = tmp_path / ".deepwiki" / "cache"
        (cache / "structure.json").write_text(
            json.dumps(
                {
                    "cache_schema_version": CACHE_SCHEMA_VERSION,
                    "project_name": "demo",
                    "modules": [
                        {
                            "name": "auth",
                            "path": "src/auth",
                            "core_files": ["src/auth/service.py"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (cache / "module-analysis.json").write_text(
            json.dumps({"cache_schema_version": CACHE_SCHEMA_VERSION, "modules": {}}),
            encoding="utf-8",
        )

        result = plan_doc_topology(tmp_path)
        page = next(
            page
            for page in result["doc_topology"]["pages"]
            if page["id"] == "deep-dive:auth"
        )
        assert page["source_files"] == [
            {"path": "src/auth/service.py", "summary": "", "ranges": []}
        ]
