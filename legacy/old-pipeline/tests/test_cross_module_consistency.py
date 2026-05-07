"""Tests for cross-module consistency checks."""

import json
import sys
from pathlib import Path



def _deepwiki(tmp_path: Path) -> Path:
    deepwiki = tmp_path / ".deepwiki"
    (deepwiki / "cache").mkdir(parents=True)
    (deepwiki / "wiki" / "deep-dive").mkdir(parents=True)
    return deepwiki


def test_reports_missing_imported_interface(tmp_path):
    from scripts.quality import check_cross_module_consistency as consistency

    deepwiki = _deepwiki(tmp_path)
    (deepwiki / "cache" / "module-analysis.json").write_text(
        json.dumps(
            {
                "src/auth": {
                    "module_summary": "Auth module",
                    "dependency_hints": {
                        "imports": [
                            {"module": "src/users", "interfaces": ["find_user"]}
                        ]
                    },
                },
                "src/users": {
                    "module_summary": "User module",
                    "dependency_hints": {"imports": []},
                },
            }
        ),
        encoding="utf-8",
    )
    (deepwiki / "wiki" / "deep-dive" / "users.md").write_text(
        "# Users\n\nDocuments `create_user` only.\n",
        encoding="utf-8",
    )

    result = consistency.check_cross_module_consistency(str(deepwiki))

    assert result["passed"]
    assert any(issue["type"] == "missing_interface" for issue in result["warnings"])


def test_reports_bidirectional_cross_section_dependency(tmp_path):
    from scripts.quality import check_cross_module_consistency as consistency

    deepwiki = _deepwiki(tmp_path)
    (deepwiki / "cache" / "module-analysis.json").write_text(
        json.dumps(
            {
                "auth": {
                    "module_summary": "Auth module",
                    "dependency_hints": {
                        "imports": [{"module": "billing", "interfaces": ["charge"]}]
                    },
                },
                "billing": {
                    "module_summary": "Billing module",
                    "dependency_hints": {
                        "imports": [{"module": "auth", "interfaces": ["login"]}]
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (deepwiki / "wiki" / "menu.json").write_text(
        json.dumps(
            {
                "items": [
                    {"title": "Identity", "items": [{"id": "auth"}]},
                    {"title": "Revenue", "items": [{"id": "billing"}]},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = consistency.check_cross_module_consistency(str(deepwiki))

    assert result["passed"]
    assert any(
        issue["type"] == "bidirectional_cross_section"
        for issue in result["infos"]
    )


def test_monorepo_nested_path_uses_generation_plan(tmp_path):
    """跨模块一致性检查应使用 generation-plan.json 中的实际路径，而非硬编码 flat 路径。"""
    from scripts.quality import check_cross_module_consistency as consistency

    deepwiki = _deepwiki(tmp_path)
    # 创建 monorepo 嵌套目录结构
    pkg_dir = deepwiki / "wiki" / "deep-dive" / "coding-agent"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    (deepwiki / "cache" / "module-analysis.json").write_text(
        json.dumps(
            {
                "packages/coding-agent/core": {
                    "module_summary": "Core tools",
                    "dependency_hints": {
                        "imports": [
                            {"module": "packages/coding-agent/utils", "interfaces": ["format"]}
                        ]
                    },
                },
                "packages/coding-agent/utils": {
                    "module_summary": "Utils",
                    "dependency_hints": {"imports": []},
                },
            }
        ),
        encoding="utf-8",
    )
    # generation-plan 中 utils 模块的路径为嵌套路径
    (deepwiki / "cache" / "generation-plan.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "affected_modules": ["packages/coding-agent/utils"],
                        "output_path": "wiki/deep-dive/coding-agent/utils.md",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    # 文档只存在于嵌套路径
    (pkg_dir / "utils.md").write_text(
        "# Utils\n\nDocuments `parse` only.\n", encoding="utf-8"
    )

    result = consistency.check_cross_module_consistency(str(deepwiki))

    # 应通过 generation-plan 找到嵌套路径下的文档，报 missing_interface 而非跳过
    assert any(issue["type"] == "missing_interface" for issue in result["warnings"])
