"""orchestrator.py - 编排 Mermaid 修复整体流程。

两阶段流程：
  阶段 1（正则修复）：扫描所有 .md → 提取块 → 应用 fixers → 写回文件
  阶段 2（AI 修复）：调用 mmdc 校验 → 失败块写入 mermaid-errors.json
                    agent 读取报告 → 驱动 AI 修复 → apply-fix 写回

公共接口：
    run_regex_pass(wiki_dir, dry_run)  -> List[dict]         # 阶段 1
    run_validate_pass(wiki_dir)        -> dict                # 阶段 2 前半（产出 error report）
    run_apply_fix(block_id, fixed_text, wiki_dir) -> bool    # 阶段 2 后半（写回单块）
    run(wiki_dir, dry_run)             -> List[dict]          # 兼容旧接口（仅阶段 1）
"""

from pathlib import Path
from typing import List, Optional

from .extractor import extract_and_fix_file, extract_mermaid_blocks
from .repairer import apply_fix, build_prompt, write_error_report
from .validator import validate_blocks


# ─────────────────────────────────────────────
# 阶段 1：正则修复
# ─────────────────────────────────────────────

def run_regex_pass(wiki_dir: str | Path, dry_run: bool = False) -> List[dict]:
    """扫描 wiki_dir 下所有 .md 文件，提取 mermaid 块并应用正则修复。

    Args:
        wiki_dir: .deepwiki/ 目录路径，或其下的 wiki/ 子目录。
        dry_run:  True = 仅统计，不写入文件。

    Returns:
        每个处理文件的结果字典列表：
        [{"file", "blocks_fixed", "total_fixes", "changes_made"}, ...]
    """
    wiki_path = _resolve_wiki_path(wiki_dir)
    results = []
    for md_file in wiki_path.rglob("*.md"):
        result = extract_and_fix_file(md_file, dry_run=dry_run)
        results.append(result)
    return results


# ─────────────────────────────────────────────
# 阶段 2 前半：校验并生成错误报告
# ─────────────────────────────────────────────

def run_validate_pass(wiki_dir: str | Path) -> dict:
    """校验所有 .md 中的 mermaid 块，将失败块写入 mermaid-errors.json。

    Args:
        wiki_dir: .deepwiki/ 目录路径。

    Returns:
        {
          "total_blocks": int,
          "failed": int,
          "skipped": int,   # mmdc 不可用时所有块均 skipped
          "report_path": str | None,
        }
    """
    deepwiki_path = Path(wiki_dir)
    wiki_path = _resolve_wiki_path(wiki_dir)
    report_path = deepwiki_path / "state" / "mermaid-errors.json"

    all_failed = []
    total_blocks = 0
    total_skipped = 0

    for md_file in wiki_path.rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception:
            continue

        file_stem = md_file.stem
        blocks = extract_mermaid_blocks(content, file_stem)
        if not blocks:
            continue

        total_blocks += len(blocks)
        results = validate_blocks(blocks)

        for block, result in zip(blocks, results):
            if result.skipped:
                total_skipped += 1
            elif not result.ok:
                prompt = build_prompt(block, result)
                all_failed.append({"block": block, "result": result, "prompt": prompt})

    written_path = None
    if all_failed:
        write_error_report(all_failed, report_path)
        written_path = str(report_path)

    return {
        "total_blocks": total_blocks,
        "failed": len(all_failed),
        "skipped": total_skipped,
        "report_path": written_path,
    }


# ─────────────────────────────────────────────
# 阶段 2 后半：应用 AI 修复结果（单块）
# ─────────────────────────────────────────────

def run_apply_fix(
    block_id: str,
    fixed_text: str,
    wiki_dir: str | Path,
) -> bool:
    """将 agent 提供的 AI 修复结果写回对应 Markdown 文件。

    Args:
        block_id:   目标块 ID，格式 "<file_stem>:<index>"。
        fixed_text: 修复后的 mermaid 文本（可含或不含 ```mermaid 围栏）。
        wiki_dir:   .deepwiki/ 目录路径。

    Returns:
        True = 写回成功。
    """
    deepwiki_path = Path(wiki_dir)
    wiki_path = _resolve_wiki_path(wiki_dir)
    report_path = deepwiki_path / "state" / "mermaid-errors.json"

    if not report_path.exists():
        return False

    return apply_fix(block_id, fixed_text, report_path, wiki_path)


# ─────────────────────────────────────────────
# 兼容旧接口
# ─────────────────────────────────────────────

def run(wiki_dir: str | Path, dry_run: bool = False) -> List[dict]:
    """兼容旧版 fix_all_mermaid 接口（仅运行阶段 1 正则修复）。"""
    return run_regex_pass(wiki_dir, dry_run=dry_run)


# ─────────────────────────────────────────────
# 内部工具
# ─────────────────────────────────────────────

def _resolve_wiki_path(wiki_dir: str | Path) -> Path:
    """解析 wiki 目录路径：优先使用 <dir>/wiki/，否则使用 <dir> 本身。"""
    p = Path(wiki_dir)
    wiki_sub = p / "wiki"
    return wiki_sub if wiki_sub.exists() else p
