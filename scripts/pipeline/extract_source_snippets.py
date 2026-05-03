"""
extract_source_snippets.py
在 generate-module-docs 之前运行，预提取源码片段，
避免 subagent 读取整文件而仅使用 ranges 范围。

用法:
    python scripts/pipeline/extract_source_snippets.py <project_dir>

输入:
    <project_dir>/.deepwiki/cache/generation-plan.json
    项目源码文件

输出:
    <project_dir>/.deepwiki/cache/snippets/<page_id>.json
"""
import json
from pathlib import Path
from typing import Any, Dict, List

from scripts.core.common import cache_path

CONTEXT_LINES = 5  # ranges 两侧各保留的上下文行数
MAX_SNIPPET_CHARS = 30000  # 单个 snippet 最大字符数（防止超大文件）


def _read_lines(file_path: Path) -> List[str]:
    """读取文件所有行（保留换行符），读取失败返回空列表。"""
    try:
        return file_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except (OSError, UnicodeDecodeError):
        return []


def _extract_snippet(lines: List[str], start_line: int, end_line: int) -> str:
    """提取指定行范围（1-based）的代码内容，包含上下文。

    自动 clamp 到文件实际行数范围。
    """
    total = len(lines)
    if total == 0:
        return ""
    ctx_start = max(0, start_line - 1 - CONTEXT_LINES)
    ctx_end = min(total, end_line + CONTEXT_LINES)

    if ctx_start >= total:
        return ""

    selected = lines[ctx_start:ctx_end]

    # 截断超大 snippet
    content = "".join(selected)
    if len(content) > MAX_SNIPPET_CHARS:
        content = content[:MAX_SNIPPET_CHARS] + "\n// ... (truncated)"
    return content


def extract_snippets_for_page(
    page_id: str,
    source_files: List[Dict[str, Any]],
    project_root: Path,
) -> Dict[str, Any]:
    """为一个页面提取所有源码片段。

    Args:
        page_id: 页面标识（如 "deep-dive:auth"）
        source_files: generation-plan 中的 source_files 列表
        project_root: 项目根目录

    Returns:
        {"page_id": str, "snippets": [...]}
    """
    snippets: List[Dict[str, Any]] = []

    for sf in source_files:
        file_path_str = sf.get("path", "")
        if not file_path_str:
            continue

        file_path = project_root / file_path_str
        ranges = sf.get("ranges", [])

        if not ranges:
            # 无 ranges 时跳过（subagent 将自行读取整文件）
            continue

        lines = _read_lines(file_path)
        if not lines:
            continue

        for rng in ranges:
            start = rng.get("start_line")
            end = rng.get("end_line", start)
            if start is None:
                continue
            label = rng.get("label", rng.get("name", ""))
            content = _extract_snippet(lines, start, end)
            if content.strip():
                snippets.append({
                    "path": file_path_str,
                    "lines": f"{start}-{end}",
                    "content": content,
                    "label": label,
                })

    return {
        "page_id": page_id,
        "snippets": snippets,
    }


def extract_all_snippets(project_dir: Path) -> Dict[str, str]:
    """为 generation-plan 中所有页面提取源码片段。

    Returns:
        {page_id: output_file_path} 映射
    """
    plan_path = cache_path(project_dir, "generation-plan.json")
    if not plan_path.exists():
        raise FileNotFoundError(f"generation-plan.json 不存在：{plan_path}")

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    pages = plan.get("pages", [])

    snippets_dir = cache_path(project_dir, "snippets")
    snippets_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, str] = {}

    for page in pages:
        page_id = page.get("page_id", "")
        source_files = page.get("source_files", [])
        if not page_id or not source_files:
            continue

        # 仅处理有 source_files 的页面（overview 等无源码页面跳过）
        page_snippets = extract_snippets_for_page(page_id, source_files, project_dir)
        if not page_snippets["snippets"]:
            continue

        # 安全文件名
        safe_id = page_id.replace(":", "_").replace("/", "_")
        out_path = snippets_dir / f"{safe_id}.json"
        out_path.write_text(
            json.dumps(page_snippets, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        result[page_id] = str(out_path)

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_source_snippets.py <project_dir>", file=sys.stderr)
        sys.exit(1)

    project = Path(sys.argv[1])
    results = extract_all_snippets(project)
    print(f"已为 {len(results)} 个页面提取源码片段")
    for page_id, path in results.items():
        print(f"  {page_id} -> {path}")
