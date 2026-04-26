"""Tests for cross-module consistency checks."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def _deepwiki(tmp_path: Path) -> Path:
    deepwiki = tmp_path / ".deepwiki"
    (deepwiki / "cache").mkdir(parents=True)
    (deepwiki / "wiki" / "deep-dive").mkdir(parents=True)
    return deepwiki


def test_reports_missing_imported_interface(tmp_path):
    import check_cross_module_consistency as consistency

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
    import check_cross_module_consistency as consistency

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
                "menu": [
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
