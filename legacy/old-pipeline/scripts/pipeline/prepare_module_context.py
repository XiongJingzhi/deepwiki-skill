"""
prepare_module_context.py
在 extract-docs 之前运行，为每个模块生成独立的 context.json，
避免每个 subagent 加载完整的全量缓存文件。

用法:
    python scripts/prepare_module_context.py <project_dir>

输出:
    <project_dir>/.deepwiki/cache/modules/<module_slug>/context.json
"""
import json
import hashlib
from pathlib import Path

from scripts.core.common import infer_code_purpose, get_module_files


def _extract_signatures(parse_result_file: dict, analysis_depth: str) -> list:
    """从 parse-results.json 单文件数据中按分析深度提取签名列表。

    - deep：全部签名，包含所有字段
    - standard：仅有 doc 注释的签名（无注释只保留 name/line/end_line）
    - quick：空列表
    """
    if analysis_depth == "quick":
        return []

    definitions = parse_result_file.get("definitions", [])
    signatures = []
    for defn in definitions:
        has_doc = bool(defn.get("doc", "").strip())
        if analysis_depth == "deep":
            sig = {
                "name": defn.get("name", ""),
                "kind": defn.get("kind", ""),
                "line": defn.get("line"),
                "end_line": defn.get("end_line"),
            }
            if "doc" in defn:
                sig["doc"] = defn["doc"]
            if "params" in defn:
                sig["params"] = defn["params"]
            if "returns" in defn:
                sig["returns"] = defn["returns"]
            signatures.append(sig)
        else:  # standard
            if has_doc:
                sig = {
                    "name": defn.get("name", ""),
                    "kind": defn.get("kind", ""),
                    "line": defn.get("line"),
                    "end_line": defn.get("end_line"),
                    "doc": defn["doc"],
                }
                if "params" in defn:
                    sig["params"] = defn["params"]
                if "returns" in defn:
                    sig["returns"] = defn["returns"]
            else:
                sig = {
                    "name": defn.get("name", ""),
                    "line": defn.get("line"),
                    "end_line": defn.get("end_line"),
                }
            signatures.append(sig)
    return signatures


def _extract_exports(parse_result_file: dict, important_lines: list) -> list:
    """从 parse-results.json 中提取顶层（非嵌套）导出符号名列表。

    与 important_lines 中含 'export' 关键词的行做交叉验证。
    """
    definitions = parse_result_file.get("definitions", [])

    # 收集 important_lines 中含 export 的行号集合
    export_lines: set = set()
    for line_entry in important_lines:
        if isinstance(line_entry, dict):
            lineno = line_entry.get("line")
            content = line_entry.get("content", "")
        elif isinstance(line_entry, (list, tuple)) and len(line_entry) >= 2:
            lineno, content = line_entry[0], line_entry[1]
        else:
            continue
        if "export" in str(content):
            export_lines.add(lineno)

    exports = []
    for defn in definitions:
        # 非嵌套：无 parent 字段或 parent 为空
        if defn.get("parent"):
            continue
        name = defn.get("name", "")
        if not name:
            continue
        # 若能与 export_lines 交叉验证则优先采纳，否则保留所有顶层定义
        if not export_lines or defn.get("line") in export_lines:
            exports.append(name)

    # 若 export_lines 非空但无交叉结果，退回全部顶层定义（不遗漏信息）
    if export_lines and not exports:
        exports = [d.get("name", "") for d in definitions if not d.get("parent") and d.get("name")]

    return exports


def _module_slug(module_path: str) -> str:
    """将模块路径转为安全的目录名，如 src/auth -> src_auth"""
    return module_path.replace("/", "_").replace("\\", "_").strip("_")


def _filter_import_relations(import_relations: dict, module_files: set) -> dict:
    """保留当前模块文件的出边和其他文件指向本模块文件的入边"""
    result = {}
    for file, data in import_relations.items():
        if file in module_files:
            result[file] = data
        else:
            # data 可能是列表（文件路径列表）或字典
            if isinstance(data, list):
                filtered = [imp for imp in data if isinstance(imp, str) and imp in module_files
                            or (isinstance(imp, dict) and imp.get("module") in module_files)]
                if filtered:
                    result[file] = data if all(isinstance(imp, str) for imp in data) else {"imports": filtered}
            else:
                filtered_imports = [
                    imp for imp in data.get("imports", [])
                    if imp.get("module") in module_files
                ]
                if filtered_imports:
                    result[file] = {"imports": filtered_imports}
    return result


def _filter_call_graph(call_graph: dict, module_files: set) -> dict:
    return {k: v for k, v in call_graph.items() if k in module_files}


def _infer_analysis_depth(complexity_score: float, important_lines_count: int,
                          code_purpose: str = "", is_workspace: bool = False) -> str:
    if complexity_score >= 30 or important_lines_count >= 20:
        return "deep"
    if complexity_score >= 15 or important_lines_count >= 8:
        return "standard"
    if code_purpose in ("Entry", "Service", "Agent", "Command"):
        return "standard"
    if is_workspace:
        # monorepo workspace 子模块至少 standard，确保分析深入到包内部结构
        return "standard"
    return "quick"


def _aggregate_dependency_hints(module_files: set, all_module_files: dict, import_relations: dict) -> dict:
    file_to_module: dict = {}
    for mod_path, files in all_module_files.items():
        for f in files:
            file_to_module[f] = mod_path

    imports_modules: set = set()
    imported_by_modules: set = set()

    for file, data in import_relations.items():
        file_module = file_to_module.get(file)
        imports_list = data if isinstance(data, list) else data.get("imports", [])
        for imp in imports_list:
            if isinstance(imp, dict):
                target_file = imp.get("module", "")
            else:
                target_file = imp
            target_module = file_to_module.get(target_file)
            if target_module and target_module != file_module:
                if file in module_files:
                    imports_modules.add(target_module)
                elif target_file in module_files:
                    if file_module:
                        imported_by_modules.add(file_module)

    return {
        "imports": sorted(imports_modules),
        "imported_by": sorted(imported_by_modules)
    }


def _compute_input_hash(structure: dict, code_structure: dict, parse_results_mtime: float = 0.0) -> str:
    content = (
        json.dumps(structure, sort_keys=True)
        + json.dumps(code_structure, sort_keys=True)
        + str(parse_results_mtime)
    )
    return hashlib.md5(content.encode()).hexdigest()


def _get_file_data(structure: dict, file_path: str) -> dict:
    for key in ("files", "core_files", "all_files"):
        files_data = structure.get(key, [])
        if isinstance(files_data, list):
            for f in files_data:
                if isinstance(f, dict) and f.get("path") == file_path:
                    return f
        elif isinstance(files_data, dict):
            if file_path in files_data:
                return files_data[file_path]
    return {}


def prepare_module_context(project_dir) -> dict:
    """
    为每个模块生成独立的 context.json，输出到 .deepwiki/cache/modules/<slug>/context.json。
    Returns: {module_path: context_file_path}
    """
    project_dir = Path(project_dir)
    cache_dir = project_dir / ".deepwiki" / "cache"

    structure_path = cache_dir / "structure.json"
    code_structure_path = cache_dir / "code-structure.json"
    parse_results_path = cache_dir / "parse-results.json"

    if not structure_path.exists() or not code_structure_path.exists():
        raise FileNotFoundError(f"缺少必要输入文件：{structure_path} 或 {code_structure_path}")

    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    code_structure = json.loads(code_structure_path.read_text(encoding="utf-8"))

    # 读取 parse-results.json（可选），用于签名注入
    parse_results: dict = {}
    parse_results_mtime: float = 0.0
    if parse_results_path.exists():
        parse_results = json.loads(parse_results_path.read_text(encoding="utf-8"))
        parse_results_mtime = parse_results_path.stat().st_mtime

    modules_raw = structure.get("modules", {})
    if isinstance(modules_raw, list):
        modules: dict = {m.get("path", m.get("name", str(i))): m for i, m in enumerate(modules_raw)}
    else:
        modules: dict = modules_raw
    import_relations: dict = code_structure.get("import_relations", {})
    call_graph: dict = code_structure.get("call_graph", {})

    all_module_files: dict = {
        mod: set(get_module_files(info))
        for mod, info in modules.items()
    }

    input_hash = _compute_input_hash(structure, code_structure, parse_results_mtime)
    result: dict = {}

    for module_path, module_info in modules.items():
        slug = _module_slug(module_path)
        out_dir = cache_dir / "modules" / slug
        out_path = out_dir / "context.json"

        hash_path = out_dir / "context.hash"

        # 缓存失效检查：hash 存于独立 sidecar 文件，不污染 AI 消费的 context.json
        if out_path.exists() and hash_path.exists():
            try:
                if hash_path.read_text(encoding="utf-8").strip() == input_hash:
                    result[module_path] = out_path
                    continue
            except OSError:
                pass

        module_files = all_module_files[module_path]
        files_list = get_module_files(module_info)

        # monorepo workspace 子模块提升分析深度
        discovery_basis = module_info.get("discovery_basis", "") if isinstance(module_info, dict) else ""
        is_workspace = str(discovery_basis).startswith("workspace")

        files_info = []
        for f in files_list:
            file_data = _get_file_data(structure, f)
            complexity = file_data.get("complexity_score", 0)
            important_lines_count = file_data.get("important_lines_count", 0)
            code_purpose = file_data.get("code_purpose", infer_code_purpose(f))
            analysis_depth = _infer_analysis_depth(complexity, important_lines_count, code_purpose, is_workspace)

            # 从 parse-results.json 注入 signatures 和 exports
            files_map = parse_results.get("files", {}) if isinstance(parse_results, dict) else {}
            parse_file_data = files_map.get(f, {}) if isinstance(files_map, dict) else {}
            important_lines_raw = file_data.get("important_lines", [])
            signatures = _extract_signatures(parse_file_data, analysis_depth)
            exports = _extract_exports(parse_file_data, important_lines_raw)

            files_info.append({
                "path": f,
                "complexity_score": complexity,
                "code_purpose": infer_code_purpose(f),
                "analysis_depth": analysis_depth,
                "exports": exports,
                "signatures": signatures,
                # important_lines_count 已用于推断 analysis_depth，AI 无需再读
            })

        # 去除纯元数据字段（is_candidate 恒 true；discovery_basis/refined_by 已在脚本内消费；core_files_count 可从 files 推导）
        _drop = {"files", "core_files", "is_candidate", "discovery_basis", "refined_by", "core_files_count"}
        module_info_out = {k: v for k, v in module_info.items() if k not in _drop}
        module_info_out["importance_score"] = module_info.get("importance_score", 0)

        # import_relations：过滤空值条目（空列表对 AI 零信息量）
        filtered_ir = {
            k: v for k, v in _filter_import_relations(import_relations, module_files).items()
            if v
        }

        # call_graph：仅非空时写入
        filtered_cg = _filter_call_graph(call_graph, module_files)

        # 展平 prefilled 包装层，dependency_hints 直接置于顶层
        context = {
            "module_path": module_path,
            "module_info": module_info_out,
            "files": files_info,
            "import_relations": filtered_ir,
            "dependency_hints": _aggregate_dependency_hints(module_files, all_module_files, import_relations),
        }
        if filtered_cg:
            context["call_graph"] = filtered_cg

        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
        # hash 写入独立 sidecar，与 AI 消费内容分离
        hash_path.write_text(input_hash, encoding="utf-8")
        result[module_path] = out_path

    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python -m scripts.pipeline.prepare_module_context <project_dir>")
        sys.exit(0 if len(sys.argv) >= 2 else 1)
    results = prepare_module_context(Path(sys.argv[1]))
    print(f"已为 {len(results)} 个模块生成 context.json")
    for mod, path in results.items():
        print(f"  {mod} -> {path}")
