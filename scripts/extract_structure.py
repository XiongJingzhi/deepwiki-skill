#!/usr/bin/env python3
"""
代码结构提取脚本 v1.0
基于正则+启发式，从源码中提取调用图、代码模式和近似时序。
输出 .deepwiki/cache/code-structure.json，供 AI 深度阅读阶段使用。
"""

from collections import deque
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from common import CODE_EXTENSIONS, CACHE_SCHEMA_VERSION
from import_relations import extract_import_relations


# ══════════════════════════════════════════════════════════════════════
# 公共入口
# ══════════════════════════════════════════════════════════════════════

def run_extract_structure(project_path: Path) -> Dict[str, Any]:
    """主入口：读取 structure.json，运行所有分析，写出 code-structure.json。"""
    structure_path = project_path / ".deepwiki" / "cache" / "structure.json"
    if not structure_path.exists():
        raise FileNotFoundError(f"structure.json not found: {structure_path}")

    with open(structure_path, encoding="utf-8") as f:
        structure = json.load(f)

    # 校验 structure.json 的 schema 版本
    if structure.get("cache_schema_version") is not None:
        if structure["cache_schema_version"] != CACHE_SCHEMA_VERSION:
            raise ValueError(
                f"structure.json schema version mismatch: "
                f"expected {CACHE_SCHEMA_VERSION}, got {structure['cache_schema_version']}. "
                f"Re-run analyze_project.py to regenerate."
            )

    # 收集待分析文件：core_files + high_priority_files（去重）
    seen_paths = set()
    all_files: List[Path] = []
    for cf in structure.get("core_files", []) + structure.get("high_priority_files", []):
        p = project_path / cf["path"]
        if p.exists() and str(p) not in seen_paths:
            seen_paths.add(str(p))
            all_files.append(p)

    archetype = detect_archetype(project_path)
    call_graph = extract_call_graph(all_files)
    patterns = detect_patterns(all_files)

    # Import 关系（可信基线，供 Step 5 交叉验证）
    import_relations = extract_import_relations(all_files, project_path)

    # 构建入口点
    entry_points = _build_entry_points(structure, call_graph)
    key_sequences = build_key_sequences(call_graph, entry_points)

    result = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "archetype": archetype,
        "call_graph": call_graph,
        "patterns": patterns,
        "key_sequences": key_sequences,
        "entry_points": entry_points,
        "import_relations": import_relations,
    }

    out_path = project_path / ".deepwiki" / "cache" / "code-structure.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 独立输出 import-relations.json
    ir_path = project_path / ".deepwiki" / "cache" / "import-relations.json"
    ir_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ir_path, "w", encoding="utf-8") as f:
        json.dump({
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "relations": import_relations,
        }, f, ensure_ascii=False, indent=2)

    return result


def _build_entry_points(structure: dict, call_graph: dict) -> List[Dict[str, str]]:
    """从 structure.json 的 entry_points 字段构建入口点列表。"""
    eps = []
    for ep_path in structure.get("entry_points", []):
        stem = Path(ep_path).stem
        # 找 call_graph 中匹配的函数名（main/run/start 等）
        candidates = [k for k in call_graph if k.lower() in ("main", "run", "start", "app", "server")]
        handler = candidates[0] if candidates else stem
        eps.append({"name": ep_path, "handler": handler})
    return eps


# ══════════════════════════════════════════════════════════════════════
# 1. 项目原型检测
# ══════════════════════════════════════════════════════════════════════

def detect_archetype(project_path: Path) -> str:
    """检测项目原型，返回原型标签字符串。"""
    rules = [
        ("fullstack-framework", lambda p: any(
            (p / f).exists() for f in [
                "next.config.js", "next.config.mjs", "next.config.ts",
                "nuxt.config.ts", "nuxt.config.js", "remix.config.js",
            ]
        )),
        ("agent-project", lambda p: (
            _has_dep(p, {"langchain", "llamaindex", "crewai", "autogen", "semantic-kernel"})
            or (p / "agents").is_dir()
        )),
        ("ml-project", lambda p: _has_dep(p, {
            "torch", "tensorflow", "keras", "scikit-learn", "sklearn",
            "transformers", "pytorch", "jax", "paddle",
        })),
        ("data-pipeline", lambda p: (
            _has_dep(p, {"airflow", "prefect", "dagster", "luigi", "pyspark",
                         "apache-beam", "kafka", "pulsar"})
            or (p / "dags").is_dir()
        )),
        ("microservice", lambda p: _has_dep(p, {
            "spring-boot", "spring-cloud", "micronaut", "quarkus",
            "dapr", "temporal", "grpc", "protobuf", "nestjs",
        })),
        ("serverless", lambda p: (
            (p / "serverless.yml").exists() or (p / "serverless.yaml").exists()
            or (p / "samconfig.toml").exists() or (p / "template.yaml").exists()
            or _has_dep(p, {"@aws-lambda/core", "azure-functions", "vercel"})
        )),
        ("cli-tool", lambda p: (
            _has_dep(p, {"commander", "yargs", "inquirer", "oclif", "clipanion",
                         "clap", "cobra", "click", "typer", "argparse-rs"})
            or (p / "cmd").is_dir()
            or _cargo_has_bin(p)
        )),
        ("web-service", lambda p: _has_dep(p, {
            "fastapi", "flask", "django", "express", "koa", "fastify", "hono",
            "gin", "fiber", "axum", "actix-web", "spring", "rails",
        })),
        ("desktop-app", lambda p: (
            _has_dep(p, {"electron", "tauri", "wry", "flutter", "slint",
                         "pyqt", "pyside", "tkinter", "kivy"})
        )),
        ("mobile-app", lambda p: (
            _has_dep(p, {"react-native", "expo", "capacitor", "ionic",
                         "swiftui", "jetpack-compose"})
            or (p / "android").is_dir() or (p / "ios").is_dir()
        )),
        ("spa-frontend", lambda p: (
            _has_dep(p, {"react", "vue", "svelte", "angular", "solid-js"})
            and not (p / "pages" / "api").is_dir()
            and not (p / "app" / "api").is_dir()
            and not (p / "server").is_dir()
        )),
        ("sdk-library", lambda p: (
            ((p / "lib").is_dir() or (p / "src").is_dir())
            and not _has_dep(p, {"react", "vue", "express", "fastapi", "flask"})
            and _has_manifest(p)
            and not (p / "pages").is_dir()
            and not (p / "app").is_dir()
        )),
    ]
    for archetype, test in rules:
        try:
            if test(project_path):
                return archetype
        except Exception:
            continue
    return "generic"


# ══════════════════════════════════════════════════════════════════════
# 2. 调用图提取
# ══════════════════════════════════════════════════════════════════════

_CLASS_DECL = re.compile(r"^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)", re.MULTILINE)
_TS_METHOD  = re.compile(r"^[ \t]{1,}(?:(?:async|static|public|private|protected|override)\s+)*(\w+)\s*\(", re.MULTILINE)
_GO_FN      = re.compile(r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(", re.MULTILINE)
_RUST_FN    = re.compile(r"^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*[\(<]", re.MULTILINE)
_CALL_OBJ   = re.compile(r"\b(\w+)\.(\w+)\s*\(")
_CALL_FN    = re.compile(r"\b([A-Za-z_]\w{2,})\s*\(")

_SKIP = frozenset({
    "if", "for", "while", "switch", "catch", "return", "await", "new",
    "typeof", "instanceof", "console", "print", "len", "str", "int",
    "float", "bool", "list", "dict", "set", "super", "self", "this",
    "True", "False", "None", "require", "import", "export", "const",
    "let", "var", "async", "function", "class", "extends", "implements",
    "type", "interface", "enum", "namespace", "module", "from",
})

# 语言分发表：文件扩展名 -> 解析函数
_PARSERS = {}


def _register_parser(*exts):
    """装饰器：将函数注册为指定扩展名的解析器。"""
    def decorator(fn):
        for ext in exts:
            _PARSERS[ext] = fn
        return fn
    return decorator


# ── 字符串/注释移除工具 ──

_PY_DOCSTRING = re.compile(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', re.MULTILINE)
_PY_STRING = re.compile(
    r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|f"[^"]*"|f\'[^\']*\'|"[^"]*"|\'[^\']*\')'
)

_TS_STRING = re.compile(
    r'(`[^`]*`|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')'
)


def _extract_calls_from_body(body: str, func_name: str) -> List[str]:
    """从函数体中提取调用，先移除字符串字面量避免误匹配。"""
    clean = _TS_STRING.sub('""', body)

    calls: List[str] = []
    seen: set = set()

    for m in re.finditer(r'\b(\w+)\.(\w+)\s*\(', clean):
        obj, meth = m.group(1), m.group(2)
        if obj not in _SKIP and meth not in _SKIP:
            c = f"{obj}.{meth}"
            if c not in seen and c != func_name:
                seen.add(c)
                calls.append(c)

    for m in re.finditer(r'\b([A-Za-z_]\w{2,})\s*\(', clean):
        name = m.group(1)
        if name not in _SKIP and name not in seen and name != func_name:
            seen.add(name)
            calls.append(name)

    return calls[:20]


# ── Python 解析器 ──

_PY_DEF = re.compile(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(', re.MULTILINE)
_PY_CLASS = re.compile(r'^class\s+(\w+)', re.MULTILINE)


@_register_parser('.py', '.pyi')
def _parse_python_file(text: str, fpath: str) -> List[tuple]:
    """解析 Python 文件，正确处理字符串中的 def 和缩进 class 范围。"""
    lines_list = text.splitlines()

    # 构建 class 范围：基于缩进判断 class 结束位置
    class_ranges: List[list] = []
    for m in _PY_CLASS.finditer(text):
        cname = m.group(1)
        start_ln = text[:m.start()].count("\n")
        class_ranges.append([cname, start_ln, len(lines_list)])

    # 用缩进判断 class 结束
    for i in range(len(class_ranges)):
        cname, start, _end = class_ranges[i]
        next_start = class_ranges[i + 1][1] if i + 1 < len(class_ranges) else len(lines_list)
        actual_end = start + 1
        for ln_idx in range(start + 1, next_start):
            line = lines_list[ln_idx] if ln_idx < len(lines_list) else ""
            if line and not line[0].isspace() and line.strip():
                actual_end = ln_idx
                break
        class_ranges[i][2] = max(actual_end, start + 2)

    def get_class_at(ln: int) -> Optional[str]:
        for cname, s, e in class_ranges:
            if s <= ln < e:
                return cname
        return None

    # 移除 docstring 后扫描 def（避免字符串中 "def " 误匹配）
    clean = _PY_DOCSTRING.sub('""', text)

    defined: List[tuple] = []
    for m in _PY_DEF.finditer(clean):
        name = m.group(1)
        ln = clean[:m.start()].count("\n")
        cls = get_class_at(ln)
        qn = f"{cls}.{name}" if cls else name
        defined.append((qn, ln + 1))

    # 去重
    seen_n: set = set()
    unique: List[tuple] = []
    for qn, ln in sorted(defined, key=lambda x: x[1]):
        if qn not in seen_n:
            seen_n.add(qn)
            unique.append((qn, ln))

    # 提取函数体（从原始文本获取，不是 clean）
    result = []
    for i, (func_name, line_no) in enumerate(unique):
        s = line_no - 1
        e = unique[i + 1][1] - 1 if i + 1 < len(unique) else len(lines_list)
        body = "\n".join(lines_list[s:e])
        result.append((func_name, line_no, body))

    return result


# ── TypeScript/JavaScript 解析器 ──

_TS_CLASS = re.compile(r'^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', re.MULTILINE)
_TS_METHOD = re.compile(
    r'^[ \t]+(?:(?:async|static|public|private|protected|override|readonly|get|set|abstract)\s+)*(\w+)\s*[<\(]',
    re.MULTILINE,
)
_TS_TOPLEVEL_FN = re.compile(r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(', re.MULTILINE)
_TS_ARROW_EXPORT = re.compile(r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\(', re.MULTILINE)


@_register_parser('.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs')
def _parse_ts_file(text: str, fpath: str) -> List[tuple]:
    """解析 TS/JS 文件，不过滤 PascalCase 方法名（保留构造函数等）。"""
    lines_list = text.splitlines()

    # 构建 class 范围
    class_ranges: List[list] = []
    for m in _TS_CLASS.finditer(text):
        cname = m.group(1)
        start_ln = text[:m.start()].count("\n")
        class_ranges.append([cname, start_ln, len(lines_list)])
    for i in range(len(class_ranges) - 1):
        class_ranges[i][2] = class_ranges[i + 1][1]

    def get_class_at(ln: int) -> Optional[str]:
        for cname, s, e in class_ranges:
            if s <= ln < e:
                return cname
        return None

    defined: List[tuple] = []

    # 顶层函数
    for m in _TS_TOPLEVEL_FN.finditer(text):
        ln = text[:m.start()].count("\n")
        defined.append((m.group(1), ln + 1))

    # 箭头函数导出
    for m in _TS_ARROW_EXPORT.finditer(text):
        name = m.group(1)
        if name not in _SKIP:
            ln = text[:m.start()].count("\n")
            defined.append((name, ln + 1))

    # 类方法（不过滤 PascalCase）
    for m in _TS_METHOD.finditer(text):
        name = m.group(1)
        if name in _SKIP:
            continue
        ln = text[:m.start()].count("\n")
        cls = get_class_at(ln)
        if cls:
            defined.append((f"{cls}.{name}", ln + 1))

    # 去重
    seen_n: set = set()
    unique: List[tuple] = []
    for qn, ln in sorted(defined, key=lambda x: x[1]):
        if qn not in seen_n:
            seen_n.add(qn)
            unique.append((qn, ln))

    # 提取函数体
    result = []
    for i, (func_name, line_no) in enumerate(unique):
        s = line_no - 1
        e = unique[i + 1][1] - 1 if i + 1 < len(unique) else len(lines_list)
        body = "\n".join(lines_list[s:e])
        result.append((func_name, line_no, body))

    return result


# ── Go 解析器 ──

_GO_FN = re.compile(r'^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(', re.MULTILINE)


_GO_METHOD = re.compile(
    r'^func\s+\((\w+)\s+\*?\w+\)\s+(\w+)\s*\(', re.MULTILINE
)


@_register_parser('.go')
def _parse_go_file(text: str, fpath: str) -> List[tuple]:
    """解析 Go 文件，支持方法 receiver 限定名。"""
    lines_list = text.splitlines()

    defined: List[tuple] = []
    # 匹配带 receiver 的方法：func (t *Type) Method(...)
    for m in _GO_METHOD.finditer(text):
        receiver = m.group(1)
        name = m.group(2)
        ln = text[:m.start()].count("\n")
        defined.append((f"{receiver}.{name}", ln + 1))
    # 匹配普通函数：func Name(...)
    for m in _GO_FN.finditer(text):
        name = m.group(1)
        ln = text[:m.start()].count("\n")
        # 跳过已被 _GO_METHOD 匹配的行（通过检查行号去重）
        if not any(d[1] == ln + 1 for d in defined):
            defined.append((name, ln + 1))

    result = []
    for i, (func_name, line_no) in enumerate(defined):
        s = line_no - 1
        e = defined[i + 1][1] - 1 if i + 1 < len(defined) else len(lines_list)
        body = "\n".join(lines_list[s:e])
        result.append((func_name, line_no, body))

    return result


# ── Rust 解析器 ──

_RUST_FN = re.compile(r'^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*[\(<]', re.MULTILINE)


_RUST_IMPL = re.compile(r'^impl\s+(\w+)', re.MULTILINE)


@_register_parser('.rs')
def _parse_rust_file(text: str, fpath: str) -> List[tuple]:
    """解析 Rust 文件，追踪 impl 块为函数生成限定名。"""
    lines_list = text.splitlines()

    # 收集 impl 块范围
    impl_ranges: List[tuple] = []  # [(impl_name, start_line), ...]
    for m in _RUST_IMPL.finditer(text):
        impl_name = m.group(1)
        start_ln = text[:m.start()].count("\n")
        impl_ranges.append((impl_name, start_ln))

    defined: List[tuple] = []
    for m in _RUST_FN.finditer(text):
        name = m.group(1)
        ln = text[:m.start()].count("\n")
        # 查找最近的 impl 块
        current_impl = None
        for iname, start in impl_ranges:
            if start <= ln:
                current_impl = iname
        if current_impl:
            defined.append((f"{current_impl}.{name}", ln + 1))
        else:
            defined.append((name, ln + 1))

    result = []
    for i, (func_name, line_no) in enumerate(defined):
        s = line_no - 1
        e = defined[i + 1][1] - 1 if i + 1 < len(defined) else len(lines_list)
        body = "\n".join(lines_list[s:e])
        result.append((func_name, line_no, body))

    return result


# ── Java/Kotlin 解析器 ──

_JAVA_CLASS = re.compile(r'^(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|static\s+|final\s+)*class\s+(\w+)', re.MULTILINE)
_JAVA_METHOD = re.compile(
    r'^[ \t]+(?:(?:public|protected|private|static|final|abstract|synchronized|native)\s+)*(?:[\w<>\[\],\s]+\s+)?(\w+)\s*\(',
    re.MULTILINE,
)


@_register_parser('.java', '.kt')
def _parse_java_file(text: str, fpath: str) -> List[tuple]:
    """解析 Java/Kotlin 文件。"""
    lines_list = text.splitlines()

    # 构建 class 范围
    class_ranges: List[list] = []
    for m in _JAVA_CLASS.finditer(text):
        cname = m.group(1)
        start_ln = text[:m.start()].count("\n")
        class_ranges.append([cname, start_ln, len(lines_list)])
    for i in range(len(class_ranges) - 1):
        class_ranges[i][2] = class_ranges[i + 1][1]

    def get_class_at(ln: int) -> Optional[str]:
        for cname, s, e in class_ranges:
            if s <= ln < e:
                return cname
        return None

    defined: List[tuple] = []
    seen_names: set = set()

    # 类方法（缩进检测）
    for m in _JAVA_METHOD.finditer(text):
        name = m.group(1)
        if name in _SKIP or name in ('class', 'interface', 'enum', 'void', 'if', 'for', 'while', 'try', 'switch', 'return'):
            continue
        ln = text[:m.start()].count("\n")
        cls = get_class_at(ln)
        if cls:
            qn = f"{cls}.{name}"
            if qn not in seen_names:
                seen_names.add(qn)
                defined.append((qn, ln + 1))

    # 去重
    unique: List[tuple] = sorted(defined, key=lambda x: x[1])

    result = []
    for i, (func_name, line_no) in enumerate(unique):
        s = line_no - 1
        e = unique[i + 1][1] - 1 if i + 1 < len(unique) else len(lines_list)
        body = "\n".join(lines_list[s:e])
        result.append((func_name, line_no, body))

    return result


# ── 主入口 ──

def extract_call_graph(files: List[Path]) -> Dict[str, Any]:
    """从源文件列表中提取调用图，按语言分发到独立解析器。"""
    graph: Dict[str, Any] = {}

    for fpath in files:
        if not fpath.exists():
            continue
        ext = fpath.suffix.lower()
        parser = _PARSERS.get(ext)
        if not parser:
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        try:
            file_defs = parser(text, str(fpath))
        except Exception:
            continue

        for func_name, line_no, body in file_defs:
            calls = _extract_calls_from_body(body, func_name)
            graph[func_name] = {
                "calls": calls,
                "file": str(fpath),
                "line": line_no,
            }

    return graph


# ══════════════════════════════════════════════════════════════════════
# 3. 代码模式检测
# ══════════════════════════════════════════════════════════════════════

_PATTERN_RULES = [
    ("middleware_chain", re.compile(r"\bapp\.use\s*\(|router\.use\s*\(|@app\.middleware|koa\.use\s*\(")),
    ("http_route",       re.compile(r"\b(?:app|router)\s*\.\s*(?:get|post|put|delete|patch)\s*\(")),
    ("orm_usage",        re.compile(r"\bprisma\.\w+\.|\b(?:repository|dao)\s*\.\s*(?:find|save|insert|create|update|delete)\s*\(|\borm\.\w+\s*\(")),
    ("react_component",  re.compile(r"export\s+(?:default\s+)?(?:function|class)\s+\w+|=>\s*<\w+|React\.createElement")),
    ("state_management", re.compile(r"\buseState\s*\(|\buseReducer\s*\(|createSlice\s*\(|createStore\s*\(|\breactive\s*\(|\bref\s*\(")),
    ("event_system",     re.compile(r"\.on\s*\(['\"\w]|\.emit\s*\(|EventEmitter|addEventListener\s*\(")),
    ("auth_pattern",     re.compile(r"jwt\.verify|bearerToken|requireAuth|@LoginRequired|session\.user|checkPermission")),
    ("dependency_injection", re.compile(r"@Injectable|@Inject\(|@Service\(|@Component\(|provide\s*\(|inject\s*\(")),
]


def detect_patterns(files: List[Path]) -> List[Dict[str, Any]]:
    """检测代码模式，返回 [{type, files, evidence}] 列表。"""
    # type -> {files, evidence}
    found: Dict[str, Dict[str, Any]] = {}

    for fpath in files:
        if not fpath.exists():
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for ptype, pattern in _PATTERN_RULES:
            m = pattern.search(text)
            if m:
                if ptype not in found:
                    found[ptype] = {"files": [], "evidence": m.group(0)[:80]}
                if str(fpath) not in found[ptype]["files"]:
                    found[ptype]["files"].append(str(fpath))

    return [
        {"type": ptype, "files": info["files"], "evidence": info["evidence"]}
        for ptype, info in found.items()
    ]


# ══════════════════════════════════════════════════════════════════════
# 4. 近似时序构建
# ══════════════════════════════════════════════════════════════════════

def build_key_sequences(
    call_graph: Dict[str, Any],
    entry_points: List[Dict[str, str]],
    max_depth: int = 6,
) -> List[Dict[str, Any]]:
    """从入口点 BFS 遍历调用图，生成近似时序。"""
    if not call_graph or not entry_points:
        return []

    sequences: List[Dict[str, Any]] = []

    for ep in entry_points:
        handler = ep.get("handler", "")
        if not handler or handler not in call_graph:
            continue

        # BFS
        visited: List[str] = []
        seen: set = set()
        queue = deque([(handler, 0)])

        while queue:
            node, depth = queue.popleft()
            if node in seen or depth > max_depth:
                continue
            seen.add(node)
            visited.append(node)
            for callee in call_graph.get(node, {}).get("calls", []):
                if callee in call_graph and callee not in seen:
                    queue.append((callee, depth + 1))

        if len(visited) < 2:
            continue

        # 从限定名提取模块名作为参与者
        def module_of(qname: str) -> str:
            parts = qname.split(".")
            return parts[0] if len(parts) > 1 else qname

        participants_ordered: List[str] = []
        seen_p: set = set()
        for qn in visited:
            p = module_of(qn)
            if p not in seen_p:
                seen_p.add(p)
                participants_ordered.append(p)

        sequences.append({
            "name": ep["name"],
            "trigger": handler,
            "participants": participants_ordered,
            "steps": [(visited[i], visited[i + 1]) for i in range(len(visited) - 1)],
        })

    return sequences


# ══════════════════════════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════════════════════════

def _has_manifest(project_path: Path) -> bool:
    manifests = ["package.json", "pyproject.toml", "requirements.txt",
                 "go.mod", "Cargo.toml", "pom.xml", "Gemfile"]
    return any((project_path / m).exists() for m in manifests)


# 词边界匹配模式：依赖名作为完整 token 匹配，避免子字符串误匹配
# 例如 "torch" 不会匹配 "torchaudio"，但会匹配 "torch>=2.0"
def _has_dep(project_path: Path, names: set) -> bool:
    """使用词边界匹配检测依赖名，避免子字符串误匹配。

    - "torch" 不会匹配 "torchaudio"
    - "gin"   不会匹配 "engine"
    - "vue"   不会匹配 "vuepress"
    """
    manifests = [
        project_path / "package.json",
        project_path / "requirements.txt",
        project_path / "pyproject.toml",
        project_path / "go.mod",
        project_path / "Cargo.toml",
    ]
    for manifest in manifests:
        if not manifest.exists():
            continue
        try:
            text = manifest.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for name in names:
            escaped = re.escape(name.lower())
            pattern = re.compile(r'(?<![.\w-])' + escaped + r'(?![.\w])')
            if pattern.search(text):
                return True
    return False


def _cargo_has_bin(project_path: Path) -> bool:
    cargo = project_path / "Cargo.toml"
    if not cargo.exists():
        return False
    try:
        return "[[bin]]" in cargo.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_structure.py <project_path>")
        sys.exit(1)
    result = run_extract_structure(Path(sys.argv[1]).resolve())
    print(json.dumps({
        "archetype": result["archetype"],
        "call_graph_size": len(result["call_graph"]),
        "patterns": [p["type"] for p in result["patterns"]],
        "sequences": len(result["key_sequences"]),
    }, ensure_ascii=False, indent=2))
