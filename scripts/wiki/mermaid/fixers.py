"""fixers.py - 正则修复器：所有针对各类 Mermaid 图表的正则修复函数。

公共接口：
    fix_mermaid_block(diagram_text) -> (fixed_text, fix_count)
"""

import re
from typing import Dict, List, Tuple


# ── 辅助工具 ──

_SAFE_ID_RE = re.compile(r'^[A-Za-z_][\w-]*$')
_FLOW_NODE_ID = r'(?<![\w-])([A-Za-z_][\w-]*)'


def _needs_quoting(text: str) -> bool:
    """检查 Mermaid ID 或标签是否需要引号包裹。"""
    if not text:
        return False
    return not _SAFE_ID_RE.match(text)


def _quote(text: str) -> str:
    """用双引号包裹文本。"""
    return f'"{text}"'


# ── flowchart / graph ──

def fix_flowchart(text: str) -> Tuple[str, int]:
    """修复 flowchart/graph 图表。

    修复：
    - 标签含空格/中文未加引号: A[数据处理] -> A["数据处理"]
    - 边标签含特殊字符未加引号: A -->|error handler| B -> A -->|"error handler"| B
    - 双引号标签内部嵌套双引号: A["fn("x")"] -> A["fn('x')"]
    """
    fix_count = 0

    def quote_label(label: str) -> str:
        nonlocal fix_count
        unwrapped_label = label.lstrip('([{/<\\')
        if _needs_quoting(label) and not (unwrapped_label.startswith('"') or unwrapped_label.startswith("'")):
            fix_count += 1
            return _quote(label)
        return label

    def fix_node_shape(pattern: str, formatter):
        def repl(m):
            node_id = m.group(1)
            label = m.group(2)
            quoted_label = quote_label(label)
            if quoted_label == label:
                return m.group(0)
            return formatter(node_id, quoted_label)
        return re.sub(pattern, repl, text)

    shape_patterns = [
        (rf'{_FLOW_NODE_ID}\[\(([^\]\n]+?)\)\]', lambda node_id, label: f'{node_id}[({label})]'),
        (rf'{_FLOW_NODE_ID}\(([^)\n]+?)\)', lambda node_id, label: f'{node_id}({label})'),
        (rf'{_FLOW_NODE_ID}\{{([^}}\n]+?)\}}', lambda node_id, label: f'{node_id}{{{label}}}'),
        (rf'{_FLOW_NODE_ID}\[([^\]\n]+?)\]', lambda node_id, label: f'{node_id}[{label}]'),
    ]
    for pattern, formatter in shape_patterns:
        text = fix_node_shape(pattern, formatter)

    def fix_edge_label(m):
        nonlocal fix_count
        label = m.group(1)
        if _needs_quoting(label) and not label.startswith('"'):
            fix_count += 1
            return f'|{_quote(label)}|'
        return m.group(0)

    text = re.sub(r'\|([^|]+)\|', fix_edge_label, text)

    # 修复双引号标签内部嵌套双引号 -> 替换为单引号（状态机扫描）
    _CLOSE_CH = {'[': ']', '{': '}', '(': ')'}
    _NODE_START = re.compile(r'([\w][\w-]*)(\[|\{|\()')

    result_parts: List[str] = []
    pos = 0
    while pos < len(text):
        m = _NODE_START.search(text, pos)
        if not m:
            result_parts.append(text[pos:])
            break

        result_parts.append(text[pos:m.start()])
        node_id = m.group(1)
        open_ch = m.group(2)
        close_ch = _CLOSE_CH[open_ch]

        depth = 1
        j = m.end()
        while j < len(text) and depth > 0:
            if text[j] == open_ch:
                depth += 1
            elif text[j] == close_ch:
                depth -= 1
            j += 1

        block_inner = text[m.end():j - 1]

        if (block_inner.startswith('"') and block_inner.endswith('"')
                and block_inner.count('"') > 2):
            inner_content = block_inner[1:-1]
            if '"' in inner_content:
                fix_count += 1
                block_inner = f'"{inner_content.replace(chr(34), chr(39))}"'

        result_parts.append(f'{node_id}{open_ch}{block_inner}{close_ch}')
        pos = j

    text = ''.join(result_parts)
    return text, fix_count


# ── classDiagram ──

def fix_class_diagram(text: str) -> Tuple[str, int]:
    """修复 classDiagram 语法错误。"""
    fix_count = 0
    raw_generic_names: List[str] = []

    def _fix_tilde_generic(raw_name: str) -> Tuple[str, str]:
        parts = [p for p in raw_name.split('~') if p]
        if len(parts) > 1:
            all_params: List[str] = []
            for p in parts[1:]:
                all_params.extend(param.strip() for param in p.split(',') if param.strip())
            display_name = parts[0] + '<' + ', '.join(all_params) + '>'
        else:
            display_name = parts[0]
        base_id = parts[0]
        if not _SAFE_ID_RE.match(base_id):
            base_id = re.sub(r'[^\w]', '_', base_id)
        return display_name, base_id

    def fix_generic_class_def(m):
        nonlocal fix_count
        indent = m.group(1)
        raw_name = m.group(2)
        brace = m.group(3) or ''
        if '~' in raw_name:
            display_name, base_id = _fix_tilde_generic(raw_name)
            raw_generic_names.append(raw_name)
            fix_count += 1
            return f'{indent}class {_quote(display_name)} as {base_id} {brace}'.rstrip()
        return m.group(0)

    text = re.sub(
        r'^(\s*)class\s+"([^"]+)"\s*(\{?)\s*$',
        fix_generic_class_def,
        text,
        flags=re.MULTILINE,
    )

    alias_map: Dict[str, str] = {}
    for m in re.finditer(r'^\s*class\s+"([^"]+)"\s+as\s+(\w+)', text, re.MULTILINE):
        alias_map[m.group(1)] = m.group(2)
    raw_alias_map: Dict[str, str] = {}
    for raw_name in raw_generic_names:
        display_name, base_id = _fix_tilde_generic(raw_name)
        raw_alias_map[raw_name] = base_id

    def fix_member_type(m):
        nonlocal fix_count
        prefix, tilde_type, suffix = m.group(1), m.group(2), m.group(3)
        if '~' in tilde_type:
            display_name, _ = _fix_tilde_generic(tilde_type)
            fix_count += 1
            return f'{prefix}{display_name}{suffix}'
        return m.group(0)

    text = re.sub(r'^(\s*[+\-~#][^:]*?:\s*)(\w[\w]*~[\w,~]+)(.*)$', fix_member_type, text, flags=re.MULTILINE)

    def fix_member_type_nocolon(m):
        nonlocal fix_count
        prefix, tilde_type, rest = m.group(1), m.group(2), m.group(3)
        if '~' in tilde_type:
            display_name, _ = _fix_tilde_generic(tilde_type)
            fix_count += 1
            return f'{prefix}{display_name}{rest}'
        return m.group(0)

    text = re.sub(r'^(\s*[+\-~#])(\w+~[\w, ~]+?~)(\s+\w.*)$', fix_member_type_nocolon, text, flags=re.MULTILINE)

    def fix_return_type_generic(m):
        nonlocal fix_count
        prefix, tilde_type = m.group(1), m.group(2)
        if '~' in tilde_type:
            display_name, _ = _fix_tilde_generic(tilde_type)
            fix_count += 1
            return f'{prefix}{display_name}'
        return m.group(0)

    text = re.sub(r'^(\s*[+\-~#]\w+\([^)]*\)\s+)(\w+~[\w, ~]+?~)(\s*)$', fix_return_type_generic, text, flags=re.MULTILINE)

    def fix_class_def(m):
        nonlocal fix_count
        indent, class_name = m.group(1), m.group(2)
        if _needs_quoting(class_name) and not class_name.startswith('"'):
            fix_count += 1
            return f'{indent}class {_quote(class_name)}'
        return m.group(0)

    text = re.sub(r'^(\s*)class\s+(\S+)\s*\{', fix_class_def, text, flags=re.MULTILINE)

    def fix_member(m):
        nonlocal fix_count
        visibility, member, rest = m.group(1), m.group(2), m.group(3)
        if ' ' in member and not member.startswith('"'):
            fix_count += 1
            return f'{visibility}{_quote(member)}{rest}'
        return m.group(0)

    text = re.sub(r'^(\s*[+\-~#])(\w[\w\s]*\w)(\s*[:(])', fix_member, text, flags=re.MULTILINE)

    _CLASS_REL_RE = re.compile(r'(?:--|__|\.\.)(?:>|<|\|>|<\|)*\s+(\S+)\s*:\s*([^\n]+)$', re.MULTILINE)

    def fix_rel_label(m):
        nonlocal fix_count
        target, label = m.group(1), m.group(2)
        resolved = alias_map.get(target) or raw_alias_map.get(target)
        if resolved:
            fix_count += 1
            return f' {resolved} : {_quote(label)}' if _needs_quoting(label) else f' {resolved} : {label}'
        if _needs_quoting(label) and not label.startswith('"'):
            fix_count += 1
            return f' : {_quote(label)}'
        return m.group(0)

    text = _CLASS_REL_RE.sub(fix_rel_label, text)

    def fix_standalone_label(m):
        nonlocal fix_count
        indent, class_ref, label = m.group(1), m.group(2), m.group(3)
        resolved = alias_map.get(class_ref) or raw_alias_map.get(class_ref)
        if resolved and resolved != class_ref:
            fix_count += 1
            return f'{indent}{resolved} : {_quote(label)}'
        return m.group(0)

    text = re.sub(r'^(\s*)(\S+)\s*:\s*"([^"]+)"\s*$', fix_standalone_label, text, flags=re.MULTILINE)

    return text, fix_count


# ── sequenceDiagram ──

def fix_sequence_diagram(text: str) -> Tuple[str, int]:
    """修复 sequenceDiagram：participant 别名和消息标签加引号。"""
    fix_count = 0

    def fix_participant(m):
        nonlocal fix_count
        keyword, alias, name = m.group(1), m.group(2), m.group(3)
        if _needs_quoting(name) and not name.startswith('"'):
            fix_count += 1
            return f'{keyword} {alias} as {_quote(name)}'
        return m.group(0)

    text = re.sub(r'^(participant|actor)\s+(\S+)\s+as\s+(.+)$', fix_participant, text, flags=re.MULTILINE)

    def fix_message(m):
        nonlocal fix_count
        prefix, label = m.group(1), m.group(2)
        if _needs_quoting(label) and not label.startswith('"'):
            fix_count += 1
            return f'{prefix}:{_quote(label)}'
        return m.group(0)

    text = re.sub(r'([\w-]+\s*(?:->>|-->>|--\|>|<<--|<<->>|--)\s*[\w-]+)\s*:([^\n]+)', fix_message, text)

    return text, fix_count


# ── 重复节点 ID ──

def fix_duplicate_node_ids(text: str) -> Tuple[str, int]:
    """检测并修复重复节点 ID，重命名为 ID_2, ID_3 等。"""
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


# ── stateDiagram ──

def fix_state_diagram(text: str) -> Tuple[str, int]:
    """修复 stateDiagram / stateDiagram-v2（目前透传，预留扩展）。"""
    return text, 0


# ── erDiagram ──

def fix_er_diagram(text: str) -> Tuple[str, int]:
    """修复 erDiagram：非安全 entity 名替换为安全 ID。"""
    fix_count = 0
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith(' ') and not stripped.startswith('{') \
                and not stripped.startswith('}') and not stripped.startswith('||'):
            match = re.match(r'^(\S+)(?:\s*\{)?', stripped)
            if match:
                entity_name = match.group(1)
                if not _SAFE_ID_RE.match(entity_name):
                    safe_name = re.sub(r'[^\w]', '_', entity_name)
                    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
                    if safe_name and safe_name != entity_name:
                        line = line.replace(entity_name, safe_name, 1)
                        fix_count += 1
        result.append(line)
    return '\n'.join(result), fix_count


# ── 主修复分发入口 ──

def fix_mermaid_block(diagram_text: str) -> Tuple[str, int]:
    """对单个 Mermaid 图表块应用所有适用的正则修复。

    Args:
        diagram_text: 图表原始文本（不含 ```mermaid 围栏）。

    Returns:
        (fixed_text, total_fix_count)
    """
    total_fixes = 0
    first_line = diagram_text.strip().split('\n')[0].strip()

    if first_line.startswith('classDiagram'):
        text, fixes = fix_class_diagram(diagram_text)
        total_fixes += fixes
    elif first_line.startswith('sequenceDiagram'):
        text, fixes = fix_sequence_diagram(diagram_text)
        total_fixes += fixes
    elif first_line.startswith('stateDiagram'):
        text, fixes = fix_state_diagram(diagram_text)
        total_fixes += fixes
    elif first_line.startswith('erDiagram'):
        text, fixes = fix_er_diagram(diagram_text)
        total_fixes += fixes
    elif any(first_line.startswith(kw) for kw in ['flowchart', 'graph']):
        text, fixes = fix_flowchart(diagram_text)
        total_fixes += fixes
        text, fixes2 = fix_duplicate_node_ids(text)
        total_fixes += fixes2
    else:
        text = diagram_text

    return text, total_fixes
