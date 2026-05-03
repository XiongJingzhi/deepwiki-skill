"""extractor.py - 从 Markdown 中提取 mermaid 块并应用正则修复。

公共接口：
    extract_mermaid_blocks(content)  -> List[MermaidBlock]
    extract_and_fix(content)         -> (new_content, List[MermaidBlock], total_fixes)
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from .fixers import fix_mermaid_block


_MERMAID_BLOCK_RE = re.compile(
    r'```mermaid\s*\n([\s\S]*?)```',
    re.MULTILINE,
)

_DIAGRAM_TYPE_RE = re.compile(
    r'^(classDiagram|sequenceDiagram|stateDiagram(?:-v2)?|erDiagram|flowchart|graph)',
)


@dataclass
class MermaidBlock:
    """单个 mermaid 图表块的元数据。"""
    block_id: str          # 唯一标识，格式 "<file_stem>:<index>"
    start: int             # 在原文中的字符起始位置（含 ```mermaid 围栏）
    end: int               # 字符结束位置（含结尾 ```）
    text: str              # diagram 原始文本（不含 ```mermaid 围栏）
    diagram_type: str      # "flowchart" / "classDiagram" / "sequenceDiagram" / ...


def extract_mermaid_blocks(content: str, file_stem: str = "doc") -> List[MermaidBlock]:
    """从 Markdown 文本中提取所有 mermaid 块。

    Args:
        content:   Markdown 全文。
        file_stem: 文件名（不含扩展名），用于生成 block_id。

    Returns:
        MermaidBlock 列表，按出现顺序排列。
    """
    blocks = []
    for idx, m in enumerate(_MERMAID_BLOCK_RE.finditer(content)):
        diagram_text = m.group(1)
        first_line = diagram_text.strip().split('\n')[0].strip()
        type_match = _DIAGRAM_TYPE_RE.match(first_line)
        diagram_type = type_match.group(1) if type_match else "unknown"
        blocks.append(MermaidBlock(
            block_id=f"{file_stem}:{idx}",
            start=m.start(),
            end=m.end(),
            text=diagram_text,
            diagram_type=diagram_type,
        ))
    return blocks


def extract_and_fix(content: str, file_stem: str = "doc") -> Tuple[str, List[MermaidBlock], int]:
    """提取所有 mermaid 块并应用正则修复，返回修复后的完整文本。

    Args:
        content:   Markdown 全文。
        file_stem: 文件名（不含扩展名），用于生成 block_id。

    Returns:
        (new_content, blocks_after_fix, total_fix_count)
        - new_content:      修复后的 Markdown 全文（若无修复则与原文相同）。
        - blocks_after_fix: 修复后的 MermaidBlock 列表（text 已更新）。
        - total_fix_count:  本次正则修复总次数。
    """
    blocks = extract_mermaid_blocks(content, file_stem)
    if not blocks:
        return content, [], 0

    total_fixes = 0
    new_content = content
    updated_blocks: List[MermaidBlock] = []

    # 反向遍历，保持字符位置正确性
    for block in reversed(blocks):
        fixed_text, fixes = fix_mermaid_block(block.text)
        total_fixes += fixes
        updated_block = MermaidBlock(
            block_id=block.block_id,
            start=block.start,
            end=block.end,
            text=fixed_text,
            diagram_type=block.diagram_type,
        )
        updated_blocks.append(updated_block)
        if fixes > 0:
            new_content = (
                new_content[:block.start]
                + f'```mermaid\n{fixed_text}```'
                + new_content[block.end:]
            )

    updated_blocks.reverse()
    return new_content, updated_blocks, total_fixes


def extract_and_fix_file(file_path: Path, dry_run: bool = False) -> dict:
    """修复单个 Markdown 文件中的所有 mermaid 块。

    Args:
        file_path: .md 文件路径。
        dry_run:   若为 True，则只统计，不写入文件。

    Returns:
        {"file", "blocks_fixed", "total_fixes", "changes_made", "blocks"}
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return {"file": str(file_path), "error": "cannot read", "blocks_fixed": 0, "total_fixes": 0}

    file_stem = file_path.stem
    new_content, blocks, total_fixes = extract_and_fix(content, file_stem)

    blocks_fixed = sum(1 for b_orig, b_new in zip(
        extract_mermaid_blocks(content, file_stem), blocks
    ) if b_orig.text != b_new.text)

    changes_made = False
    if not dry_run and total_fixes > 0:
        file_path.write_text(new_content, encoding='utf-8')
        changes_made = True

    return {
        "file": str(file_path),
        "blocks_fixed": blocks_fixed,
        "total_fixes": total_fixes,
        "changes_made": changes_made,
        "blocks": blocks,
    }
