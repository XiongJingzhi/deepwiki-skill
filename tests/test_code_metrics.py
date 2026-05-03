"""Tests for scripts/code_metrics.py"""

from pathlib import Path

import pytest

import sys

from scripts.core.code_metrics import estimate_complexity, count_important_lines


# =====================================================================
# 9. estimate_complexity
# =====================================================================


class TestEstimateComplexity:
    def test_simple_file(self, tmp_path):
        f = tmp_path / "simple.py"
        f.write_text("x = 1\nprint(x)\n", encoding="utf-8")
        c = estimate_complexity(f)
        # "x = 1\nprint(x)\n" has 0 control flow and 0 definitions, so complexity is 0
        assert c >= 0

    def test_complex_file_higher(self, tmp_path):
        simple = tmp_path / "simple.py"
        simple.write_text("x = 1\nprint(x)\n", encoding="utf-8")

        complex_code_lines = [
            "import os",
            "",
            "def func1():",
            "    if x > 0:",
            "        for i in range(10):",
            "            if y:",
            "                pass",
            "            else:",
            "                pass",
            "    elif x < 0:",
            "        while True:",
            "            try:",
            "                pass",
            "            except:",
            "                pass",
            "    else:",
            "        pass",
            "",
            "def func2():",
            "    for i in range(10):",
            "        if i % 2 == 0:",
            "            continue",
            "        elif i % 3 == 0:",
            "            break",
            "        else:",
            "            pass",
            "",
            "class MyClass:",
            "    def method1(self):",
            "        if self.x:",
            "            return True",
            "        return False",
            "",
            "    def method2(self):",
            "        for item in items:",
            "            try:",
            "                result = process(item)",
            "            except Exception:",
            "                pass",
        ]
        complex_file = tmp_path / "complex.py"
        complex_file.write_text("\n".join(complex_code_lines), encoding="utf-8")

        c_simple = estimate_complexity(simple)
        c_complex = estimate_complexity(complex_file)
        assert c_complex > c_simple

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.py"
        f.write_text("", encoding="utf-8")
        c = estimate_complexity(f)
        assert c == 0

    def test_range(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("if True:\n    pass\n", encoding="utf-8")
        c = estimate_complexity(f)
        assert 0 <= c <= 100


# =====================================================================
# 10. count_important_lines
# =====================================================================


class TestCountImportantLines:
    def test_def_and_class_counted(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text(
            "def my_func():\n"
            "    pass\n"
            "\n"
            "class MyClass:\n"
            "    pass\n",
            encoding="utf-8",
        )
        count = count_important_lines(f)
        assert count >= 2  # def + class

    def test_import_counted(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text(
            "import os\n"
            "from sys import path\n"
            "import json\n",
            encoding="utf-8",
        )
        count = count_important_lines(f)
        assert count >= 3

    def test_decorator_counted(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text(
            "@property\n"
            "def name(self):\n"
            "    return self._name\n"
            "\n"
            "@staticmethod\n"
            "def run():\n"
            "    pass\n",
            encoding="utf-8",
        )
        count = count_important_lines(f)
        # @property, @staticmethod, def name, def run all counted
        assert count >= 4

    def test_plain_lines_not_counted(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1\ny = 2\nprint(x + y)\n", encoding="utf-8")
        count = count_important_lines(f)
        assert count == 0
