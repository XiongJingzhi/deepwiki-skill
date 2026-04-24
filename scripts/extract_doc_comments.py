#!/usr/bin/env python3
"""
文档提取脚本
从代码文件中提取 JSDoc/TSDoc/DocString/GoDoc/Javadoc 注释
支持: JavaScript/TypeScript, Python, Go, Java/Kotlin, Rust

使用 tree-sitter AST 解析（通过 parsers.py），替代旧的 regex 实现。
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from parsers import get_manager, get_parser_for_ext, get_lang_for_ext


@dataclass
class DocEntry:
    """文档条目"""
    name: str
    type: str  # 'function', 'class', 'method', 'type', 'interface'
    description: str
    params: List[Dict[str, str]]
    returns: Optional[str]
    examples: List[str]
    line_number: int
    file_path: str


# ---------------------------------------------------------------------------
# JSDoc / TSDoc comment text parsing (used by JS/TS and Java/Kotlin)
# ---------------------------------------------------------------------------

def _parse_jsdoc_text(doc_text: str) -> dict:
    """Parse the inner text of a /** ... */ comment block.

    Returns a dict with keys: description, params, returns, examples.
    """
    description_lines = []
    params = []
    returns = None
    examples = []

    for line in doc_text.split('\n'):
        line = line.strip()
        # Strip leading '*' from each line
        if line.startswith('*'):
            line = line[1:]
        line = line.strip()

        if line.startswith('@param'):
            param_match = re.match(r'@param\s+{([^}]+)}\s+(\w+)\s*-?\s*(.*)', line)
            if param_match:
                params.append({
                    'type': param_match.group(1),
                    'name': param_match.group(2),
                    'description': param_match.group(3)
                })
        elif line.startswith('@returns') or line.startswith('@return'):
            return_match = re.match(r'@returns?\s+{([^}]+)}\s*(.*)', line)
            if return_match:
                returns = f"{return_match.group(1)}: {return_match.group(2)}"
        elif line.startswith('@example'):
            examples.append(line[len('@example'):].strip())
        elif line.startswith('@'):
            continue
        elif examples:
            # Append to current example block
            examples[-1] += '\n' + line if examples[-1] else line
        else:
            description_lines.append(line)

    return {
        'description': ' '.join(description_lines).strip(),
        'params': params,
        'returns': returns,
        'examples': examples,
    }


def _parse_javadoc_text(doc_text: str) -> dict:
    """Parse the inner text of a /** ... */ Javadoc block (Java/Kotlin style).

    Returns a dict with keys: description, params, returns, examples.
    """
    description_lines = []
    params = []
    returns = None

    for line in doc_text.split('\n'):
        line = line.strip()
        # Strip leading '*'
        if line.startswith('*'):
            line = line[1:]
        line = line.strip()

        if line.startswith('@param'):
            param_match = re.match(r'@param\s+(\w+)\s+-?\s*(.*)', line)
            if param_match:
                params.append({
                    'name': param_match.group(1),
                    'type': 'any',
                    'description': param_match.group(2)
                })
        elif line.startswith('@return') or line.startswith('@returns'):
            return_match = re.match(r'@returns?\s+(.*)', line)
            if return_match:
                returns = return_match.group(1)
        elif line.startswith('@throws') or line.startswith('@exception'):
            pass  # could extend later
        elif not line.startswith('@'):
            description_lines.append(line)

    return {
        'description': ' '.join(description_lines).strip(),
        'params': params,
        'returns': returns,
        'examples': [],
    }


# ---------------------------------------------------------------------------
# Python docstring parsing
# ---------------------------------------------------------------------------

def _parse_python_docstring(docstring_text: str) -> dict:
    """Parse a Python docstring (Google/NumPy style sections).

    Returns a dict with keys: description, params, returns, examples.
    """
    description_lines = []
    params = []
    returns = None
    examples = []

    current_section = 'description'

    for line in docstring_text.split('\n'):
        stripped = line.strip()

        if stripped in ('Args:', 'Arguments:', 'Parameters:', '参数:', '参数：'):
            current_section = 'params'
            continue
        elif stripped in ('Returns:', 'Return:', '返回:', '返回值：', '返回值:'):
            current_section = 'returns'
            continue
        elif stripped in ('Example:', 'Examples:', '示例:', '示例：'):
            current_section = 'examples'
            continue
        elif stripped.endswith(':') and ':' not in stripped[:-1]:
            current_section = 'other'
            continue

        if current_section == 'description':
            description_lines.append(stripped)
        elif current_section == 'params':
            param_match = re.match(r'(\w+)\s*(?:\(([^)]+)\))?\s*:\s*(.*)', stripped)
            if param_match:
                params.append({
                    'name': param_match.group(1),
                    'type': param_match.group(2) or 'Any',
                    'description': param_match.group(3)
                })
        elif current_section == 'returns':
            if stripped:
                returns = (returns + ' ' + stripped) if returns else stripped
        elif current_section == 'examples':
            examples.append(stripped)

    return {
        'description': ' '.join(description_lines).strip(),
        'params': params,
        'returns': returns,
        'examples': examples,
    }


# ---------------------------------------------------------------------------
# Go doc comment parsing
# ---------------------------------------------------------------------------

def _parse_go_doc_lines(lines: list) -> dict:
    """Parse Go doc comment lines.

    Returns a dict with keys: description, params, returns, examples.
    """
    description_lines = []

    for line in lines:
        if line.startswith('Deprecated:'):
            description_lines.append('[Deprecated] ' + line[len('Deprecated:'):].strip())
        else:
            description_lines.append(line)

    return {
        'description': ' '.join(description_lines).strip(),
        'params': [],
        'returns': None,
        'examples': [],
    }


# ---------------------------------------------------------------------------
# Rust doc comment parsing
# ---------------------------------------------------------------------------

def _parse_rust_doc_lines(lines: list) -> dict:
    """Parse Rust /// doc comment lines (with # section headers).

    Returns a dict with keys: description, params, returns, examples.
    """
    description_lines = []
    examples = []
    params = []
    returns = None

    current_section = 'description'

    for line in lines:
        if line.startswith('# '):
            section_name = line[2:].strip().lower()
            if section_name in ('examples', 'example'):
                current_section = 'examples'
            elif section_name in ('arguments', 'parameters', 'args'):
                current_section = 'params'
            elif section_name in ('returns', 'return'):
                current_section = 'returns'
            elif section_name in ('panics', 'errors', 'safety'):
                description_lines.append(f'[{line[2:].strip()}]')
                current_section = 'description'
            else:
                current_section = 'description'
            continue

        if current_section == 'description':
            description_lines.append(line)
        elif current_section == 'examples':
            examples.append(line)
        elif current_section == 'params':
            param_match = re.match(r'[*\-]?\s*`?(\w+)`?\s*[-:]\s*(.*)', line.strip())
            if param_match and param_match.group(1):
                params.append({
                    'name': param_match.group(1),
                    'type': 'any',
                    'description': param_match.group(2)
                })
        elif current_section == 'returns':
            if line.strip():
                returns = (returns + ' ' + line.strip()) if returns else line.strip()

    return {
        'description': ' '.join(l for l in description_lines if l).strip(),
        'params': params,
        'returns': returns,
        'examples': examples,
    }


# ---------------------------------------------------------------------------
# Node text helpers
# ---------------------------------------------------------------------------

def _node_text(node) -> str:
    """Get the text of a tree-sitter node as a decoded string."""
    return node.text.decode('utf-8', errors='replace')


def _get_def_name(node, lang_name: str) -> Optional[str]:
    """Extract the identifier name from a definition node."""
    if lang_name == 'python':
        # For python, the name is the first named child that is an 'identifier'
        for child in node.children:
            if child.type == 'identifier':
                return _node_text(child)
        return None

    # For most C-family languages, the name identifier is a direct child
    for child in node.children:
        if child.type in ('identifier', 'type_identifier', 'property_identifier',
                          'field_identifier', 'simple_identifier', 'scoped_identifier'):
            return _node_text(child)

    # Go type_declaration: the name is inside type_spec > type_identifier
    # Go var_declaration: names are inside var_spec > identifier
    if lang_name == 'go':
        for child in node.children:
            if child.type in ('type_spec', 'var_spec'):
                for gc in child.children:
                    if gc.type in ('type_identifier', 'identifier'):
                        return _node_text(gc)

    # Java record_declaration: name may be inside a different structure
    return None


# ---------------------------------------------------------------------------
# Python tree-sitter extraction
# ---------------------------------------------------------------------------

def _extract_python_docs_ts(root, source: bytes, file_path: str) -> List[DocEntry]:
    """Extract docstrings from Python AST."""
    entries = []

    for child in root.children:
        # Module-level docstring: expression_statement containing a string
        if child.type == 'expression_statement':
            for gc in child.children:
                if gc.type == 'string':
                    text = _node_text(gc)
                    # Strip triple quotes
                    text = re.sub(r'^"""|"""$', '', text.strip())
                    text = re.sub(r"^'''|'''$", '', text)
                    text = text.strip()
                    parsed = _parse_python_docstring(text)
                    entries.append(DocEntry(
                        name='module',
                        type='module',
                        description=parsed['description'],
                        params=parsed['params'],
                        returns=parsed['returns'],
                        examples=parsed['examples'],
                        line_number=child.start_point[0] + 1,
                        file_path=file_path,
                    ))

        elif child.type in ('function_definition', 'class_definition'):
            name = _get_def_name(child, 'python')
            if not name:
                continue
            line = child.start_point[0] + 1
            def_type = 'function' if child.type == 'function_definition' else 'class'

            # Check for docstring: block > expression_statement > string
            doc_text = None
            block = None
            for c in child.children:
                if c.type == 'block':
                    block = c
                    break
            if block and block.child_count > 0 and block.children[0].type == 'expression_statement':
                expr = block.children[0]
                if expr.child_count > 0 and expr.children[0].type == 'string':
                    doc_text = _node_text(expr.children[0])

            if doc_text:
                # Strip triple quotes
                doc_text = re.sub(r'^"""|"""$', '', doc_text.strip())
                doc_text = re.sub(r"^'''|'''$", '', doc_text)
                doc_text = doc_text.strip()
                parsed = _parse_python_docstring(doc_text)
                entries.append(DocEntry(
                    name=name,
                    type=def_type,
                    description=parsed['description'],
                    params=parsed['params'],
                    returns=parsed['returns'],
                    examples=parsed['examples'],
                    line_number=line,
                    file_path=file_path,
                ))

    return entries


# ---------------------------------------------------------------------------
# JS/TS/TSX tree-sitter extraction
# ---------------------------------------------------------------------------

def _is_jsdoc_comment(node) -> bool:
    """Check if a comment node is a JSDoc comment (starts with /**)."""
    text = _node_text(node).strip()
    return text.startswith('/**') and text.endswith('*/')


def _get_preceding_jsdoc(node) -> Optional[Any]:
    """Find the JSDoc comment node immediately preceding a definition node.

    Handles the fact that comments are not named siblings in tree-sitter.
    We walk backwards from the node's position.
    """
    # Strategy: go to the previous sibling (named or unnamed), check if it's a JSDoc
    prev = node.prev_sibling
    while prev is not None:
        if prev.type == 'comment' and _is_jsdoc_comment(prev):
            return prev
        # Skip blank/comment-only nodes, but stop at actual code
        if prev.type not in ('comment',):
            return None
        prev = prev.prev_sibling
    return None


def _get_js_entry_type(node) -> tuple:
    """Determine (name, entry_type, line) from a JS/TS definition node."""
    name = None
    entry_type = 'function'
    line = node.start_point[0] + 1

    if node.type in ('function_declaration', 'generator_function_declaration'):
        entry_type = 'function'
        name = _get_def_name(node, 'javascript')
    elif node.type == 'class_declaration':
        entry_type = 'class'
        name = _get_def_name(node, 'javascript')
    elif node.type == 'lexical_declaration':
        # e.g. const myFunc = () => {}; or const MyClass = class {};
        for child in node.children:
            if child.type == 'variable_declarator':
                name = _get_def_name(child, 'javascript')
                # Check value type
                for vc in child.children:
                    if vc.type == 'arrow_function':
                        entry_type = 'function'
                        break
                    elif vc.type == 'class':
                        entry_type = 'class'
                        break
                break
    elif node.type == 'method_definition':
        entry_type = 'method'
        name = _get_def_name(node, 'javascript')
    elif node.type == 'interface_declaration':
        entry_type = 'interface'
        name = _get_def_name(node, 'javascript')
    elif node.type == 'type_alias_declaration':
        entry_type = 'type'
        for child in node.children:
            if child.type == 'type_identifier':
                name = _node_text(child)
                break

    return name, entry_type, line


def _strip_jsdoc_delimiters(text: str) -> str:
    """Strip /** and */ from JSDoc comment text."""
    text = text.strip()
    if text.startswith('/**'):
        text = text[3:]
    if text.endswith('*/'):
        text = text[:-2]
    return text


def _extract_js_doc_comments(root, source: bytes, file_path: str) -> List[DocEntry]:
    """Extract JSDoc comments from JS/TS/TSX AST."""
    entries = []

    # Walk all top-level children
    for child in root.children:
        if child.type == 'comment':
            continue  # Skip standalone comments

        if child.type in ('function_declaration', 'generator_function_declaration',
                          'class_declaration', 'lexical_declaration',
                          'method_definition', 'interface_declaration',
                          'type_alias_declaration', 'export_statement'):
            # Look for preceding JSDoc from this node (or its export wrapper)
            jsdoc = _get_preceding_jsdoc(child)
            if jsdoc:
                doc_text = _strip_jsdoc_delimiters(_node_text(jsdoc))
                # Get the actual definition node (skip export wrappers)
                def_node = child
                if child.type == 'export_statement':
                    # The first child is the 'export' keyword, skip to the declaration
                    for c in child.children:
                        if c.type != 'export':
                            def_node = c
                            break
                name, entry_type, line = _get_js_entry_type(def_node)
                if name:
                    parsed = _parse_jsdoc_text(doc_text)
                    entries.append(DocEntry(
                        name=name,
                        type=entry_type,
                        description=parsed['description'],
                        params=parsed['params'],
                        returns=parsed['returns'],
                        examples=parsed['examples'],
                        line_number=jsdoc.start_point[0] + 1,
                        file_path=file_path,
                    ))

    return entries


# ---------------------------------------------------------------------------
# Go tree-sitter extraction
# ---------------------------------------------------------------------------

def _get_preceding_go_comment(node) -> Optional[Any]:
    """Find the comment block immediately preceding a Go declaration node."""
    prev = node.prev_sibling
    while prev is not None:
        if prev.type == 'comment':
            return prev
        if prev.type not in ('comment',):
            return None
        prev = prev.prev_sibling
    return None


def _extract_go_doc_comments(root, source: bytes, file_path: str) -> List[DocEntry]:
    """Extract Go doc comments from AST."""
    entries = []

    for child in root.children:
        if child.type in ('function_declaration', 'method_declaration',
                          'type_declaration', 'var_declaration', 'const_declaration'):
            comment = _get_preceding_go_comment(child)
            if not comment:
                continue

            comment_text = _node_text(comment)
            lines = [line.lstrip('/').strip() for line in comment_text.split('\n') if line.strip().startswith('/')]

            name = _get_def_name(child, 'go')
            if not name:
                continue

            line = comment.start_point[0] + 1

            # Determine type from the declaration node
            if child.type == 'function_declaration':
                entry_type = 'function'
            elif child.type == 'method_declaration':
                entry_type = 'method'
            elif child.type == 'type_declaration':
                entry_type = 'type'
            elif child.type == 'const_declaration':
                entry_type = 'constant'
            else:
                entry_type = 'variable'

            parsed = _parse_go_doc_lines(lines)
            entries.append(DocEntry(
                name=name,
                type=entry_type,
                description=parsed['description'],
                params=parsed['params'],
                returns=parsed['returns'],
                examples=parsed['examples'],
                line_number=line,
                file_path=file_path,
            ))

    return entries


# ---------------------------------------------------------------------------
# Java / Kotlin tree-sitter extraction
# ---------------------------------------------------------------------------

def _get_preceding_block_comment(node) -> Optional[Any]:
    """Find a Javadoc block_comment immediately preceding a declaration."""
    prev = node.prev_sibling
    while prev is not None:
        if prev.type == 'block_comment':
            text = _node_text(prev).strip()
            if text.startswith('/**') and text.endswith('*/'):
                return prev
            return None  # Regular block comment, not Javadoc
        if prev.type not in ('comment', 'block_comment', 'line_comment'):
            return None
        prev = prev.prev_sibling
    return None


def _get_java_entry_type(node) -> tuple:
    """Determine (name, entry_type, line) from a Java/Kotlin declaration node."""
    name = None
    entry_type = 'function'
    line = node.start_point[0] + 1

    if node.type == 'class_declaration':
        entry_type = 'class'
        name = _get_def_name(node, 'java')
    elif node.type == 'interface_declaration':
        entry_type = 'interface'
        name = _get_def_name(node, 'java')
    elif node.type == 'enum_declaration':
        entry_type = 'enum'
        name = _get_def_name(node, 'java')
    elif node.type == 'method_declaration':
        entry_type = 'function'
        name = _get_def_name(node, 'java')
    elif node.type == 'record_declaration':
        entry_type = 'type'
        name = _get_def_name(node, 'java')
    elif node.type == 'function_declaration':
        # Kotlin fun declaration
        entry_type = 'function'
        name = _get_def_name(node, 'kotlin')

    return name, entry_type, line


def _extract_java_doc_comments(root, source: bytes, file_path: str, lang_name: str = 'java') -> List[DocEntry]:
    """Extract Javadoc comments from Java/Kotlin AST."""
    entries = []

    for child in root.children:
        # Check for class_declaration etc.
        target_types = ('class_declaration', 'interface_declaration',
                        'enum_declaration', 'method_declaration',
                        'record_declaration', 'function_declaration',
                        'object_declaration', 'property_declaration')

        if child.type in target_types:
            javadoc = _get_preceding_block_comment(child)
            if not javadoc:
                continue

            doc_text = _node_text(javadoc).strip()
            # Strip /** and */
            if doc_text.startswith('/**'):
                doc_text = doc_text[3:]
            if doc_text.endswith('*/'):
                doc_text = doc_text[:-2]

            name, entry_type, line = _get_java_entry_type(child)
            if not name:
                continue

            parsed = _parse_javadoc_text(doc_text)
            entries.append(DocEntry(
                name=name,
                type=entry_type,
                description=parsed['description'],
                params=parsed['params'],
                returns=parsed['returns'],
                examples=parsed['examples'],
                line_number=javadoc.start_point[0] + 1,
                file_path=file_path,
            ))

    return entries


# ---------------------------------------------------------------------------
# Rust tree-sitter extraction
# ---------------------------------------------------------------------------

def _extract_rust_doc_comments(root, source: bytes, file_path: str) -> List[DocEntry]:
    """Extract Rust doc comments (///) from AST."""
    entries = []

    for child in root.children:
        if child.type in ('function_item', 'struct_item', 'enum_item',
                          'trait_item', 'impl_item', 'type_item',
                          'const_item', 'static_item'):
            # Rust outer doc comments are tracked as comment nodes
            # Look for preceding /// comments
            comment_lines = []
            comment_line = child.start_point[0] + 1

            prev = child.prev_sibling
            while prev is not None:
                if prev.type == 'line_comment':
                    text = _node_text(prev).strip()
                    # Check if it's a doc comment
                    if text.startswith('///'):
                        # Strip the /// prefix
                        line_content = text[3:]
                        if line_content.startswith(' '):
                            line_content = line_content[1:]
                        comment_lines.insert(0, line_content)
                        comment_line = prev.start_point[0] + 1
                    else:
                        break
                elif prev.type == 'outer_doc_comment':
                    text = _node_text(prev).strip()
                    line_content = text[3:]  # strip ///
                    if line_content.startswith(' '):
                        line_content = line_content[1:]
                    comment_lines.insert(0, line_content)
                    comment_line = prev.start_point[0] + 1
                else:
                    break
                prev = prev.prev_sibling

            if not comment_lines:
                continue

            name = _get_def_name(child, 'rust')
            if not name:
                continue

            # Determine entry type
            if child.type == 'function_item':
                entry_type = 'function'
            elif child.type == 'struct_item':
                entry_type = 'type'
            elif child.type == 'enum_item':
                entry_type = 'enum'
            elif child.type == 'trait_item':
                entry_type = 'interface'
            elif child.type in ('type_item', 'impl_item'):
                entry_type = 'type'
            elif child.type in ('const_item', 'static_item'):
                entry_type = 'constant'
            else:
                entry_type = 'function'

            parsed = _parse_rust_doc_lines(comment_lines)
            entries.append(DocEntry(
                name=name,
                type=entry_type,
                description=parsed['description'],
                params=parsed['params'],
                returns=parsed['returns'],
                examples=parsed['examples'],
                line_number=comment_line,
                file_path=file_path,
            ))

    return entries


# ---------------------------------------------------------------------------
# Main per-language dispatcher (tree-sitter based)
# ---------------------------------------------------------------------------

def _extract_doc_entries(source: bytes, lang_name: str, file_path: str, tree=None) -> List[DocEntry]:
    """Extract doc comment entries using tree-sitter AST parsing.

    Args:
        source: 文件原始字节内容
        lang_name: 语言名称
        file_path: 文件路径（用于 DocEntry.file_path）
        tree: 可选的预解析 tree-sitter Tree 对象，传入则跳过重复解析
    """
    if tree is None:
        mgr = get_manager()
        parser = mgr.get_parser(lang_name)
        tree = parser.parse(source)
    root = tree.root_node

    if root.has_error and root.child_count == 0:
        return []

    if lang_name == 'python':
        return _extract_python_docs_ts(root, source, file_path)
    elif lang_name in ('javascript', 'typescript', 'tsx'):
        return _extract_js_doc_comments(root, source, file_path)
    elif lang_name == 'go':
        return _extract_go_doc_comments(root, source, file_path)
    elif lang_name == 'rust':
        return _extract_rust_doc_comments(root, source, file_path)
    elif lang_name in ('java', 'kotlin'):
        return _extract_java_doc_comments(root, source, file_path, lang_name)

    return []


# ---------------------------------------------------------------------------
# 缓存读取辅助函数
# ---------------------------------------------------------------------------

def _read_doc_entries_from_cache(file_path: str, project_root: str) -> Optional[List[DocEntry]]:
    """尝试从 parse-results.json 缓存中读取文档条目。

    Args:
        file_path: 文件的绝对路径或项目根相对路径
        project_root: 项目根目录路径

    Returns:
        缓存的 DocEntry 列表，如果缓存未命中则返回 None
    """
    try:
        cache_path = Path(project_root) / ".deepwiki" / "cache" / "parse-results.json"
        if not cache_path.exists():
            return None
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        rel_path = str(Path(file_path).relative_to(project_root)).replace('\\', '/')
        files_data = data.get("files", {})
        if rel_path in files_data:
            cached = files_data[rel_path].get("doc_entries", [])
            if cached:
                return [DocEntry(**entry) for entry in cached]
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        pass
    return None


# ---------------------------------------------------------------------------
# Public API（所有新参数均为可选，保持向后兼容）
# ---------------------------------------------------------------------------

def extract_jsdoc(content: str, file_path: str, project_root: str = None) -> List[DocEntry]:
    """从 JavaScript/TypeScript 文件中提取 JSDoc 注释"""
    # 尝试从缓存读取
    if project_root:
        cached = _read_doc_entries_from_cache(file_path, project_root)
        if cached is not None:
            return cached
    source = content.encode('utf-8')
    # Infer lang from file_path extension
    path = Path(file_path)
    lang = 'typescript' if path.suffix.lower() in ('.ts', '.tsx') else 'javascript'
    return _extract_doc_entries(source, lang, file_path)


def extract_python_docstring(content: str, file_path: str, project_root: str = None) -> List[DocEntry]:
    """从 Python 文件中提取 DocString"""
    if project_root:
        cached = _read_doc_entries_from_cache(file_path, project_root)
        if cached is not None:
            return cached
    source = content.encode('utf-8')
    return _extract_doc_entries(source, 'python', file_path)


def extract_go_docs(content: str, file_path: str, project_root: str = None) -> List[DocEntry]:
    """从 Go 文件中提取文档注释"""
    if project_root:
        cached = _read_doc_entries_from_cache(file_path, project_root)
        if cached is not None:
            return cached
    source = content.encode('utf-8')
    return _extract_doc_entries(source, 'go', file_path)


def extract_java_docs(content: str, file_path: str, project_root: str = None) -> List[DocEntry]:
    """从 Java/Kotlin 文件中提取 Javadoc"""
    if project_root:
        cached = _read_doc_entries_from_cache(file_path, project_root)
        if cached is not None:
            return cached
    source = content.encode('utf-8')
    path = Path(file_path)
    lang = 'kotlin' if path.suffix.lower() == '.kt' else 'java'
    return _extract_doc_entries(source, lang, file_path)


def extract_rust_docs(content: str, file_path: str, project_root: str = None) -> List[DocEntry]:
    """从 Rust 文件中提取文档注释"""
    if project_root:
        cached = _read_doc_entries_from_cache(file_path, project_root)
        if cached is not None:
            return cached
    source = content.encode('utf-8')
    return _extract_doc_entries(source, 'rust', file_path)


def extract_docs_from_file(file_path: str, project_root: str = None) -> List[DocEntry]:
    """从文件中提取文档"""
    path = Path(file_path)

    if not path.exists():
        return []

    # 尝试从 parse-results.json 缓存读取
    if project_root:
        cached = _read_doc_entries_from_cache(file_path, project_root)
        if cached is not None:
            return cached

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    suffix = path.suffix.lower()

    if suffix in {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'}:
        return extract_jsdoc(content, file_path)
    elif suffix in {'.py', '.pyi'}:
        return extract_python_docstring(content, file_path)
    elif suffix == '.go':
        return extract_go_docs(content, file_path)
    elif suffix in {'.java', '.kt'}:
        return extract_java_docs(content, file_path)
    elif suffix == '.rs':
        return extract_rust_docs(content, file_path)

    return []


_I18N_LABELS = {
    'zh': {
        'functions': '## 函数', 'classes': '## 类', 'types': '## 类型定义',
        'params': '**参数:**', 'returns_prefix': '**返回值:**',
    },
    'en': {
        'functions': '## Functions', 'classes': '## Classes', 'types': '## Type Definitions',
        'params': '**Parameters:**', 'returns_prefix': '**Returns:**',
    },
}


def docs_to_markdown(entries: List[DocEntry], language: str = 'zh') -> str:
    """将文档条目转换为 Markdown"""
    labels = _I18N_LABELS.get(language, _I18N_LABELS['zh'])
    lines = []

    # 按类型分组
    functions = [e for e in entries if e.type == 'function']
    classes = [e for e in entries if e.type == 'class']
    types = [e for e in entries if e.type in {'type', 'interface'}]

    if functions:
        lines.append(f'{labels["functions"]}\n')
        for func in functions:
            lines.append(f'### `{func.name}`\n')
            lines.append(f'{func.description}\n')

            if func.params:
                lines.append(f'{labels["params"]}\n')
                for param in func.params:
                    lines.append(f"- `{param['name']}` ({param['type']}): {param['description']}")
                lines.append('')

            if func.returns:
                lines.append(f'{labels["returns_prefix"]} {func.returns}\n')

    if classes:
        lines.append(f'{labels["classes"]}\n')
        for cls in classes:
            lines.append(f'### `{cls.name}`\n')
            lines.append(f'{cls.description}\n')

    if types:
        lines.append(f'{labels["types"]}\n')
        for t in types:
            lines.append(f'### `{t.name}`\n')
            lines.append(f'{t.description}\n')

    return '\n'.join(lines)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python extract_doc_comments.py <文件路径>")
        sys.exit(1)

    file_path = sys.argv[1]
    entries = extract_docs_from_file(file_path)

    print(docs_to_markdown(entries))
