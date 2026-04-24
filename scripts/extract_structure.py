#!/usr/bin/env python3
"""
代码结构提取脚本 v2.0

基于 tree-sitter AST 解析，从源码中精确提取调用图、代码模式和近似时序。
输出 .deepwiki/cache/code-structure.json，供 AI 深度阅读阶段使用。
"""

from collections import deque
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

from common import CODE_EXTENSIONS, CACHE_SCHEMA_VERSION
from import_relations import extract_import_relations
from parsers import get_manager, get_lang_for_ext


# ══════════════════════════════════════════════════════════════════════
# 调用提取过滤集合
# ══════════════════════════════════════════════════════════════════════

_SKIP: frozenset = frozenset({
    "if", "for", "while", "switch", "catch", "return", "await", "new",
    "typeof", "instanceof", "console", "print", "len", "str", "int",
    "float", "bool", "list", "dict", "set", "super", "self", "this",
    "True", "False", "None", "require", "import", "export", "const",
    "let", "var", "async", "function", "class", "extends", "implements",
    "type", "interface", "enum", "namespace", "module", "from",
})


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
    seen_paths: Set[str] = set()
    all_files: List[Path] = []
    for cf in structure.get("core_files", []) + structure.get("high_priority_files", []):
        p = project_path / cf["path"]
        if p.exists() and str(p) not in seen_paths:
            seen_paths.add(str(p))
            all_files.append(p)

    archetype = detect_archetype(project_path)
    call_graph = extract_call_graph(all_files)
    patterns = detect_patterns(all_files)

    # Import 关系（可信基线，供依赖综合阶段交叉验证）
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

    # 输出 parse-results.json（AST 摘要缓存，供后续步骤复用，避免重复 tree-sitter 解析）
    parse_summaries = _collect_parse_summaries(all_files, project_path)
    pr_path = project_path / ".deepwiki" / "cache" / "parse-results.json"
    pr_path.parent.mkdir(parents=True, exist_ok=True)
    with open(pr_path, "w", encoding="utf-8") as f:
        json.dump({
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "files": parse_summaries,
        }, f, ensure_ascii=False, indent=2)

    return result


def _build_entry_points(structure: dict, call_graph: dict) -> List[Dict[str, str]]:
    """从 structure.json 的 entry_points 字段构建入口点列表。

    匹配优先级：
    1. 精确匹配入口文件名（main.py → "main"）
    2. 精确匹配入口文件名前缀（app.py → "app"）
    3. 精确匹配常见入口函数名（main, run, start）
    4. 子串匹配（兜底）
    """
    ENTRY_NAMES = {"main", "run", "start", "create_app", "serve"}
    eps = []
    for ep_path in structure.get("entry_points", []):
        stem = Path(ep_path).stem
        handler = None

        # 1. 精确匹配 stem
        if stem in call_graph and call_graph[stem].get("calls"):
            handler = stem
        else:
            # 2. 精确匹配 stem（即使 calls 为空也比子串匹配好）
            if stem in call_graph:
                handler = stem
            else:
                # 3. 精确匹配入口函数名（按优先级排序）
                for name in ENTRY_NAMES:
                    if name in call_graph and call_graph[name].get("calls"):
                        handler = name
                        break
                if handler is None:
                    # 4. 子串匹配（兜底，仅匹配 has calls 的 key）
                    sub = [k for k in call_graph
                            if stem.lower() in k.lower()
                            and call_graph[k].get("calls")]
                    if sub:
                        handler = sub[0]
                    else:
                        handler = stem

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
            _has_dep(p, {"langchain", "langgraph", "pi-mono", "llamaindex", "crewai", "autogen", "semantic-kernel"})
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
# 2. 调用图提取 (tree-sitter)
# ══════════════════════════════════════════════════════════════════════

def _parse_definitions(text: bytes, lang_name: str, fpath: str) -> List[Tuple[str, int, bytes]]:
    """用 tree-sitter 提取函数/方法定义，返回 [(qualified_name, line_no, body_bytes)]。

    每种语言使用统一策略：
    1. 查询所有 function_definition 和 class_definition 节点
    2. 通过父节点链判断是否在类/impl 内，生成限定名
    3. 提取函数体字节用于后续调用分析
    """
    from tree_sitter import Language, Query, QueryCursor

    mgr = get_manager()
    lang = mgr.get_language(lang_name)
    parser = mgr.get_parser(lang_name)
    tree = parser.parse(text)
    root = tree.root_node

    if root.has_error or root.child_count == 0:
        return []

    # 获取 func_class query 的所有 captures
    captures = mgr.run_query(lang_name, "func_class", root)

    # 提取类/impl 的范围用于限定名生成
    class_ranges: List[Tuple[str, int, int]] = []  # (class_name, start_byte, end_byte)

    # 按语言收集容器节点
    if lang_name == "python":
        for cls_node in captures.get("cls", []):
            name_node = cls_node.child_by_field_name("name")
            if name_node:
                class_ranges.append((
                    name_node.text.decode(),
                    cls_node.start_byte,
                    cls_node.end_byte,
                ))
    elif lang_name in ("javascript", "typescript", "tsx", "java", "kotlin"):
        for cls_node in captures.get("cls", []):
            name_node = cls_node.child_by_field_name("name")
            if name_node:
                class_ranges.append((
                    name_node.text.decode(),
                    cls_node.start_byte,
                    cls_node.end_byte,
                ))
    elif lang_name == "rust":
        for impl_node in captures.get("impl", []):
            type_node = impl_node.child_by_field_name("type")
            if type_node:
                class_ranges.append((
                    type_node.text.decode(),
                    impl_node.start_byte,
                    impl_node.end_byte,
                ))

    def get_qualifier(start_byte: int) -> Optional[str]:
        """检查节点是否在某个类/impl 范围内，返回限定前缀。"""
        for cname, s, e in class_ranges:
            if s <= start_byte < e:
                return cname
        return None

    # 提取函数/方法定义
    results: List[Tuple[str, int, bytes]] = []
    seen: Set[str] = set()

    # 按语言获取函数节点和体节点
    if lang_name == "python":
        for fn_node in captures.get("fn", []):
            name_node = fn_node.child_by_field_name("name")
            body_node = fn_node.child_by_field_name("body")
            if not name_node or not body_node:
                continue
            name = name_node.text.decode()
            line_no = fn_node.start_point[0] + 1
            qf = get_qualifier(fn_node.start_byte)
            qname = f"{qf}.{name}" if qf else name
            if qname not in seen:
                seen.add(qname)
                results.append((qname, line_no, body_node.text))

    elif lang_name == "go":
        # 普通函数
        for fn_node in captures.get("fn", []):
            name_node = fn_node.child_by_field_name("name")
            if not name_node:
                continue
            name = name_node.text.decode()
            line_no = fn_node.start_point[0] + 1
            if name not in seen:
                seen.add(name)
                results.append((name, line_no, fn_node.text))
        # 方法 (method_declaration)
        for method_node in captures.get("method", []):
            recv_list = method_node.child_by_field_name("receiver")
            name_node = method_node.child_by_field_name("name")
            if not recv_list or not name_node:
                continue
            # 提取 receiver type
            recv_type = _extract_go_receiver_type(recv_list)
            method_name = name_node.text.decode()
            line_no = method_node.start_point[0] + 1
            qname = f"{recv_type}.{method_name}" if recv_type else method_name
            if qname not in seen:
                seen.add(qname)
                results.append((qname, line_no, method_node.text))

    elif lang_name == "rust":
        # 普通函数
        for fn_node in captures.get("fn", []):
            name_node = fn_node.child_by_field_name("name")
            if not name_node:
                continue
            name = name_node.text.decode()
            line_no = fn_node.start_point[0] + 1
            qf = get_qualifier(fn_node.start_byte)
            qname = f"{qf}.{name}" if qf else name
            if qname not in seen:
                seen.add(qname)
                results.append((qname, line_no, fn_node.text))
        # impl 内的函数通过 get_qualifier 已处理（fn 节点在 impl 范围内）

    elif lang_name in ("java",):
        # Java: method_declaration
        for method_node in captures.get("method", []):
            name_node = method_node.child_by_field_name("name")
            body_node = method_node.child_by_field_name("body")
            if not name_node:
                continue
            name = name_node.text.decode()
            line_no = method_node.start_point[0] + 1
            qf = get_qualifier(method_node.start_byte)
            qname = f"{qf}.{name}" if qf else name
            if qname not in seen:
                seen.add(qname)
                body = body_node.text if body_node else method_node.text
                results.append((qname, line_no, body))

    elif lang_name == "kotlin":
        # Kotlin: function_declaration
        for fn_node in captures.get("fn", []):
            name_node = fn_node.child_by_field_name("name") if fn_node.type == "function_declaration" else None
            if not name_node:
                # Kotlin function_declaration 的 name 字段可能是 simple_identifier
                for child in fn_node.named_children:
                    if child.type == "simple_identifier":
                        name_node = child
                        break
            if not name_node:
                continue
            name = name_node.text.decode()
            line_no = fn_node.start_point[0] + 1
            qf = get_qualifier(fn_node.start_byte)
            qname = f"{qf}.{name}" if qf else name
            if qname not in seen:
                seen.add(qname)
                results.append((qname, line_no, fn_node.text))

    elif lang_name in ("javascript", "typescript", "tsx"):
        # JS/TS: function_declaration
        for fn_node in captures.get("fn", []):
            name_node = fn_node.child_by_field_name("name")
            body_node = fn_node.child_by_field_name("body")
            if not name_node:
                continue
            name = name_node.text.decode()
            line_no = fn_node.start_point[0] + 1
            qf = get_qualifier(fn_node.start_byte)
            qname = f"{qf}.{name}" if qf else name
            if qname not in seen:
                seen.add(qname)
                body = body_node.text if body_node else fn_node.text
                results.append((qname, line_no, body))

        # JS/TS: method_definition（类方法）
        for method_node in captures.get("method", []):
            name_node = method_node.child_by_field_name("name")
            body_node = method_node.child_by_field_name("body")
            if not name_node:
                continue
            name = name_node.text.decode()
            line_no = method_node.start_point[0] + 1
            qf = get_qualifier(method_node.start_byte)
            qname = f"{qf}.{name}" if qf else name
            if qname not in seen:
                seen.add(qname)
                body = body_node.text if body_node else method_node.text
                results.append((qname, line_no, body))

        # 箭头函数（导出赋值）
        for arrow_node in captures.get("arrow", []):
            # arrow_node 是 lexical_declaration，取 variable_declarator
            for child in arrow_node.named_children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    value_node = child.child_by_field_name("value")
                    if name_node and value_node and name_node.text.decode() not in _SKIP:
                        name = name_node.text.decode()
                        line_no = arrow_node.start_point[0] + 1
                        if name not in seen:
                            seen.add(name)
                            results.append((name, line_no, value_node.text))
                        break

    # 按行号排序
    results.sort(key=lambda x: x[1])
    return results


def _extract_go_receiver_type(param_list_node) -> Optional[str]:
    """从 Go method_declaration 的 receiver 参数列表提取类型名。"""
    # receiver 是 parameter_list，内含 parameter_declaration
    for child in param_list_node.named_children:
        if child.type == "parameter_declaration":
            type_node = child.child_by_field_name("type")
            if type_node:
                # 可能是指针类型 *Type，取最后一个标识符
                if type_node.type == "pointer_type":
                    for tc in type_node.named_children:
                        if tc.type in ("type_identifier", "identifier"):
                            return tc.text.decode()
                elif type_node.type in ("type_identifier", "identifier"):
                    return type_node.text.decode()
    return None


def _extract_calls_from_body(body: bytes, func_name: str, lang_name: str) -> List[str]:
    """用 tree-sitter 从函数体中提取函数调用，过滤关键字。"""
    mgr = get_manager()
    parser = mgr.get_parser(lang_name)
    tree = parser.parse(body)
    root = tree.root_node

    if root.has_error or root.child_count == 0:
        return []

    try:
        captures = mgr.run_query(lang_name, "call", root)
    except (ValueError, Exception):
        return []

    calls: List[str] = []
    seen: Set[str] = set()

    fn_calls = captures.get("call.fn", [])
    for node in fn_calls:
        name = node.text.decode()
        if name not in _SKIP and name not in seen and len(name) > 1 and name != func_name:
            seen.add(name)
            calls.append(name)

    obj_calls = captures.get("call.obj", [])
    attr_calls = captures.get("call.attr", [])
    for obj_node, attr_node in zip(obj_calls, attr_calls):
        raw_obj = obj_node.text.decode("utf-8", errors="replace")
        attr = attr_node.text.decode("utf-8", errors="replace")
        if attr in _SKIP:
            continue
        # member_expression として捕捉された場合（例: this.userDao）
        # "this." プレフィックスを除去して短い識別子として扱う
        if obj_node.type == "member_expression":
            obj = raw_obj
            if obj.startswith("this."):
                obj = obj[5:]
        else:
            obj = raw_obj
        if obj in _SKIP or not obj:
            continue
        c = f"{obj}.{attr}"
        if c not in seen and c != func_name:
            seen.add(c)
            calls.append(c)

    return calls[:20]


def extract_call_graph(files: List[Path]) -> Dict[str, Any]:
    """从源文件列表中提取调用图，使用 tree-sitter AST 解析。"""
    graph: Dict[str, Any] = {}

    for fpath in files:
        if not fpath.exists():
            continue
        ext = fpath.suffix.lower()
        lang_name = get_lang_for_ext(ext)
        if not lang_name:
            continue

        try:
            source = fpath.read_bytes()
            if not source.strip():
                continue
        except Exception:
            continue

        try:
            file_defs = _parse_definitions(source, lang_name, str(fpath))
        except Exception:
            continue

        for func_name, line_no, body_bytes in file_defs:
            body_text = body_bytes.decode("utf-8", errors="replace")
            calls = _extract_calls_from_body(body_bytes, func_name, lang_name)
            graph[func_name] = {
                "calls": calls,
                "file": str(fpath),
                "line": line_no,
            }

    return graph


# ══════════════════════════════════════════════════════════════════════
# 2.5 Parse Results 缓存（AST 摘要收集）
# ══════════════════════════════════════════════════════════════════════

def _collect_parse_summaries(
    files: List[Path], project_path: Path
) -> Dict[str, Dict[str, Any]]:
    """收集每个文件的 tree-sitter AST 摘要，供后续步骤复用。

    在 extract_call_graph 已解析过的文件上做一轮轻量补充收集，
    提取 definitions / complexity_nodes / important_lines，
    写入 cache/parse-results.json，避免后续步骤重复 tree-sitter 解析。

    Returns:
        {rel_path: {
            "language": "python",
            "definitions": [{"name": "func", "kind": "function", "line": 10, "end_line": 25}],
            "complexity_nodes": 15,
            "complexity_score": 42,
            "important_lines": [1, 3, 10],
            "important_lines_count": 3,
            "loc": 50,
        }}
    """
    from code_metrics import compute_complexity_score

    mgr = get_manager()
    summaries: Dict[str, Dict[str, Any]] = {}

    for fpath in files:
        if not fpath.exists():
            continue
        ext = fpath.suffix.lower()
        lang_name = get_lang_for_ext(ext)
        if not lang_name:
            continue

        try:
            source = fpath.read_bytes()
            if not source.strip():
                continue
        except Exception:
            continue

        try:
            parser = mgr.get_parser(lang_name)
            tree = parser.parse(source)
            root = tree.root_node

            if root.has_error and root.child_count == 0:
                continue

            rel_path = str(fpath.relative_to(project_path)).replace("\\", "/")
            summary: Dict[str, Any] = {"language": lang_name}

            # 1. 提取定义列表（复用 _parse_definitions）
            defs = _parse_definitions(source, lang_name, str(fpath))
            summary["definitions"] = [
                {
                    "name": name,
                    "kind": "method" if "." in name else "function",
                    "line": line_no,
                    "end_line": line_no + body_bytes.count(b"\n"),
                }
                for name, line_no, body_bytes in defs
            ]

            # 2. 复杂度节点计数 + complexity_score + loc
            try:
                caps = mgr.run_query(lang_name, "complexity", root)
                cf_count = len(caps.get("cf", []))
                def_count = len(caps.get("def", []))
                summary["complexity_nodes"] = cf_count + def_count
                lines = source.split(b"\n")
                non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith((b"#", b"//", b"/*", b"*"))]
                loc = len(non_empty_lines)
                summary["loc"] = loc
                summary["complexity_score"] = compute_complexity_score(cf_count, def_count, loc)
            except Exception:
                summary["complexity_nodes"] = 0
                summary["loc"] = 0
                summary["complexity_score"] = 0

            # 3. 重要行号集合
            try:
                caps = mgr.run_query(lang_name, "important", root)
                important_lines: set = set()
                for category in ("imp", "exp", "decl"):
                    for node in caps.get(category, []):
                        important_lines.add(node.start_point[0])
                # TODO/FIXME 标记
                import re as _re
                for i, line in enumerate(source.split(b"\n")):
                    line_str = line.decode("utf-8", errors="replace")
                    if _re.search(
                        r"(?:TODO|FIXME|HACK|NOTE|WARN|XXX)\s*[:\(]", line_str
                    ):
                        important_lines.add(i)
                summary["important_lines"] = sorted(important_lines)
                summary["important_lines_count"] = len(summary["important_lines"])
            except Exception:
                summary["important_lines"] = []
                summary["important_lines_count"] = 0

            summaries[rel_path] = summary
        except Exception:
            continue

    return summaries


# ══════════════════════════════════════════════════════════════════════
# 3. 代码模式检测（保留 regex，适合高层语义模式扫描）
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

        if len(visited) < 1:
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
    """使用词边界匹配检测依赖名，避免子字符串误匹配。"""
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
