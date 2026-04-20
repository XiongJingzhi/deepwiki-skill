#!/usr/bin/env python3
"""
文档提取脚本
从代码文件中提取 JSDoc/TSDoc/DocString/GoDoc/Javadoc 注释
支持: JavaScript/TypeScript, Python, Go, Java/Kotlin, Rust
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


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


def extract_jsdoc(content: str, file_path: str) -> List[DocEntry]:
    """从 JavaScript/TypeScript 文件中提取 JSDoc 注释"""
    entries = []
    
    # JSDoc 注释模式
    jsdoc_pattern = r'/\*\*\s*([\s\S]*?)\*/\s*(?:export\s+)?(?:async\s+)?(?:function|class|const|let|var|interface|type)\s+(\w+)'
    
    for match in re.finditer(jsdoc_pattern, content):
        doc_text = match.group(1)
        name = match.group(2)
        line_number = content[:match.start()].count('\n') + 1
        
        # 解析描述
        description_lines = []
        params = []
        returns = None
        examples = []
        
        for line in doc_text.split('\n'):
            line = line.strip().lstrip('* ')
            
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
                # 收集示例代码直到下一个 @ 标签
                continue
            elif not line.startswith('@'):
                description_lines.append(line)
        
        description = ' '.join(description_lines).strip()
        
        # 确定类型
        if 'class' in match.group(0).lower():
            entry_type = 'class'
        elif 'interface' in match.group(0).lower():
            entry_type = 'interface'
        elif 'type' in match.group(0):
            entry_type = 'type'
        else:
            entry_type = 'function'
        
        entries.append(DocEntry(
            name=name,
            type=entry_type,
            description=description,
            params=params,
            returns=returns,
            examples=examples,
            line_number=line_number,
            file_path=file_path
        ))
    
    return entries


def extract_python_docstring(content: str, file_path: str) -> List[DocEntry]:
    """从 Python 文件中提取 DocString"""
    entries = []
    
    # 函数/类定义模式
    def_pattern = r'(?:^|\n)((?:async\s+)?def|class)\s+(\w+)[^:]*:\s*(?:\n\s+)?(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\')'
    
    for match in re.finditer(def_pattern, content):
        def_type = 'function' if 'def' in match.group(1) else 'class'
        name = match.group(2)
        docstring = match.group(3) or match.group(4) or ''
        line_number = content[:match.start()].count('\n') + 1
        
        # 解析 Google/NumPy 风格 docstring
        description_lines = []
        params = []
        returns = None
        examples = []
        
        current_section = 'description'
        
        for line in docstring.split('\n'):
            stripped = line.strip()
            
            if stripped in ('Args:', 'Arguments:', 'Parameters:'):
                current_section = 'params'
                continue
            elif stripped in ('Returns:', 'Return:'):
                current_section = 'returns'
                continue
            elif stripped in ('Example:', 'Examples:'):
                current_section = 'examples'
                continue
            elif stripped.endswith(':') and not ':' in stripped[:-1]:
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
                returns = stripped
            elif current_section == 'examples':
                examples.append(stripped)
        
        description = ' '.join(description_lines).strip()
        
        entries.append(DocEntry(
            name=name,
            type=def_type,
            description=description,
            params=params,
            returns=returns,
            examples=examples,
            line_number=line_number,
            file_path=file_path
        ))
    
    return entries


def extract_docs_from_file(file_path: str) -> List[DocEntry]:
    """从文件中提取文档"""
    path = Path(file_path)

    if not path.exists():
        return []

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


def extract_go_docs(content: str, file_path: str) -> List[DocEntry]:
    """从 Go 文件中提取文档注释"""
    entries = []

    # Go doc: 注释紧邻声明之前
    # 匹配 func, type, const, var 前面的注释块
    pattern = r'(?:(?://\s*(.+)\n)+)\s*(?:func|type|const|var)\s+(\w+)'

    for match in re.finditer(pattern, content):
        comment_block = match.group(0)
        lines = re.findall(r'//\s*(.+)', comment_block)
        # 最后一行是声明行中的名称后面的内容，去掉
        decl_match = re.search(r'(?:func|type|const|var)\s+(\w+)', comment_block)
        if not decl_match:
            continue
        name = decl_match.group(1)
        line_number = content[:match.start()].count('\n') + 1

        # 提取描述（第一句是摘要）
        description_lines = []
        params = []
        returns = None

        for line in lines:
            if line.startswith('@deprecated'):
                description_lines.append('[Deprecated] ' + line[len('@deprecated'):].strip())
            elif line.startswith('@param') or line.startswith('@param:'):
                param_match = re.match(r'@param:?\s+(\w+)\s*-?\s*(.*)', line)
                if param_match:
                    params.append({
                        'name': param_match.group(1),
                        'type': 'any',
                        'description': param_match.group(2)
                    })
            elif not line.startswith('@'):
                description_lines.append(line)

        description = ' '.join(description_lines).strip()

        # 确定类型
        if 'func ' in comment_block:
            entry_type = 'function'
        elif 'type ' in comment_block:
            entry_type = 'type'
        elif 'const ' in comment_block:
            entry_type = 'constant'
        else:
            entry_type = 'variable'

        entries.append(DocEntry(
            name=name,
            type=entry_type,
            description=description,
            params=params,
            returns=returns,
            examples=[],
            line_number=line_number,
            file_path=file_path
        ))

    return entries


def extract_java_docs(content: str, file_path: str) -> List[DocEntry]:
    """从 Java/Kotlin 文件中提取 Javadoc"""
    entries = []

    # Javadoc 模式: /** ... */ 紧邻 public/protected 声明之前
    javadoc_pattern = r'/\*\*\s*([\s\S]*?)\*/\s*(?:(?:public|protected|private|static|final|abstract|open|sealed)\s+)*(?:class|interface|enum|record|object|fun|val|var)\s+(\w+)'

    for match in re.finditer(javadoc_pattern, content):
        doc_text = match.group(1)
        name = match.group(2)
        line_number = content[:match.start()].count('\n') + 1

        description_lines = []
        params = []
        returns = None

        for line in doc_text.split('\n'):
            line = line.strip().lstrip('* ')

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
                pass  # 可以扩展
            elif not line.startswith('@'):
                description_lines.append(line)

        description = ' '.join(description_lines).strip()

        # 确定类型
        decl = match.group(0).lower()
        if 'class ' in decl or 'object ' in decl:
            entry_type = 'class'
        elif 'interface ' in decl:
            entry_type = 'interface'
        elif 'enum ' in decl:
            entry_type = 'enum'
        elif 'record ' in decl:
            entry_type = 'type'
        else:
            entry_type = 'function'

        entries.append(DocEntry(
            name=name,
            type=entry_type,
            description=description,
            params=params,
            returns=returns,
            examples=[],
            line_number=line_number,
            file_path=file_path
        ))

    return entries


def extract_rust_docs(content: str, file_path: str) -> List[DocEntry]:
    """从 Rust 文件中提取文档注释"""
    entries = []

    # Rust doc: /// 注释紧邻 pub 声明之前
    pattern = r'(?:(?:///[ \t]*(.+)\n)+)\s*(?:pub\s+)?(?:async\s+)?(?:fn|struct|enum|trait|type|const|static)\s+(\w+)'

    for match in re.finditer(pattern, content):
        comment_block = match.group(0)
        lines = re.findall(r'///[ \t]*(.+)', comment_block)
        decl_match = re.search(r'(?:pub\s+)?(?:async\s+)?(?:fn|struct|enum|trait|type|const|static)\s+(\w+)', comment_block)
        if not decl_match:
            continue
        name = decl_match.group(1)
        line_number = content[:match.start()].count('\n') + 1

        description_lines = []
        params = []
        returns = None

        for line in lines:
            if line.startswith('# '):
                # Rust doc heading, skip section markers
                description_lines.append(line[2:].strip())
            elif not line.startswith('@'):
                description_lines.append(line)

        description = ' '.join(description_lines).strip()

        # 确定类型
        if 'fn ' in comment_block:
            entry_type = 'function'
        elif 'struct ' in comment_block:
            entry_type = 'type'
        elif 'enum ' in comment_block:
            entry_type = 'enum'
        elif 'trait ' in comment_block:
            entry_type = 'interface'
        elif 'type ' in comment_block:
            entry_type = 'type'
        else:
            entry_type = 'constant'

        entries.append(DocEntry(
            name=name,
            type=entry_type,
            description=description,
            params=params,
            returns=returns,
            examples=[],
            line_number=line_number,
            file_path=file_path
        ))

    return entries


def docs_to_markdown(entries: List[DocEntry]) -> str:
    """将文档条目转换为 Markdown"""
    lines = []
    
    # 按类型分组
    functions = [e for e in entries if e.type == 'function']
    classes = [e for e in entries if e.type == 'class']
    types = [e for e in entries if e.type in {'type', 'interface'}]
    
    if functions:
        lines.append('## 函数\n')
        for func in functions:
            lines.append(f'### `{func.name}`\n')
            lines.append(f'{func.description}\n')
            
            if func.params:
                lines.append('**参数:**\n')
                for param in func.params:
                    lines.append(f"- `{param['name']}` ({param['type']}): {param['description']}")
                lines.append('')
            
            if func.returns:
                lines.append(f'**返回值:** {func.returns}\n')
    
    if classes:
        lines.append('## 类\n')
        for cls in classes:
            lines.append(f'### `{cls.name}`\n')
            lines.append(f'{cls.description}\n')
    
    if types:
        lines.append('## 类型定义\n')
        for t in types:
            lines.append(f'### `{t.name}`\n')
            lines.append(f'{t.description}\n')
    
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python extract_docs.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    entries = extract_docs_from_file(file_path)
    
    print(docs_to_markdown(entries))
