#!/usr/bin/env python3
"""
Step 3.5 辅助脚本：架构骨架数据提取

从已生成的确定性缓存文件中提取精简摘要，输出 cache/architecture-skeleton-input.json，
供 AI 在第 3.5 步生成全局架构骨架（architecture-skeleton.json）时使用。

该脚本只做数据提取和裁剪，不调用 AI：
  - structure.json       → 模块列表、重要性排名、技术栈
  - code-structure.json  → archetype、patterns 摘要、key_sequences 参与者
  - import-relations.json → 跨模块导入关系摘要（仅保留模块间关系，过滤文件内部关系）

输出：cache/architecture-skeleton-input.json（约 5-15K tokens）

用法：
  python scripts/generate_architecture_skeleton.py <项目目录绝对路径>

退出码：
  0 — 成功，architecture-skeleton-input.json 已写入
  1 — 必要的输入缓存文件缺失（需先运行 analyze_project.py 和 extract_structure.py）
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# ── 常量 ────────────────────────────────────────────────────────────────────

# import-relations 中保留的最大跨模块关系数（避免过多噪声）
MAX_CROSS_MODULE_RELATIONS = 60

# structure.json 模块列表最大保留数量
MAX_MODULES = 30

# key_sequences 最大保留条数
MAX_KEY_SEQUENCES = 5

# patterns 最大保留条数
MAX_PATTERNS = 10


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def load_json(path: Path) -> Optional[dict]:
    """加载 JSON 文件，失败返回 None。"""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def extract_module_summary(structure: dict) -> List[Dict[str, Any]]:
    """
    从 structure.json 提取模块摘要列表。

    只保留 AI 在生成骨架时需要的字段：名称、类型、重要性、文件数、核心文件数。
    """
    modules = structure.get("modules", [])[:MAX_MODULES]
    result = []
    for mod in modules:
        result.append({
            "name": mod.get("name", ""),
            "type": mod.get("type", "module"),
            "importance_score": mod.get("importance_score", 0.0),
            "files": mod.get("files", 0),
            "core_files_count": mod.get("core_files_count", 0),
            # 保留前 5 个核心文件名（文件路径可帮助 AI 识别模块职责）
            "core_files_sample": mod.get("core_files", [])[:5],
        })
    return result


def extract_project_basics(structure: dict) -> Dict[str, Any]:
    """从 structure.json 提取项目基本信息。"""
    return {
        "project_name": structure.get("project_name", ""),
        "project_type": structure.get("project_type", []),
        "languages": structure.get("languages", [])[:5],
        "entry_points": structure.get("entry_points", [])[:5],
        "stats": {
            "total_files": structure.get("stats", {}).get("total_files", 0),
            "code_files": structure.get("stats", {}).get("code_files", 0),
            "total_modules": structure.get("stats", {}).get("total_modules", 0),
        },
    }


def extract_code_structure_summary(code_structure: dict) -> Dict[str, Any]:
    """
    从 code-structure.json 提取结构摘要。

    重点提取：archetype、patterns（不含文件列表）、key_sequences 参与者。
    """
    # archetype
    archetype = code_structure.get("archetype", "unknown")

    # patterns：只保留模式名称和文件数，不含文件列表
    patterns_raw = code_structure.get("patterns", {})
    patterns_summary: Dict[str, int] = {}
    if isinstance(patterns_raw, dict):
        for pattern_name, files in patterns_raw.items():
            if isinstance(files, list):
                patterns_summary[pattern_name] = len(files)
            elif isinstance(files, (int, float)):
                patterns_summary[pattern_name] = int(files)

    # 按文件数降序排列，取前 MAX_PATTERNS 个
    patterns_sorted = dict(
        sorted(patterns_summary.items(), key=lambda x: x[1], reverse=True)[:MAX_PATTERNS]
    )

    # key_sequences：只保留参与者列表和名称，不含完整步骤
    key_sequences_raw = code_structure.get("key_sequences", [])
    key_sequences_summary = []
    for seq in key_sequences_raw[:MAX_KEY_SEQUENCES]:
        if isinstance(seq, dict):
            key_sequences_summary.append({
                "name": seq.get("name", ""),
                "participants": seq.get("participants", [])[:8],
            })

    return {
        "archetype": archetype,
        "detected_patterns": patterns_sorted,
        "key_sequences": key_sequences_summary,
    }


def extract_cross_module_imports(
    import_relations: dict,
    modules: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    从 import-relations.json 中提取跨模块导入关系。

    只保留源文件和目标文件属于不同模块的关系，
    并将文件路径归约为模块名（取第一层有效目录）。
    """
    # 构建文件 → 模块名的快速映射
    file_to_module: Dict[str, str] = {}
    for mod in modules:
        mod_path = mod.get("name", "")  # 模块名即顶层目录名
        for cf in mod.get("core_files_sample", []):
            # cf 形如 "src/auth/service.py" 或 "auth/service.py"
            file_to_module[cf] = mod_path

    def guess_module(file_path: str) -> str:
        """从文件路径猜测所属模块名（取 src/ 或根目录的直接子目录名）。"""
        parts = file_path.replace("\\", "/").split("/")
        if len(parts) >= 2 and parts[0] in ("src", "lib", "packages", "apps"):
            return parts[1] if len(parts) > 2 else parts[0]
        return parts[0] if parts else file_path

    # 提取关系
    relations_raw = import_relations
    if isinstance(relations_raw, dict) and "relations" in relations_raw:
        relations_raw = relations_raw["relations"]

    cross_module_set: Dict[Tuple[str, str], bool] = {}

    if isinstance(relations_raw, dict):
        # 格式：{file_path: [imported_file, ...]}
        for src_file, imports in relations_raw.items():
            src_mod = file_to_module.get(src_file) or guess_module(src_file)
            if not isinstance(imports, list):
                continue
            for imp in imports:
                if isinstance(imp, dict):
                    dst_file = imp.get("path", imp.get("module", ""))
                elif isinstance(imp, str):
                    dst_file = imp
                else:
                    continue
                dst_mod = file_to_module.get(dst_file) or guess_module(dst_file)
                if src_mod and dst_mod and src_mod != dst_mod:
                    cross_module_set[(src_mod, dst_mod)] = True
    elif isinstance(relations_raw, list):
        # 格式：[{from: ..., to: ...}, ...]
        for rel in relations_raw:
            if not isinstance(rel, dict):
                continue
            src_file = rel.get("from", rel.get("source", ""))
            dst_file = rel.get("to", rel.get("target", ""))
            src_mod = file_to_module.get(src_file) or guess_module(src_file)
            dst_mod = file_to_module.get(dst_file) or guess_module(dst_file)
            if src_mod and dst_mod and src_mod != dst_mod:
                cross_module_set[(src_mod, dst_mod)] = True

    # 转换为列表格式，限制数量
    cross_module_list = [
        {"from": src, "to": dst}
        for (src, dst) in list(cross_module_set.keys())[:MAX_CROSS_MODULE_RELATIONS]
    ]

    return cross_module_list


def build_skeleton_input(project_path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    构建架构骨架输入数据。

    Returns:
        (skeleton_input, warnings)
        skeleton_input: 提取结果，失败时为 None
        warnings:       非致命警告信息列表
    """
    cache_dir = project_path / ".deepwiki" / "cache"
    warnings: List[str] = []

    # ── 加载必需的输入文件 ─────────────────────────────────────────────────
    structure = load_json(cache_dir / "structure.json")
    if structure is None:
        return None, ["structure.json 不存在，请先运行 analyze_project.py"]

    code_structure = load_json(cache_dir / "code-structure.json")
    if code_structure is None:
        warnings.append("code-structure.json 不存在，跳过代码结构摘要提取（建议先运行 extract_structure.py）")
        code_structure = {}

    import_relations_data = load_json(cache_dir / "import-relations.json")
    if import_relations_data is None:
        warnings.append("import-relations.json 不存在，跳过跨模块导入关系提取")
        import_relations_data = {}

    # ── 提取各部分摘要 ─────────────────────────────────────────────────────
    project_basics = extract_project_basics(structure)
    modules_summary = extract_module_summary(structure)
    code_summary = extract_code_structure_summary(code_structure)
    cross_imports = extract_cross_module_imports(import_relations_data, modules_summary)

    skeleton_input = {
        "project": project_basics,
        "modules": modules_summary,
        "code_structure": code_summary,
        "cross_module_imports": cross_imports,
        # 元数据
        "_meta": {
            "source_files": [
                "cache/structure.json",
                "cache/code-structure.json",
                "cache/import-relations.json",
            ],
            "purpose": (
                "AI 读取此文件，生成 cache/architecture-skeleton.json。"
                "骨架包含：project_nature、architecture_style、module_groups、"
                "cross_domain_dependencies、key_data_flows。"
            ),
        },
    }

    return skeleton_input, warnings


def main() -> int:
    # 确保 Windows 控制台支持 UTF-8 输出
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print(
            "用法：python scripts/generate_architecture_skeleton.py <项目目录绝对路径>",
            file=sys.stderr,
        )
        return 1


    project_path = Path(sys.argv[1])
    if not project_path.is_dir():
        print(f"❌ 项目目录不存在: {project_path}", file=sys.stderr)
        return 1

    skeleton_input, warnings = build_skeleton_input(project_path)

    for w in warnings:
        print(f"⚠  {w}", file=sys.stderr)

    if skeleton_input is None:
        print("❌ 构建架构骨架输入失败，请检查缓存文件", file=sys.stderr)
        return 1

    # 写出 architecture-skeleton-input.json
    output_path = project_path / ".deepwiki" / "cache" / "architecture-skeleton-input.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(skeleton_input, f, indent=2, ensure_ascii=False)

    n_modules = len(skeleton_input.get("modules", []))
    n_imports = len(skeleton_input.get("cross_module_imports", []))
    print(
        f"✅ 架构骨架输入数据已写入: {output_path}\n"
        f"   模块数: {n_modules}  跨模块导入关系: {n_imports}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
