"""Tests for scripts/extract_doc_comments.py - documentation extraction from source code."""

import pytest

import extract_doc_comments
from extract_doc_comments import (
    DocEntry,
    extract_jsdoc,
    extract_python_docstring,
    extract_go_docs,
    extract_java_docs,
    extract_rust_docs,
    extract_docs_from_file,
    docs_to_markdown,
)


# ---------------------------------------------------------------------------
# DocEntry dataclass
# ---------------------------------------------------------------------------

class TestDocEntry:
    """DocEntry holds extracted documentation for a single code element."""

    def test_fields(self):
        entry = DocEntry(
            name="myFunc",
            type="function",
            description="A sample function",
            params=[{"name": "x", "type": "number", "description": "the input"}],
            returns="number",
            examples=["myFunc(1)"],
            line_number=10,
            file_path="src/index.ts",
        )
        assert entry.name == "myFunc"
        assert entry.type == "function"
        assert entry.description == "A sample function"
        assert len(entry.params) == 1
        assert entry.returns == "number"
        assert entry.examples == ["myFunc(1)"]
        assert entry.line_number == 10
        assert entry.file_path == "src/index.ts"

    def test_defaults(self):
        """Optional fields (returns) can be None."""
        entry = DocEntry(
            name="f",
            type="function",
            description="desc",
            params=[],
            returns=None,
            examples=[],
            line_number=1,
            file_path="a.py",
        )
        assert entry.returns is None


# ---------------------------------------------------------------------------
# JSDoc extraction
# ---------------------------------------------------------------------------

class TestExtractJSDoc:
    """Tests for extract_jsdoc (JavaScript / TypeScript)."""

    def test_simple_function(self):
        content = '''\
/**
 * Adds two numbers.
 */
function add(a, b) {
    return a + b;
}
'''
        entries = extract_jsdoc(content, "math.js")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "add"
        assert e.type == "function"
        assert e.description == "Adds two numbers."
        assert e.line_number == 1
        assert e.file_path == "math.js"

    def test_function_with_param(self):
        content = '''\
/**
 * Greets a person.
 * @param {string} name - The person's name
 */
function greet(name) {}
'''
        entries = extract_jsdoc(content, "greet.ts")
        assert len(entries) == 1
        e = entries[0]
        assert len(e.params) == 1
        p = e.params[0]
        assert p["name"] == "name"
        assert p["type"] == "string"
        assert p["description"] == "The person's name"

    def test_function_with_returns(self):
        content = '''\
/**
 * Compute square.
 * @param {number} x - input
 * @returns {number} the square of x
 */
function square(x) {}
'''
        entries = extract_jsdoc(content, "math.ts")
        e = entries[0]
        assert e.returns == "number: the square of x"

    def test_class(self):
        content = '''\
/**
 * Represents a user.
 */
class User {}
'''
        entries = extract_jsdoc(content, "models.ts")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "User"
        assert e.type == "class"

    def test_interface(self):
        content = '''\
/**
 * A serializable object.
 */
interface Serializable {}
'''
        entries = extract_jsdoc(content, "types.ts")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Serializable"
        assert e.type == "interface"

    def test_async_export(self):
        content = '''\
/**
 * Fetches data from remote API.
 * @param {string} url - endpoint URL
 * @returns {Promise<any>} the response data
 */
export async function fetchData(url) {}
'''
        entries = extract_jsdoc(content, "api.ts")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "fetchData"
        assert e.type == "function"
        assert e.params[0]["name"] == "url"

    def test_empty_content(self):
        entries = extract_jsdoc("", "empty.js")
        assert entries == []

    def test_no_jsdoc_comments(self):
        content = "function noDoc() {}\nfunction alsoNoDoc() {}\n"
        entries = extract_jsdoc(content, "plain.js")
        assert entries == []


# ---------------------------------------------------------------------------
# Python docstring extraction
# ---------------------------------------------------------------------------

class TestExtractPythonDocstring:
    """Tests for extract_python_docstring."""

    def test_simple_function(self):
        content = '''\
def hello():
    """Say hello."""
    pass
'''
        entries = extract_python_docstring(content, "util.py")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "hello"
        assert e.type == "function"
        assert e.description == "Say hello."

    def test_class(self):
        content = '''\
class Animal:
    """Base class for all animals."""
    pass
'''
        entries = extract_python_docstring(content, "models.py")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Animal"
        assert e.type == "class"
        assert e.description == "Base class for all animals."

    def test_google_style_args(self):
        content = '''\
def connect(host, port):
    """Connect to a server.

    Args:
        host (str): The hostname to connect to.
        port (int): The port number.
    """
    pass
'''
        entries = extract_python_docstring(content, "net.py")
        e = entries[0]
        assert len(e.params) == 2
        assert e.params[0] == {"name": "host", "type": "str", "description": "The hostname to connect to."}
        assert e.params[1] == {"name": "port", "type": "int", "description": "The port number."}

    def test_returns_section(self):
        content = '''\
def area(radius):
    """Calculate the area of a circle.

    Args:
        radius (float): radius of the circle

    Returns:
        float
    """
    pass
'''
        entries = extract_python_docstring(content, "geo.py")
        e = entries[0]
        # The extract_python_docstring function sets returns = stripped on each line
        # in the 'returns' section, so only the last non-empty line is kept
        assert "float" in e.returns

    def test_triple_single_quotes(self):
        content = """\
def legacy():
    '''
    A legacy function.
    '''
    pass
"""
        entries = extract_python_docstring(content, "old.py")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "legacy"
        assert "legacy" in e.description.lower()

    def test_no_docstring(self):
        content = "def bare():\n    pass\n"
        entries = extract_python_docstring(content, "bare.py")
        assert entries == []


# ---------------------------------------------------------------------------
# Go doc extraction
# ---------------------------------------------------------------------------

class TestExtractGoDocs:
    """Tests for extract_go_docs."""

    def test_function(self):
        content = '''\
// Sum computes the sum of two integers.
func Sum(a, b int) int {
\treturn a + b
}
'''
        entries = extract_go_docs(content, "math.go")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Sum"
        assert e.type == "function"
        assert "sum" in e.description.lower()

    def test_type_struct(self):
        content = '''\
// Config holds application configuration.
type Config struct {
\tPort int
\tHost string
}
'''
        entries = extract_go_docs(content, "config.go")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Config"
        assert e.type == "type"
        assert "configuration" in e.description.lower()

    def test_deprecated_annotation(self):
        content = '''\
// OldFunc is no longer used.
// Deprecated: Use NewFunc instead.
func OldFunc() {}
'''
        entries = extract_go_docs(content, "legacy.go")
        assert len(entries) == 1
        e = entries[0]
        assert "[Deprecated]" in e.description
        assert "NewFunc" in e.description

    def test_empty_content(self):
        entries = extract_go_docs("", "empty.go")
        assert entries == []


# ---------------------------------------------------------------------------
# Java / Javadoc extraction
# ---------------------------------------------------------------------------

class TestExtractJavaDocs:
    """Tests for extract_java_docs."""

    def test_class(self):
        content = '''\
/**
 * Represents a bank account.
 */
public class Account {}
'''
        entries = extract_java_docs(content, "Account.java")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Account"
        assert e.type == "class"
        assert "bank account" in e.description.lower()

    def test_interface(self):
        content = '''\
/**
 * A generic repository interface.
 */
public interface Repository {}
'''
        entries = extract_java_docs(content, "Repository.java")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Repository"
        assert e.type == "interface"

    def test_enum(self):
        content = '''\
/**
 * Supported color values.
 */
public enum Color {}
'''
        entries = extract_java_docs(content, "Color.java")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Color"
        assert e.type == "enum"

    def test_with_param(self):
        content = '''\
/**
 * Creates a new user.
 * @param name the username
 * @param age the user age
 */
public class User {}
'''
        entries = extract_java_docs(content, "User.java")
        e = entries[0]
        assert len(e.params) == 2
        assert e.params[0]["name"] == "name"
        assert e.params[0]["description"] == "the username"
        assert e.params[1]["name"] == "age"

    def test_empty_content(self):
        entries = extract_java_docs("", "Empty.java")
        assert entries == []


# ---------------------------------------------------------------------------
# Rust doc extraction
# ---------------------------------------------------------------------------

class TestExtractRustDocs:
    """Tests for extract_rust_docs."""

    def test_function(self):
        content = '''\
/// Compute the factorial of n.
pub fn factorial(n: u64) -> u64 {
    1
}
'''
        entries = extract_rust_docs(content, "math.rs")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "factorial"
        assert e.type == "function"
        assert "factorial" in e.description.lower()

    def test_struct(self):
        content = '''\
/// A 2D point.
pub struct Point {
    pub x: f64,
    pub y: f64,
}
'''
        entries = extract_rust_docs(content, "geometry.rs")
        assert len(entries) == 1
        e = entries[0]
        assert e.name == "Point"
        assert e.type == "type"

    def test_examples_section(self):
        content = '''\
/// Divide two numbers.
///
/// # Examples
///
/// ```
/// let r = divide(10.0, 2.0);
/// assert_eq!(r, 5.0);
/// ```
pub fn divide(a: f64, b: f64) -> f64 {
    a / b
}
'''
        entries = extract_rust_docs(content, "math.rs")
        e = entries[0]
        assert len(e.examples) > 0
        assert any("assert_eq" in ex for ex in e.examples)

    def test_arguments_section(self):
        content = '''\
/// Print a greeting.
///
/// # Arguments
///
/// * `name` - The name of the person to greet
/// * `times` - How many times to greet
pub fn greet(name: &str, times: usize) {}
'''
        entries = extract_rust_docs(content, "greet.rs")
        e = entries[0]
        assert len(e.params) == 2
        assert e.params[0]["name"] == "name"
        assert "person" in e.params[0]["description"]
        assert e.params[1]["name"] == "times"

    def test_returns_section(self):
        content = '''\
/// Get the length.
///
/// # Returns
///
/// The number of elements in the vector.
pub fn len(&self) -> usize {
    0
}
'''
        entries = extract_rust_docs(content, "vec.rs")
        e = entries[0]
        assert e.returns is not None
        assert "number" in e.returns.lower()

    def test_panics_section(self):
        content = '''\
/// Access element by index.
///
/// # Panics
///
/// Panics if index is out of bounds.
pub fn get(&self, index: usize) -> &i32 {
    todo!()
}
'''
        entries = extract_rust_docs(content, "vec.rs")
        e = entries[0]
        assert "[Panics]" in e.description

    def test_empty_content(self):
        entries = extract_rust_docs("", "empty.rs")
        assert entries == []


# ---------------------------------------------------------------------------
# extract_docs_from_file dispatcher
# ---------------------------------------------------------------------------

class TestExtractDocsFromFile:
    """Tests for the file-level dispatcher extract_docs_from_file."""

    def test_dispatch_typescript(self, tmp_path):
        p = tmp_path / "mod.ts"
        p.write_text(
            '/** A helper. */\nfunction helper() {}\n', encoding="utf-8"
        )
        entries = extract_docs_from_file(str(p))
        assert len(entries) == 1
        assert entries[0].name == "helper"

    def test_dispatch_python(self, tmp_path):
        p = tmp_path / "mod.py"
        p.write_text(
            'def foo():\n    """Do foo."""\n    pass\n', encoding="utf-8"
        )
        entries = extract_docs_from_file(str(p))
        assert len(entries) == 1
        assert entries[0].name == "foo"

    def test_dispatch_go(self, tmp_path):
        p = tmp_path / "mod.go"
        p.write_text(
            '// Run starts the server.\nfunc Run() {}\n', encoding="utf-8"
        )
        entries = extract_docs_from_file(str(p))
        assert len(entries) == 1
        assert entries[0].name == "Run"

    def test_dispatch_java(self, tmp_path):
        p = tmp_path / "Mod.java"
        p.write_text(
            '/** A model. */\npublic class Mod {}\n', encoding="utf-8"
        )
        entries = extract_docs_from_file(str(p))
        assert len(entries) == 1
        assert entries[0].name == "Mod"

    def test_dispatch_rust(self, tmp_path):
        p = tmp_path / "mod.rs"
        p.write_text(
            '/// Do something.\npub fn do_it() {}\n', encoding="utf-8"
        )
        entries = extract_docs_from_file(str(p))
        assert len(entries) == 1
        assert entries[0].name == "do_it"

    def test_nonexistent_file(self):
        entries = extract_docs_from_file("/tmp/__nonexistent_12345__.xyz")
        assert entries == []

    def test_unsupported_extension(self, tmp_path):
        p = tmp_path / "readme.txt"
        p.write_text("Hello world\n", encoding="utf-8")
        entries = extract_docs_from_file(str(p))
        assert entries == []


# ---------------------------------------------------------------------------
# docs_to_markdown conversion
# ---------------------------------------------------------------------------

class TestDocsToMarkdown:
    """Tests for docs_to_markdown."""

    def _entry(self, name, etype, description):
        return DocEntry(
            name=name,
            type=etype,
            description=description,
            params=[],
            returns=None,
            examples=[],
            line_number=1,
            file_path="test.py",
        )

    def test_functions_list(self):
        entries = [
            self._entry("foo", "function", "Do foo."),
            self._entry("bar", "function", "Do bar."),
        ]
        md = docs_to_markdown(entries)
        assert "## 函数" in md
        assert "`foo`" in md
        assert "`bar`" in md
        assert "Do foo." in md

    def test_classes_list(self):
        entries = [
            self._entry("Dog", "class", "A dog."),
            self._entry("Cat", "class", "A cat."),
        ]
        md = docs_to_markdown(entries)
        assert "## 类" in md
        assert "`Dog`" in md
        assert "`Cat`" in md

    def test_types_list(self):
        entries = [
            self._entry("Shape", "type", "A shape."),
            self._entry("Drawable", "interface", "Can be drawn."),
        ]
        md = docs_to_markdown(entries)
        assert "## 类型定义" in md
        assert "`Shape`" in md
        assert "`Drawable`" in md

    def test_empty_list(self):
        md = docs_to_markdown([])
        assert md == ""

    def test_mixed_entries_with_params_and_returns(self):
        entry = DocEntry(
            name="compute",
            type="function",
            description="Compute a value.",
            params=[{"name": "x", "type": "int", "description": "the input"}],
            returns="int: the result",
            examples=[],
            line_number=1,
            file_path="test.py",
        )
        md = docs_to_markdown([entry])
        assert "**参数:**" in md
        assert "`x`" in md
        assert "(int)" in md
        assert "**返回值:**" in md
        assert "the result" in md
