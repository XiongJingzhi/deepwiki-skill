"""Tests for scripts/extract_structure.py"""

import json
from pathlib import Path
import pytest
import extract_structure


# =====================================================================
# 1. detect_archetype
# =====================================================================

class TestDetectArchetype:
    def test_nextjs_project(self, tmp_path):
        (tmp_path / "next.config.js").write_text("module.exports = {};")
        (tmp_path / "package.json").write_text('{"dependencies":{"react":"^18"}}')
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "fullstack-framework"

    def test_spa_frontend(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies":{"react":"^18","react-dom":"^18"}}'
        )
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "App.tsx").write_text("export default function App() {}")
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "spa-frontend"

    def test_web_service_fastapi(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname="svc"\n[project.dependencies]\nfastapi="*"\n'
        )
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "web-service"

    def test_web_service_flask(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask>=2.0\n")
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "web-service"

    def test_cli_tool_nodejs(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies":{"commander":"^10"}}'
        )
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "cli-tool"

    def test_cli_tool_go(self, tmp_path):
        (tmp_path / "go.mod").write_text("module example.com/mycli\ngo 1.21\n")
        (tmp_path / "cmd").mkdir()
        (tmp_path / "cmd" / "root.go").write_text('package main\nfunc main(){}')
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "cli-tool"

    def test_sdk_library(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"my-lib","main":"index.js"}')
        lib = tmp_path / "lib"
        lib.mkdir()
        (lib / "index.ts").write_text("export const VERSION = '1.0.0';")
        # no pages/, no app/, no routes/
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "sdk-library"

    def test_ml_project(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("torch>=2.0\ntransformers\n")
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "ml-project"

    def test_rust_cli(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text(
            '[package]\nname="mycli"\n[[bin]]\nname="mycli"\npath="src/main.rs"\n'
        )
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "cli-tool"

    def test_fallback_generic(self, tmp_path):
        # No recognizable signals
        (tmp_path / "README.md").write_text("# My Project")
        result = extract_structure.detect_archetype(tmp_path)
        assert result == "generic"


# =====================================================================
# 2. extract_call_graph
# =====================================================================

class TestExtractCallGraph:
    def test_typescript_method_call(self, tmp_path):
        f = tmp_path / "service.ts"
        f.write_text(
            "class UserService {\n"
            "  async createUser(dto) {\n"
            "    const hash = await bcrypt.hash(dto.password, 10);\n"
            "    return this.userDao.insert(dto);\n"
            "  }\n"
            "}\n"
        )
        graph = extract_structure.extract_call_graph([f])
        # Should detect calls: bcrypt.hash, this.userDao.insert
        calls = graph.get("UserService.createUser", {}).get("calls", [])
        assert any("hash" in c for c in calls)
        assert any("insert" in c for c in calls)

    def test_python_function_calls(self, tmp_path):
        f = tmp_path / "service.py"
        f.write_text(
            "def create_user(dto):\n"
            "    hashed = bcrypt.hashpw(dto.password, bcrypt.gensalt())\n"
            "    return user_dao.insert(dto)\n"
        )
        graph = extract_structure.extract_call_graph([f])
        calls = graph.get("create_user", {}).get("calls", [])
        assert any("hashpw" in c or "insert" in c for c in calls)

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.ts"
        f.write_text("")
        graph = extract_structure.extract_call_graph([f])
        assert isinstance(graph, dict)

    def test_file_metadata_present(self, tmp_path):
        f = tmp_path / "main.py"
        f.write_text("def run():\n    helper()\n")
        graph = extract_structure.extract_call_graph([f])
        entry = graph.get("run", {})
        assert "file" in entry
        assert "calls" in entry


# =====================================================================
# 3. detect_patterns
# =====================================================================

class TestDetectPatterns:
    def test_express_middleware(self, tmp_path):
        f = tmp_path / "app.ts"
        f.write_text(
            "app.use(cors());\n"
            "app.use(express.json());\n"
            "app.get('/users', authMiddleware, userController.list);\n"
        )
        patterns = extract_structure.detect_patterns([f])
        types = [p["type"] for p in patterns]
        assert "middleware_chain" in types
        assert "http_route" in types

    def test_orm_usage(self, tmp_path):
        f = tmp_path / "dao.ts"
        f.write_text(
            "const users = await prisma.user.findMany();\n"
            "await prisma.user.create({ data: dto });\n"
        )
        patterns = extract_structure.detect_patterns([f])
        types = [p["type"] for p in patterns]
        assert "orm_usage" in types

    def test_react_component(self, tmp_path):
        f = tmp_path / "Button.tsx"
        f.write_text(
            "import React, { useState } from 'react';\n"
            "export function Button({ onClick }) {\n"
            "  const [active, setActive] = useState(false);\n"
            "  return <button onClick={onClick}>{active}</button>;\n"
            "}\n"
        )
        patterns = extract_structure.detect_patterns([f])
        types = [p["type"] for p in patterns]
        assert "react_component" in types
        assert "state_management" in types

    def test_no_patterns_plain_util(self, tmp_path):
        f = tmp_path / "utils.ts"
        f.write_text(
            "export function clamp(n: number, min: number, max: number) {\n"
            "  return Math.max(min, Math.min(max, n));\n"
            "}\n"
        )
        patterns = extract_structure.detect_patterns([f])
        # A pure util should produce no or minimal patterns
        assert isinstance(patterns, list)

    def test_pattern_includes_file_reference(self, tmp_path):
        f = tmp_path / "routes.ts"
        f.write_text("router.get('/health', (req, res) => res.json({ ok: true }));\n")
        patterns = extract_structure.detect_patterns([f])
        for p in patterns:
            assert "files" in p
            assert isinstance(p["files"], list)


# =====================================================================
# 4. build_key_sequences
# =====================================================================

class TestBuildKeySequences:
    def test_simple_chain(self):
        call_graph = {
            "Controller.create": {"calls": ["Service.create"], "file": "c.ts"},
            "Service.create": {"calls": ["Dao.insert"], "file": "s.ts"},
            "Dao.insert": {"calls": [], "file": "d.ts"},
        }
        entry_points = [{"name": "POST /users", "handler": "Controller.create"}]
        seqs = extract_structure.build_key_sequences(call_graph, entry_points)
        assert len(seqs) >= 1
        seq = seqs[0]
        assert "name" in seq
        assert "participants" in seq
        # Controller, Service, Dao should all appear
        participants_flat = " ".join(seq["participants"])
        assert "Controller" in participants_flat
        assert "Service" in participants_flat
        assert "Dao" in participants_flat

    def test_empty_graph(self):
        seqs = extract_structure.build_key_sequences({}, [])
        assert seqs == []

    def test_max_depth_respected(self):
        # Deep chain: A->B->C->D->E->F (depth 5)
        graph = {}
        prev = None
        for letter in "ABCDEF":
            func = f"func_{letter}"
            graph[func] = {"calls": [f"func_{chr(ord(letter)+1)}"] if letter != "F" else [], "file": "x.ts"}
        entry_points = [{"name": "start", "handler": "func_A"}]
        seqs = extract_structure.build_key_sequences(graph, entry_points, max_depth=3)
        if seqs:
            assert len(seqs[0]["participants"]) <= 4  # entry + max_depth


# =====================================================================
# 5. Integration: run_extract_structure (main entry)
# =====================================================================

class TestRunExtractStructure:
    def test_output_file_created(self, tmp_path):
        """End-to-end: script produces code-structure.json in .deepwiki/cache/."""
        # Minimal TS project
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("export const app = {};")
        (src / "service.ts").write_text(
            "class UserService { create() { return dao.insert(); } }"
        )
        (tmp_path / "package.json").write_text('{"dependencies":{"express":"^4"}}')
        (tmp_path / "app.ts").write_text(
            "app.use(auth);\napp.get('/users', controller.list);\n"
        )

        # Create .deepwiki/cache/structure.json (required input)
        deepwiki = tmp_path / ".deepwiki" / "cache"
        deepwiki.mkdir(parents=True)
        structure = {
            "entry_points": ["src/index.ts"],
            "core_files": [
                {"path": "src/index.ts", "importance_score": 0.9},
                {"path": "src/service.ts", "importance_score": 0.8},
                {"path": "app.ts", "importance_score": 0.7},
            ],
            "modules": [{"name": "src", "path": "src", "importance_score": 0.8}],
        }
        (deepwiki / "structure.json").write_text(json.dumps(structure))

        result = extract_structure.run_extract_structure(tmp_path)

        # Output file should be written
        out_file = tmp_path / ".deepwiki" / "cache" / "code-structure.json"
        assert out_file.exists()

        data = json.loads(out_file.read_text())
        assert "archetype" in data
        assert "call_graph" in data
        assert "patterns" in data
        assert "key_sequences" in data

    def test_missing_structure_json_raises(self, tmp_path):
        """Should raise FileNotFoundError if structure.json is missing."""
        with pytest.raises(FileNotFoundError):
            extract_structure.run_extract_structure(tmp_path)
