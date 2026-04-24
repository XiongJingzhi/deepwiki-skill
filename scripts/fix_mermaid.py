#!/usr/bin/env python3
"""
Mermaid 语法修复脚本

扫描 wiki/ 目录下所有 .md 文件中的 Mermaid 图表块，
自动修复常见的语法问题：
- Node IDs 包含中文字符或特殊字符 -> 引用包裹
- 标签包含空格或特殊字符 -> 引号包裹
- classDiagram 语法错误（缺失引号、错误箭头）
- sequenceDiagram 语法错误
- 重复的节点 ID（重命名为 ID_2, ID_3 等）

用法:
    python scripts/fix_mermaid.py <项目目录>/.deepwiki
    python scripts/fix_mermaid.py <项目目录>/.deepwiki --dry-run
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timezone


# ── Mermaid block extraction ──

_MERMAID_BLOCK_RE = re.compile(
    r'```mermaid\s*\n([\s\S]*?)```',
    re.MULTILINE,
)


def extract_mermaid_blocks(content: str) -> List[Tuple[int, int, str]]:
    """提取 (start_pos, end_pos, diagram_text) 列表。"""
    return [(m.start(), m.end(), m.group(1)) for m in _MERMAID_BLOCK_RE.finditer(content)]


# ── 辅助函数 ──

_SAFE_ID_RE = re.compile(r'^[A-Za-z_]\w*$')


def _needs_quoting(text: str) -> bool:
    """检查 Mermaid ID 或标签是否需要引号包裹。"""
    if not text:
        return False
    return not _SAFE_ID_RE.match(text)


def _quote(text: str) -> str:
    """用双引号包裹文本。"""
    return f'"{text}"'


# ── 修复器 ──

def fix_flowchart(text: str) -> Tuple[str, int]:
    """修复 flowchart/flowchart LR/TB 图表。

    修复：
    - 标签含空格/中文未加引号: A[数据处理] -> A["数据处理"]
    - 边标签含特殊字符未加引号: A -->|error handler| B -> A -->|"error handler"| B
    """
    fix_count = 0

    def fix_node_def(m):
        nonlocal fix_count
        node_id = m.group(1)
        label = m.group(2)
        if _needs_quoting(label) and not (label.startswith('"') or label.startswith("'")):
            fix_count += 1
            return f'{node_id}[{_quote(label)}]'
        return m.group(0)

    # 修复节点定义：ID[label] -> ID["label"]
    text = re.sub(r'(\w+)\[([^\]]+)\]', fix_node_def, text)

    # 修复边标签：A -->|label| B -> A -->|"label"| B
    def fix_edge_label(m):
        nonlocal fix_count
        label = m.group(1)
        if _needs_quoting(label) and not label.startswith('"'):
            fix_count += 1
            return f'|{_quote(label)}|'
        return m.group(0)

    text = re.sub(r'\|([^|]+)\|', fix_edge_label, text)

    return text, fix_count


def fix_class_diagram(text: str) -> Tuple[str, int]:
    """修复 classDiagram 语法错误。

    修复：
    - 类名含特殊字符需要引号
    - 成员名含空格需要引号
    - 关系标签缺少引号
    """
    fix_count = 0

    # 修复类定义
    def fix_class_def(m):
        nonlocal fix_count
        indent = m.group(1)
        class_name = m.group(2)
        if _needs_quoting(class_name) and not class_name.startswith('"'):
            fix_count += 1
            return f'{indent}class {_quote(class_name)}'
        return m.group(0)

    text = re.sub(r'^(\s*)class\s+(\S+)\s*\{', fix_class_def, text, flags=re.MULTILINE)

    # 修复成员名含空格: +method name() -> +"method name"()
    def fix_member(m):
        nonlocal fix_count
        visibility = m.group(1)
        member = m.group(2)
        rest = m.group(3)
        if ' ' in member and not member.startswith('"'):
            fix_count += 1
            return f'{visibility}{_quote(member)}{rest}'
        return m.group(0)

    text = re.sub(
        r'^(\s*[+\-~#])(\w[\w\s]*\w)(\s*[:(])',
        fix_member,
        text,
        flags=re.MULTILINE,
    )

    # 修复关系标签: ClassA --|> ClassB : extends -> ClassA --|> ClassB : "extends"
    _CLASS_REL_RE = re.compile(r'(?:--|__|\.\.)(?:>|<|\|>|<\|)*\s+\w+\s*:\s*([^\n]+)$', re.MULTILINE)

    def fix_rel_label(m):
        nonlocal fix_count
        label = m.group(1)
        if _needs_quoting(label) and not label.startswith('"'):
            fix_count += 1
            return f' : {_quote(label)}'
        return m.group(0)

    text = _CLASS_REL_RE.sub(fix_rel_label, text)

    return text, fix_count


def fix_sequence_diagram(text: str) -> Tuple[str, int]:
    """修复 sequenceDiagram 语法错误。

    修复：
    - participant 别名含空格未加引号
    - 消息标签含空格未加引号
    """
    fix_count = 0

    # 修复 participant: Participant Name as P -> Participant "Name" as P
    def fix_participant(m):
        nonlocal fix_count
        keyword = m.group(1)
        alias = m.group(2)
        name = m.group(3)
        if _needs_quoting(name) and not name.startswith('"'):
            fix_count += 1
            return f'{keyword} {alias} as {_quote(name)}'
        return m.group(0)

    text = re.sub(
        r'^(participant|actor)\s+(\S+)\s+as\s+(.+)$',
        fix_participant,
        text,
        flags=re.MULTILINE,
    )

    # 修复消息标签: A->>B:send request -> A->>B:"send request"
    def fix_message(m):
        nonlocal fix_count
        prefix = m.group(1)
        label = m.group(2)
        if _needs_quoting(label) and not label.startswith('"'):
            fix_count += 1
            return f'{prefix}:{_quote(label)}'
        return m.group(0)

    text = re.sub(
        r'([\w-]+\s*(?:->>|-->>|--\|>|<<--|<<->>|--)\s*[\w-]+)\s*:([^\n]+)',
        fix_message,
        text,
    )

    return text, fix_count


def fix_duplicate_node_ids(text: str) -> Tuple[str, int]:
    """检测并修复重复的节点 ID 定义，重命名为 ID_2, ID_3 等。"""
    fix_count = 0

    id_defs = re.findall(r'(\w+)\[([^\]]*)\]', text)
    seen: Dict[str, str] = {}
    renames: Dict[str, str] = {}

    for node_id, label in id_defs:
        if node_id in seen and seen[node_id] != label:
            counter = 2
            while f"{node_id}_{counter}" in seen:
                counter += 1
            new_id = f"{node_id}_{counter}"
            renames[node_id] = new_id
            fix_count += 1
            text = text.replace(f'{node_id}[{label}]', f'{new_id}[{label}]', 1)
            seen[new_id] = label
        else:
            seen[node_id] = label

    for old_id, new_id in renames.items():
        text = re.sub(r'\b' + re.escape(old_id) + r'\b(?![\["\'\w])', new_id, text)

    return text, fix_count


# ── 主修复流水线 ──

def fix_mermaid_block(diagram_text: str) -> Tuple[str, int]:
    """对单个 Mermaid 图表块应用所有适用的修复。

    Returns: (fixed_text, total_fix_count)
    """
    total_fixes = 0
    first_line = diagram_text.strip().split('\n')[0].strip()

    if first_line.startswith('classDiagram'):
        text, fixes = fix_class_diagram(diagram_text)
        total_fixes += fixes
    elif first_line.startswith('sequenceDiagram'):
        text, fixes = fix_sequence_diagram(diagram_text)
        total_fixes += fixes
    elif any(first_line.startswith(kw) for kw in ['flowchart', 'graph']):
        text, fixes = fix_flowchart(diagram_text)
        total_fixes += fixes
        text2, fixes2 = fix_duplicate_node_ids(text)
        total_fixes += fixes2
        text = text2
    else:
        text = diagram_text

    return text, total_fixes


def fix_mermaid_in_file(file_path: Path, dry_run: bool = False) -> Dict[str, any]:
    """修复单个 markdown 文件中的所有 Mermaid 块。

    Returns: {file, blocks_fixed, total_fixes, changes_made}
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return {"file": str(file_path), "error": "cannot read", "blocks_fixed": 0, "total_fixes": 0}

    blocks = extract_mermaid_blocks(content)
    if not blocks:
        return {"file": str(file_path), "blocks_fixed": 0, "total_fixes": 0, "changes_made": False}

    total_fixes = 0
    blocks_fixed = 0
    new_content = content

    # 反向处理以保持位置
    for start, end, diagram_text in reversed(blocks):
        fixed_text, fixes = fix_mermaid_block(diagram_text)
        if fixes > 0:
            total_fixes += fixes
            blocks_fixed += 1
            if not dry_run:
                new_content = new_content[:start] + f'```mermaid\n{fixed_text}```' + new_content[end:]

    changes_made = False
    if not dry_run and total_fixes > 0:
        file_path.write_text(new_content, encoding='utf-8')
        changes_made = True

    return {
        "file": str(file_path),
        "blocks_fixed": blocks_fixed,
        "total_fixes": total_fixes,
        "changes_made": changes_made,
    }


def fix_all_mermaid(wiki_dir: str, dry_run: bool = False) -> List[Dict[str, any]]:
    """修复 wiki_dir/wiki/ 下所有 .md 文件中的 Mermaid 图表。"""
    wiki_path = Path(wiki_dir)
    if not wiki_path.exists():
        return [{"error": f"Wiki directory not found: {wiki_dir}"}]

    wiki_md = wiki_path / "wiki" if (wiki_path / "wiki").exists() else wiki_path
    results = []

    for md_file in wiki_md.rglob("*.md"):
        results.append(fix_mermaid_in_file(md_file, dry_run=dry_run))

    return results


def main():
    parser = argparse.ArgumentParser(
        description="DeepWiki Mermaid 语法修复工具",
    )
    parser.add_argument("wiki_path", help="Wiki 目录路径 (.deepwiki)")
    parser.add_argument("--dry-run", action="store_true", help="仅报告问题，不修改文件")
    parser.add_argument("--json", metavar="FILE", help="将结果保存为 JSON")

    args = parser.parse_args()
    results = fix_all_mermaid(args.wiki_path, dry_run=args.dry_run)

    total_files = len(results)
    total_blocks = sum(r.get("blocks_fixed", 0) for r in results)
    total_fixes = sum(r.get("total_fixes", 0) for r in results)

    print(f"Mermaid 修复: {total_fixes} 处修复 ({total_blocks} 个图表块, {total_files} 个文件)")

    for r in results:
        if r.get("total_fixes", 0) > 0:
            mode = "DRY-RUN" if args.dry_run else "FIXED"
            print(f"  [{mode}] {r['file']}: {r['total_fixes']} fixes in {r['blocks_fixed']} blocks")

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump({
                "check_time": datetime.now(timezone.utc).isoformat(),
                "total_fixes": total_fixes,
                "files_affected": [r for r in results if r.get("total_fixes", 0) > 0],
            }, f, indent=2, ensure_ascii=False)

    return 0 if total_fixes == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
