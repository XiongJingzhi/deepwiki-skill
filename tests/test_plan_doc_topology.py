"""Tests for scripts/plan_doc_topology.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import cache_path
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
        assert any(page["page_id"] == "overview" for page in generation_plan["pages"])
