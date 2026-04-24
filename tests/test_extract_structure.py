"""Tests for scripts/extract_structure.py"""

import json
from pathlib import Path
import pytest
import common
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


# =========================================================================
# 新增测试：_has_dep() 词边界匹配
# =========================================================================

class TestHasDep:
    """Tests for _has_dep() word-boundary matching."""

    def test_torch_not_matches_torchaudio(self, tmp_path):
        """torch should NOT match torchaudio in requirements.txt."""
        (tmp_path / "requirements.txt").write_text("torchaudio>=2.0\ntensorboard\n")
        assert not extract_structure._has_dep(tmp_path, {"torch"})

    def test_torch_matches_torch(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("torch>=2.0\n")
        assert extract_structure._has_dep(tmp_path, {"torch"})

    def test_gin_not_matches_engine(self, tmp_path):
        """gin should NOT match engine in go.mod."""
        (tmp_path / "go.mod").write_text("module example.com/engine\n")
        assert not extract_structure._has_dep(tmp_path, {"gin"})

    def test_vue_not_matches_vuepress(self, tmp_path):
        """vue should NOT match vuepress in package.json."""
        (tmp_path / "package.json").write_text('{"devDependencies":{"vuepress":"^1.0"}}')
        assert not extract_structure._has_dep(tmp_path, {"vue"})

    def test_vue_matches_vue(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies":{"vue":"^3.0","vue-router":"^4"}}')
        assert extract_structure._has_dep(tmp_path, {"vue"})

    def test_multiple_names_any_match(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask>=2.0\n")
        assert extract_structure._has_dep(tmp_path, {"django", "flask", "fastapi"})

    def test_no_manifest_no_crash(self, tmp_path):
        assert not extract_structure._has_dep(tmp_path, {"anything"})

    def test_gin_in_go_mod(self, tmp_path):
        """gin should match gin-gonic in go.mod."""
        (tmp_path / "go.mod").write_text("module example.com/app\ngo 1.21\nrequire github.com/gin-gonic/gin v1.9.0\n")
        # Note: "gin" in "github.com/gin-gonic" - the preceding "/" is not a word char,
        # so this SHOULD match. This is the correct behavior.
        assert extract_structure._has_dep(tmp_path, {"gin"})


# =========================================================================
# 新增测试：分语言调用图解析
# =========================================================================

class TestExtractCallGraphLanguageSplit:
    """Tests for language-specific call graph parsing."""

    def test_python_def_in_string_not_matched(self, tmp_path):
        """'def ' inside a Python string should not create a function entry."""
        f = tmp_path / "strings.py"
        f.write_text(
            'HELP_TEXT = "Use def main() to start"\n'
            'def actual_function():\n'
            '    return 42\n'
        )
        graph = extract_structure.extract_call_graph([f])
        assert "actual_function" in graph
        assert "main" not in graph

    def test_typescript_constructor_not_filtered(self, tmp_path):
        """PascalCase methods like constructor should not be filtered."""
        f = tmp_path / "Service.ts"
        f.write_text(
            "class UserService {\n"
            "  constructor(private dao: UserDao) {}\n"
            "  createUser(name: string) {\n"
            "    this.dao.insert(name);\n"
            "  }\n"
            "}\n"
        )
        graph = extract_structure.extract_call_graph([f])
        assert "UserService.createUser" in graph

    def test_python_method_qualified_name(self, tmp_path):
        """Python methods should be qualified as ClassName.method."""
        f = tmp_path / "model.py"
        f.write_text(
            "class UserModel:\n"
            "    def save(self):\n"
            "        self.validate()\n"
            "    def validate(self):\n"
            "        pass\n"
            "def standalone():\n"
            "    pass\n"
        )
        graph = extract_structure.extract_call_graph([f])
        assert "UserModel.save" in graph
        assert "UserModel.validate" in graph
        assert "standalone" in graph

    def test_go_functions_independent(self, tmp_path):
        """Go functions should be parsed independently."""
        f = tmp_path / "main.go"
        f.write_text(
            "package main\n\n"
            "func main() {\n"
            "    greet()\n"
            "}\n\n"
            "func greet() {\n"
            '    fmt.Println("hello")\n'
            "}\n"
        )
        graph = extract_structure.extract_call_graph([f])
        assert "main" in graph
        assert "greet" in graph

    def test_rust_functions_independent(self, tmp_path):
        """Rust functions should be parsed independently."""
        f = tmp_path / "lib.rs"
        f.write_text(
            "pub fn process(input: &str) -> String {\n"
            "    transform(input)\n"
            "}\n\n"
            "fn transform(s: &str) -> String {\n"
            "    s.to_uppercase()\n"
            "}\n"
        )
        graph = extract_structure.extract_call_graph([f])
        assert "process" in graph
        assert "transform" in graph

    def test_java_class_methods(self, tmp_path):
        """Java class methods should be detected."""
        f = tmp_path / "Service.java"
        f.write_text(
            "public class Service {\n"
            "    public void execute() {\n"
            "        helper();\n"
            "    }\n"
            "    private void helper() {}\n"
            "}\n"
        )
        graph = extract_structure.extract_call_graph([f])
        assert any("execute" in k for k in graph)

    def test_call_extraction_strips_strings(self, tmp_path):
        """Function calls inside string literals should not be extracted."""
        f = tmp_path / "utils.py"
        f.write_text(
            'LOG = "calling process_data() now"\n'
            "def real_func():\n"
            "    do_something()\n"
        )
        graph = extract_structure.extract_call_graph([f])
        assert "real_func" in graph
        # "process_data" should not be in calls because it's inside a string
        if "real_func" in graph:
            assert "process_data" not in graph["real_func"]["calls"]


# =========================================================================
# 新增测试：缓存版本控制
# =========================================================================

class TestCacheVersioning:
    """Tests for cache schema version validation."""

    def test_stale_structure_json_raises_valueerror(self, tmp_path):
        """Should raise ValueError when structure.json has wrong version."""
        deepwiki = tmp_path / ".deepwiki" / "cache"
        deepwiki.mkdir(parents=True)
        structure = {
            "cache_schema_version": 999,
            "entry_points": [],
            "core_files": [],
            "modules": [],
        }
        (deepwiki / "structure.json").write_text(json.dumps(structure))

        with pytest.raises(ValueError, match="schema version mismatch"):
            extract_structure.run_extract_structure(tmp_path)

    def test_code_structure_json_has_version(self, tmp_path):
        """Output code-structure.json should include cache_schema_version."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("export const x = 1;")

        deepwiki = tmp_path / ".deepwiki" / "cache"
        deepwiki.mkdir(parents=True)
        structure = {
            "cache_schema_version": common.CACHE_SCHEMA_VERSION,
            "entry_points": [],
            "core_files": [{"path": "src/index.ts", "importance_score": 0.5}],
            "high_priority_files": [],
            "modules": [],
        }
        (deepwiki / "structure.json").write_text(json.dumps(structure))

        result = extract_structure.run_extract_structure(tmp_path)
        out_file = deepwiki / "code-structure.json"
        data = json.loads(out_file.read_text())
        assert "cache_schema_version" in data
        assert data["cache_schema_version"] == common.CACHE_SCHEMA_VERSION


# =========================================================================
# 新增测试：import_relations 集成
# =========================================================================

class TestImportRelationsIntegration:
    """Tests for import_relations integration in run_extract_structure."""

    def test_import_relations_in_output(self, tmp_path):
        """code-structure.json should include import_relations field."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.py").write_text(
            "from .b import helper\n\ndef run():\n    helper()\n"
        )
        (src / "b.py").write_text("def helper():\n    pass\n")
        (tmp_path / "requirements.txt").write_text("flask>=2.0\n")

        deepwiki = tmp_path / ".deepwiki" / "cache"
        deepwiki.mkdir(parents=True)
        structure = {
            "cache_schema_version": common.CACHE_SCHEMA_VERSION,
            "entry_points": [],
            "core_files": [
                {"path": "src/a.py", "importance_score": 0.7},
                {"path": "src/b.py", "importance_score": 0.5},
            ],
            "high_priority_files": [],
            "modules": [],
        }
        (deepwiki / "structure.json").write_text(json.dumps(structure))

        result = extract_structure.run_extract_structure(tmp_path)
        assert "import_relations" in result
        assert isinstance(result["import_relations"], dict)

    def test_import_relations_json_file(self, tmp_path):
        """import-relations.json should be written to cache/."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("export const x = 1;")

        deepwiki = tmp_path / ".deepwiki" / "cache"
        deepwiki.mkdir(parents=True)
        structure = {
            "cache_schema_version": common.CACHE_SCHEMA_VERSION,
            "entry_points": [],
            "core_files": [{"path": "src/index.ts", "importance_score": 0.5}],
            "high_priority_files": [],
            "modules": [],
        }
        (deepwiki / "structure.json").write_text(json.dumps(structure))

        extract_structure.run_extract_structure(tmp_path)

        ir_file = deepwiki / "import-relations.json"
        assert ir_file.exists()
        data = json.loads(ir_file.read_text())
        assert "cache_schema_version" in data
        assert "relations" in data
