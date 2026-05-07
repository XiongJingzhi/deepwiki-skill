"""Tests for prepare_module_context.py"""
import json
import pytest
from pathlib import Path
from scripts.pipeline.prepare_module_context import prepare_module_context


def _setup_cache(tmp_path, structure, code_structure):
    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "structure.json").write_text(json.dumps(structure), encoding="utf-8")
    (cache / "code-structure.json").write_text(json.dumps(code_structure), encoding="utf-8")
    return cache


def test_creates_context_per_module(tmp_path):
    """每个模块生成独立的 context.json"""
    structure = {
        "modules": {
            "src/auth": {"files": ["src/auth/login.py"], "importance_score": 0.8},
            "src/user": {"files": ["src/user/model.py"], "importance_score": 0.6},
        }
    }
    code_structure = {
        "import_relations": {
            "src/auth/login.py": {"imports": [{"module": "src/user/model.py", "line": 5}]},
            "src/user/model.py": {"imports": []}
        },
        "call_graph": {},
        "patterns": {}
    }
    _setup_cache(tmp_path, structure, code_structure)
    prepare_module_context(tmp_path)
    auth_ctx_path = tmp_path / ".deepwiki" / "cache" / "modules" / "src_auth" / "context.json"
    assert auth_ctx_path.exists()
    ctx = json.loads(auth_ctx_path.read_text())
    assert ctx["module_info"]["importance_score"] == 0.8
    assert "src/auth/login.py" in ctx["import_relations"]


def test_prefills_dependency_hints(tmp_path):
    """import_relations 自动聚合为 dependency_hints"""
    structure = {
        "modules": {
            "src/auth": {"files": ["src/auth/login.py"], "importance_score": 0.8},
            "src/user": {"files": ["src/user/model.py"], "importance_score": 0.6},
        }
    }
    code_structure = {
        "import_relations": {
            "src/auth/login.py": {"imports": [{"module": "src/user/model.py", "line": 5}]},
            "src/user/model.py": {"imports": []}
        },
        "call_graph": {}, "patterns": {}
    }
    _setup_cache(tmp_path, structure, code_structure)
    prepare_module_context(tmp_path)
    ctx_path = tmp_path / ".deepwiki" / "cache" / "modules" / "src_auth" / "context.json"
    ctx = json.loads(ctx_path.read_text())
    assert "src/user" in ctx["dependency_hints"]["imports"]


def test_idempotent_when_no_changes(tmp_path):
    """输入文件未变化时重跑不覆盖已有 context（mtime 不更新）"""
    structure = {"modules": {"src/auth": {"files": ["src/auth/login.py"], "importance_score": 0.7}}}
    code_structure = {"import_relations": {"src/auth/login.py": {"imports": []}}, "call_graph": {}, "patterns": {}}
    _setup_cache(tmp_path, structure, code_structure)
    prepare_module_context(tmp_path)
    ctx_path = tmp_path / ".deepwiki" / "cache" / "modules" / "src_auth" / "context.json"
    mtime1 = ctx_path.stat().st_mtime
    prepare_module_context(tmp_path)
    mtime2 = ctx_path.stat().st_mtime
    assert mtime1 == mtime2
