"""Tests for generate_skeleton.py"""
import json
import pytest
from pathlib import Path
from scripts.pipeline.generate_skeleton import generate_skeleton_structure


def _make_cache(tmp_path, structure, code_structure):
    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "structure.json").write_text(json.dumps(structure), encoding="utf-8")
    (cache / "code-structure.json").write_text(json.dumps(code_structure), encoding="utf-8")


def test_generates_module_groups(tmp_path):
    """从 import_relations 生成 module_groups"""
    structure = {
        "modules": {
            "src/auth": {"files": ["src/auth/login.py"]},
            "src/user": {"files": ["src/user/model.py"]},
            "src/order": {"files": ["src/order/service.py"]},
        }
    }
    code_structure = {
        "import_relations": {
            "src/auth/login.py": {"imports": [{"module": "src/user/model.py", "line": 1}]},
            "src/user/model.py": {"imports": []},
            "src/order/service.py": {"imports": [{"module": "src/user/model.py", "line": 2}]},
        },
        "archetype": "web-service"
    }
    _make_cache(tmp_path, structure, code_structure)
    result = generate_skeleton_structure(tmp_path)
    assert "module_groups" in result
    assert len(result["module_groups"]) > 0
    groups = result["module_groups"]
    auth_group = next((g for g in groups if "src/auth" in g["modules"]), None)
    assert auth_group is not None


def test_generates_architecture_layers(tmp_path):
    """从 code_purpose 推断分层"""
    structure = {
        "modules": {
            "src/api": {"files": ["src/api/routes.py"]},
            "src/service": {"files": ["src/service/logic.py"]},
            "src/db": {"files": ["src/db/session.py"]},
        }
    }
    code_structure = {"import_relations": {}, "archetype": "web-service"}
    _make_cache(tmp_path, structure, code_structure)
    result = generate_skeleton_structure(tmp_path)
    assert "architecture_layers" in result
    assert len(result["architecture_layers"]) > 0


def test_placeholders_for_ai_fields(tmp_path):
    """project_nature 和 key_data_flows 保留为空占位符"""
    structure = {"modules": {"src/core": {"files": ["src/core/main.py"]}}}
    code_structure = {"import_relations": {}, "archetype": "cli-tool"}
    _make_cache(tmp_path, structure, code_structure)
    result = generate_skeleton_structure(tmp_path)
    assert result["project_nature"] == ""
    assert result["key_data_flows"] == []

def test_build_skeleton_input_summary_excludes_call_graph(tmp_path):
    """_build_skeleton_input_summary 产出不含函数级 call_graph"""
    import json
    from scripts.pipeline.generate_skeleton import _build_skeleton_input_summary

    structure = {
        "project_name": "demo",
        "modules": {"auth": {"files": ["src/auth/service.py"]}},
        "tech_stack": {"language": "python"},
    }
    code_structure = {
        "archetype": "web-service",
        "import_relations": {},
        "call_graph": {
            "src/auth/service.py": {"calls": ["foo", "bar"]}
        },
    }

    summary = _build_skeleton_input_summary(structure, code_structure)

    assert "call_graph" not in summary
    assert "call_graph" not in json.dumps(summary)
    assert summary["archetype"] == "web-service"
    assert any(m["name"] == "auth" for m in summary["modules"])


def test_generate_skeleton_structure_includes_summary(tmp_path):
    """generate_skeleton_structure 返回值应包含 _input_summary"""
    import json
    from scripts.wiki.init_wiki import init_deep_wiki
    from scripts.analysis.analyze_project import analyze_project
    from scripts.analysis.extract_structure import run_extract_structure
    from scripts.pipeline.generate_skeleton import generate_skeleton_structure

    init_deep_wiki(str(tmp_path))
    analyze_project(str(tmp_path), save_to_cache=True)
    run_extract_structure(tmp_path)

    result = generate_skeleton_structure(tmp_path)

    assert "_input_summary" in result
    summary = result["_input_summary"]
    assert "archetype" in summary
    assert "modules" in summary
    assert "call_graph" not in summary
