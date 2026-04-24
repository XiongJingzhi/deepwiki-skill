"""
Tree-Sitter 解析器管理模块。

提供统一的 ParserManager 单例，按需懒加载各语言的 tree-sitter 解析器。
支持 Python、JavaScript、TypeScript、TSX、Go、Rust、Java、Kotlin。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

# tree-sitter 核心类型
from tree_sitter import Language, Parser, Query, QueryCursor

# 扩展名 → (模块名, 语言工厂函数名)
_LANGUAGE_SPECS: Dict[str, Tuple[str, str]] = {
    "python": ("tree_sitter_python", "language"),
    "javascript": ("tree_sitter_javascript", "language"),
    "typescript": ("tree_sitter_typescript", "language_typescript"),
    "tsx": ("tree_sitter_typescript", "language_tsx"),
    "go": ("tree_sitter_go", "language"),
    "rust": ("tree_sitter_rust", "language"),
    "java": ("tree_sitter_java", "language"),
    "kotlin": ("tree_sitter_kotlin", "language"),
}

# 文件扩展名 → 语言名
_EXT_TO_LANG: Dict[str, str] = {
    ".py": "python", ".pyi": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
}

# ── 预编译 Query 模式 ────────────────────────────────────────────────────

# 函数/方法定义提取（返回 function_definition + class_definition 节点）
_FUNC_CLASS_QUERIES: Dict[str, str] = {
    "python": "(function_definition) @fn (class_definition) @cls",
    "javascript": """
        (function_declaration) @fn
        (method_definition) @method
        (class_declaration) @cls
        (lexical_declaration (variable_declarator value: (arrow_function))) @arrow
    """,
    "typescript": """
        (function_declaration) @fn
        (method_definition) @method
        (class_declaration) @cls
        (lexical_declaration (variable_declarator value: (arrow_function))) @arrow
    """,
    "tsx": """
        (function_declaration) @fn
        (method_definition) @method
        (class_declaration) @cls
        (lexical_declaration (variable_declarator value: (arrow_function))) @arrow
    """,
    "go": "(function_declaration) @fn (method_declaration) @method",
    "rust": "(function_item) @fn (impl_item) @impl",
    "java": "(method_declaration) @method (class_declaration) @cls (interface_declaration) @iface",
    "kotlin": "(function_declaration) @fn (class_declaration) @cls",
}

# 函数体内调用提取
_CALL_QUERIES: Dict[str, str] = {
    "python": """
        (call
          function: (identifier) @call.fn)
        (call
          function: (attribute
            object: (identifier) @call.obj
            attribute: (identifier) @call.attr))
    """,
    "javascript": """
        (call_expression
          function: (identifier) @call.fn)
        (call_expression
          function: (member_expression
            object: (identifier) @call.obj
            property: (property_identifier) @call.attr))
        (call_expression
          function: (member_expression
            object: (member_expression) @call.obj
            property: (property_identifier) @call.attr))
    """,
    "typescript": """
        (call_expression
          function: (identifier) @call.fn)
        (call_expression
          function: (member_expression
            object: (identifier) @call.obj
            property: (property_identifier) @call.attr))
        (call_expression
          function: (member_expression
            object: (member_expression) @call.obj
            property: (property_identifier) @call.attr))
    """,
    "tsx": """
        (call_expression
          function: (identifier) @call.fn)
        (call_expression
          function: (member_expression
            object: (identifier) @call.obj
            property: (property_identifier) @call.attr))
        (call_expression
          function: (member_expression
            object: (member_expression) @call.obj
            property: (property_identifier) @call.attr))
    """,
    "go": """
        (call_expression
          function: (identifier) @call.fn)
        (call_expression
          function: (selector_expression
            operand: (identifier) @call.obj
            field: (field_identifier) @call.attr))
    """,
    "rust": """
        (call_expression
          function: (identifier) @call.fn)
        (call_expression
          function: (field_expression
            value: (identifier) @call.obj
            field: (field_identifier) @call.attr))
    """,
    "java": """
        (method_invocation
          name: (identifier) @call.fn)
        (method_invocation
          object: (identifier) @call.obj
          name: (identifier) @call.attr)
    """,
    "kotlin": """
        (call_expression
          function: (identifier) @call.fn)
        (call_expression
          function: (member_access_expression
            value: (identifier) @call.obj
                . (simple_identifier) @call.attr))
    """,
}

# Import 语句提取
_IMPORT_QUERIES: Dict[str, str] = {
    "python": """
        (import_from_statement module_name: (dotted_name) @import.module) @stmt
        (import_statement name: (dotted_name) @import.path) @stmt
    """,
    "javascript": """
        (import_statement source: (string) @import.path) @stmt
        (call_expression
          function: (identifier) @require.fn
          arguments: (arguments (string) @import.path)) @require
    """,
    "typescript": """
        (import_statement source: (string) @import.path) @stmt
    """,
    "tsx": """
        (import_statement source: (string) @import.path) @stmt
    """,
    "go": """
        (import_spec path: (interpreted_string_literal) @import.path) @stmt
    """,
    "rust": """
        (use_declaration
          argument: (scoped_identifier) @import.path) @stmt
    """,
    "java": """
        (import_declaration (scoped_identifier) @import.path) @stmt
    """,
    "kotlin": """
        (import
          (qualified_identifier) @import.path) @stmt
    """,
}

# 控制流节点（复杂度估算用）
_COMPLEXITY_QUERIES: Dict[str, str] = {
    "python": """
        (if_statement) @cf (elif_clause) @cf (while_statement) @cf (for_statement) @cf
        (try_statement) @cf (except_clause) @cf (with_statement) @cf
        (match_statement) @cf
        (function_definition) @def (class_definition) @def
    """,
    "javascript": """
        (if_statement) @cf (while_statement) @cf (for_statement) @cf
        (for_in_statement) @cf (switch_statement) @cf (try_statement) @cf (catch_clause) @cf
        (function_declaration) @def (class_declaration) @def
    """,
    "typescript": """
        (if_statement) @cf (while_statement) @cf (for_statement) @cf
        (for_in_statement) @cf (switch_statement) @cf (try_statement) @cf (catch_clause) @cf
        (function_declaration) @def (class_declaration) @def
    """,
    "tsx": """
        (if_statement) @cf (while_statement) @cf (for_statement) @cf
        (for_in_statement) @cf (switch_statement) @cf (try_statement) @cf (catch_clause) @cf
        (function_declaration) @def (class_declaration) @def
    """,
    "go": """
        (if_statement) @cf (for_statement) @cf (switch_statement) @cf
        (select_statement) @cf (type_switch_statement) @cf
        (function_declaration) @def (method_declaration) @def
    """,
    "rust": """
        (if_expression) @cf (while_expression) @cf (for_expression) @cf
        (loop_expression) @cf (match_expression) @cf (if_let_expression) @cf
        (function_item) @def (struct_item) @def (enum_item) @def (trait_item) @def (impl_item) @def
    """,
    "java": """
        (if_statement) @cf (while_statement) @cf (for_statement) @cf
        (enhanced_for_statement) @cf (switch_expression) @cf (try_statement) @cf (catch_clause) @cf
        (method_declaration) @def (class_declaration) @def (interface_declaration) @def
    """,
    "kotlin": """
        (if_expression) @cf (while_statement) @cf (for_statement) @cf
        (when_expression) @cf (try_expression) @cf (catch_block) @cf
        (function_declaration) @def (class_declaration) @def
    """,
}

# 重要行检测（声明/导入/导出等节点）
_IMPORTANT_QUERIES: Dict[str, str] = {
    "python": """
        (import_statement) @imp (import_from_statement) @imp
        (function_definition) @decl (class_definition) @decl
        (decorator) @decl
    """,
    "javascript": """
        (import_statement) @imp (export_statement) @exp
        (function_declaration) @decl (class_declaration) @decl (lexical_declaration) @decl
        (expression_statement (assignment_expression)) @decl
    """,
    "typescript": """
        (import_statement) @imp (export_statement) @exp
        (function_declaration) @decl (class_declaration) @decl (lexical_declaration) @decl
        (interface_declaration) @decl (type_alias_declaration) @decl (enum_declaration) @decl
    """,
    "tsx": """
        (import_statement) @imp (export_statement) @exp
        (function_declaration) @decl (class_declaration) @decl (lexical_declaration) @decl
        (interface_declaration) @decl (type_alias_declaration) @decl
    """,
    "go": """
        (import_declaration) @imp (function_declaration) @decl (method_declaration) @decl
        (type_declaration) @decl (var_declaration) @decl (const_declaration) @decl
    """,
    "rust": """
        (use_declaration) @imp
        (function_item) @decl (struct_item) @decl (enum_item) @decl
        (trait_item) @decl (impl_item) @decl (type_item) @decl (const_item) @decl
        (attribute_item) @decl
    """,
    "java": """
        (import_declaration) @imp
        (method_declaration) @decl (class_declaration) @decl
        (interface_declaration) @decl (enum_declaration) @decl (field_declaration) @decl
        (annotation) @decl
    """,
    "kotlin": """
        (import) @imp
        (function_declaration) @decl (class_declaration) @decl
        (object_declaration) @decl (property_declaration) @decl (annotation) @decl
    """,
}


class ParserManager:
    """管理各语言 tree-sitter Parser/Language 的单例，按需懒加载。"""

    def __init__(self):
        self._parsers: Dict[str, Parser] = {}
        self._languages: Dict[str, Language] = {}
        self._queries: Dict[str, Dict[str, Query]] = {}

    def get_language(self, lang_name: str) -> Language:
        """获取指定语言的 Language 对象（懒加载）。"""
        if lang_name not in self._languages:
            mod_name, func_name = _LANGUAGE_SPECS[lang_name]
            mod = __import__(mod_name, fromlist=[func_name])
            lang_func = getattr(mod, func_name)
            self._languages[lang_name] = Language(lang_func())
        return self._languages[lang_name]

    def get_parser(self, lang_name: str) -> Parser:
        """获取指定语言的 Parser 实例（懒加载）。"""
        if lang_name not in self._parsers:
            lang = self.get_language(lang_name)
            self._parsers[lang_name] = Parser(lang)
        return self._parsers[lang_name]

    def get_parser_for_ext(self, ext: str) -> Optional[Parser]:
        """根据文件扩展名获取 Parser。"""
        lang = _EXT_TO_LANG.get(ext.lower())
        if not lang:
            return None
        return self.get_parser(lang)

    def get_lang_for_ext(self, ext: str) -> Optional[str]:
        """根据文件扩展名获取语言名。"""
        return _EXT_TO_LANG.get(ext.lower())

    def get_query(self, lang_name: str, category: str) -> Query:
        """获取预编译的 Query 对象。

        Args:
            lang_name: 语言名 (python, javascript, ...)
            category: 查询类别 (func_class, call, import, complexity, important)
        """
        category_map = {
            "func_class": _FUNC_CLASS_QUERIES,
            "call": _CALL_QUERIES,
            "import": _IMPORT_QUERIES,
            "complexity": _COMPLEXITY_QUERIES,
            "important": _IMPORTANT_QUERIES,
        }
        key = f"{lang_name}:{category}"
        if key not in self._queries:
            patterns = category_map.get(category, {})
            source = patterns.get(lang_name, "")
            if not source:
                raise ValueError(f"No {category} query for {lang_name}")
            lang = self.get_language(lang_name)
            self._queries[key] = Query(lang, source)
        return self._queries[key]

    def parse_file(self, filepath: Path) -> Optional[tuple]:
        """解析文件，返回 (tree, source_bytes) 或 None。"""
        ext = filepath.suffix.lower()
        parser = self.get_parser_for_ext(ext)
        if not parser:
            return None
        try:
            source = filepath.read_bytes()
            if not source.strip():
                return None
            tree = parser.parse(source)
            return tree, source
        except Exception:
            return None

    def run_query(self, lang_name: str, category: str, node):
        """在指定节点上执行预编译 query，返回 captures dict。"""
        query = self.get_query(lang_name, category)
        cursor = QueryCursor(query)
        return cursor.captures(node)


# 模块级单例
_manager: Optional[ParserManager] = None


def get_manager() -> ParserManager:
    """获取 ParserManager 全局单例。"""
    global _manager
    if _manager is None:
        _manager = ParserManager()
    return _manager


def get_parser_for_ext(ext: str) -> Optional[Parser]:
    """便捷函数：根据扩展名获取 Parser。"""
    return get_manager().get_parser_for_ext(ext)


def get_lang_for_ext(ext: str) -> Optional[str]:
    """便捷函数：根据扩展名获取语言名。"""
    return get_manager().get_lang_for_ext(ext)


def parse_file(filepath: Path) -> Optional[tuple]:
    """便捷函数：解析文件。"""
    return get_manager().parse_file(filepath)


def run_query(lang_name: str, category: str, node) -> dict:
    """便捷函数：执行预编译 query。"""
    return get_manager().run_query(lang_name, category, node)
