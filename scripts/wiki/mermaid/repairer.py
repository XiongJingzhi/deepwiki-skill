"""repairer.py - AI 修复辅助：构建 Prompt、生成错误报告、应用 AI 修复结果。

本模块不直接调用 LLM。它是 skill 工作流的"脚手架"：
  1. build_prompt()       → 生成供 agent 投喂给 AI 的修复提示词
  2. write_error_report() → 将校验失败的块序列化为 mermaid-errors.json
  3. apply_fix()          → 接收 agent 回传的修复结果，写回 Markdown 文件

工作流：
    python scripts/postprocess.py mermaid $DEEPWIKI --validate
    # agent 读取 state/mermaid-errors.json，对每个 block 调用 AI 修复，然后：
    python scripts/postprocess.py mermaid $DEEPWIKI --apply-fix <block_id> --content <fixed_text>
"""

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .extractor import MermaidBlock
from .validator import ValidationResult


# ── Prompt 构建 ──

_SYSTEM_PROMPT = """\
你是 Mermaid 图表语法专家。请修复下方错误的 Mermaid 图表，使其能通过 mmdc 语法校验。

修复规则：
1. 保留图表的语义和结构，只修改语法错误。
2. 节点 ID 只能包含字母、数字、下划线、连字符；含中文/特殊字符的 ID 需用双引号包裹，或替换为安全 ID。
3. 节点标签含空格/中文时，用双引号包裹（如 A["中文标签"]）。
4. 边标签含特殊字符时，用双引号包裹（如 A -->|"标签"| B）。
5. classDiagram 中泛型类型用 <T> 表示，不用 ~T~。
6. sequenceDiagram participant 含空格时加引号。
7. 不要添加多余注释或解释，只输出修复后的 mermaid 代码块。

输出格式（严格遵守）：
```mermaid
<修复后的图表代码>
```
"""


def build_prompt(block: MermaidBlock, validation_result: ValidationResult) -> str:
    """构建供 agent 投喂给 AI 的修复提示词。

    Args:
        block:             待修复的 MermaidBlock。
        validation_result: 对应的校验失败结果。

    Returns:
        完整的提示词字符串（system + user 合并为单段）。
    """
    error_section = ""
    if validation_result.error_msg:
        error_section = f"\n**mmdc 错误信息：**\n```\n{validation_result.error_msg}\n```\n"
        if validation_result.error_lines:
            lines_str = ', '.join(str(l) for l in validation_result.error_lines)
            error_section += f"**出错行号：** {lines_str}\n"

    original_lines = block.text.strip().split('\n')
    numbered = '\n'.join(f'{i+1:3d} | {line}' for i, line in enumerate(original_lines))

    return (
        f"{_SYSTEM_PROMPT}\n"
        f"---\n"
        f"**图表类型：** {block.diagram_type}\n"
        f"**Block ID：** {block.block_id}\n"
        f"{error_section}\n"
        f"**原始图表（带行号）：**\n"
        f"```\n{numbered}\n```\n"
    )


# ── 错误报告 ──

def write_error_report(
    failed: List[Dict],
    report_path: Path,
) -> None:
    """将校验失败的块信息写入 mermaid-errors.json。

    Args:
        failed:      [{"block": MermaidBlock, "result": ValidationResult, "prompt": str}, ...]
        report_path: 输出路径，通常为 .deepwiki/state/mermaid-errors.json。
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    for item in failed:
        block: MermaidBlock = item["block"]
        result: ValidationResult = item["result"]
        prompt: str = item.get("prompt", build_prompt(block, result))
        entries.append({
            "block_id": block.block_id,
            "diagram_type": block.diagram_type,
            "error_msg": result.error_msg,
            "error_lines": result.error_lines,
            "original_text": block.text,
            "prompt": prompt,
            "status": "pending",   # pending | fixed | failed
            "retries": 0,
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_failed": len(entries),
        "blocks": entries,
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


def read_error_report(report_path: Path) -> dict:
    """读取 mermaid-errors.json。"""
    return json.loads(report_path.read_text(encoding='utf-8'))


# ── 应用 AI 修复结果 ──

def apply_fix(
    block_id: str,
    fixed_text: str,
    report_path: Path,
    wiki_dir: Path,
) -> bool:
    """将 agent 提供的 AI 修复结果写回对应 Markdown 文件。

    Args:
        block_id:    目标块 ID，格式 "<file_stem>:<index>"。
        fixed_text:  AI 修复后的 mermaid 图表文本（可含或不含 ```mermaid 围栏）。
        report_path: mermaid-errors.json 路径（用于更新状态）。
        wiki_dir:    wiki/ 目录路径（用于定位 .md 文件）。

    Returns:
        True = 写回成功，False = block_id 未找到或文件不存在。
    """
    # 剥离围栏（agent 可能附带）
    fixed_text = _strip_fence(fixed_text)

    # 更新 report
    report = read_error_report(report_path)
    entry = next((e for e in report["blocks"] if e["block_id"] == block_id), None)
    if entry is None:
        return False

    # 定位 .md 文件
    file_stem, idx_str = block_id.rsplit(':', 1)
    md_candidates = list(wiki_dir.rglob(f"{file_stem}.md"))
    if not md_candidates:
        entry["status"] = "failed"
        entry["error_msg"] = f"file not found: {file_stem}.md"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        return False

    md_file = md_candidates[0]
    content = md_file.read_text(encoding='utf-8')

    # 定位并替换对应块（按顺序索引定位）
    from .extractor import extract_mermaid_blocks, _MERMAID_BLOCK_RE  # noqa: PLC0415
    blocks_in_file = list(_MERMAID_BLOCK_RE.finditer(content))
    try:
        idx = int(idx_str)
        target_match = blocks_in_file[idx]
    except (ValueError, IndexError):
        entry["status"] = "failed"
        entry["error_msg"] = f"block index {idx_str} out of range in {file_stem}.md"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        return False

    new_content = (
        content[:target_match.start()]
        + f'```mermaid\n{fixed_text}```'
        + content[target_match.end():]
    )
    md_file.write_text(new_content, encoding='utf-8')

    # 更新 report 状态
    entry["status"] = "fixed"
    entry["fixed_text"] = fixed_text
    entry["retries"] = entry.get("retries", 0) + 1
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return True


def _strip_fence(text: str) -> str:
    """剥离 ```mermaid ... ``` 围栏，保留内部文本。"""
    text = text.strip()
    m = re.match(r'^```mermaid\s*\n([\s\S]*?)```\s*$', text)
    if m:
        return m.group(1)
    return text
