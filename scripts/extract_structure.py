#!/usr/bin/env python3
"""
代码结构提取脚本 v1.0
基于正则+启发式，从源码中提取调用图、代码模式和近似时序。
输出 .deepwiki/cache/code-structure.json，供 AI 深度阅读阶段使用。
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from common import CODE_EXTENSIONS


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

    # 收集待分析文件
    core_files = [
        project_path / cf["path"]
        for cf in structure.get("core_files", [])
        if (project_path / cf["path"]).exists()
    ]

    archetype = detect_archetype(project_path)
    call_graph = extract_call_graph(core_files)
    patterns = detect_patterns(core_files)

    # 构建入口点
    entry_points = _build_entry_points(structure, call_graph)
    key_sequences = build_key_sequences(call_graph, entry_points)

    result = {
        "archetype": archetype,
        "call_graph": call_graph,
        "patterns": patterns,
        "key_sequences": key_sequences,
        "entry_points": entry_points,
    }

    out_path = project_path / ".deepwiki" / "cache" / "code-structure.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

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
        ("ml-project", lambda p: _has_dep(p, {
            "torch", "tensorflow", "keras", "scikit-learn", "sklearn",
            "transformers", "pytorch", "jax", "paddle",
        })),
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
_PY_DEF     = re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
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


def extract_call_graph(files: List[Path]) -> Dict[str, Any]:
    """从源文件列表中提取调用图。"""
    graph: Dict[str, Any] = {}

    for fpath in files:
        if not fpath.exists():
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lines_list = text.splitlines()

        # 类行范围
        class_ranges: List[list] = []
        for m in re.finditer(r"^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)", text, re.MULTILINE):
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

        for m in re.finditer(r"^(?:async\s+)?def\s+(\w+)\s*\(", text, re.MULTILINE):
            ln = text[:m.start()].count("\n")
            cls = get_class_at(ln)
            qn = f"{cls}.{m.group(1)}" if cls else m.group(1)
            defined.append((qn, ln + 1))

        for m in re.finditer(r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(", text, re.MULTILINE):
            ln = text[:m.start()].count("\n")
            defined.append((m.group(1), ln + 1))

        for m in re.finditer(r"^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*[\(<]", text, re.MULTILINE):
            ln = text[:m.start()].count("\n")
            defined.append((m.group(1), ln + 1))

        for m in re.finditer(r"^[ \t]{1,}(?:(?:async|static|public|private|protected|override)\s+)*(\w+)\s*\(", text, re.MULTILINE):
            name = m.group(1)
            if name in _SKIP or name[0].isupper():
                continue
            ln = text[:m.start()].count("\n")
            cls = get_class_at(ln)
            if cls:
                qn = f"{cls}.{name}"
                defined.append((qn, ln + 1))

        seen_n: set = set()
        unique_defs: List[tuple] = []
        for qn, ln in sorted(defined, key=lambda x: x[1]):
            if qn not in seen_n:
                seen_n.add(qn)
                unique_defs.append((qn, ln))

        for i, (func_name, line_no) in enumerate(unique_defs):
            s = line_no - 1
            e = unique_defs[i + 1][1] - 1 if i + 1 < len(unique_defs) else len(lines_list)
            body = "\n".join(lines_list[s:e])

            calls: List[str] = []
            for m in re.finditer(r"\b(\w+)\.(\w+)\s*\(", body):
                obj, meth = m.group(1), m.group(2)
                if obj not in _SKIP and meth not in _SKIP:
                    calls.append(f"{obj}.{meth}")
            for m in re.finditer(r"\b([A-Za-z_]\w{2,})\s*\(", body):
                name = m.group(1)
                if name not in _SKIP:
                    calls.append(name)

            deduped: List[str] = []
            seen_c: set = set()
            for c in calls:
                if c not in seen_c and c != func_name:
                    seen_c.add(c)
                    deduped.append(c)

            graph[func_name] = {
                "calls": deduped[:20],
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
        queue = [(handler, 0)]

        while queue:
            node, depth = queue.pop(0)
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


def _has_dep(project_path: Path, names: set) -> bool:
    manifests = [project_path / m for m in [
        "package.json", "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml"
    ]]
    for manifest in manifests:
        if not manifest.exists():
            continue
        try:
            text = manifest.read_text(encoding="utf-8", errors="ignore").lower()
            if any(n.lower() in text for n in names):
                return True
        except Exception:
            continue
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
