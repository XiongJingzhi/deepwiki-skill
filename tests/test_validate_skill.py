from scripts.quality.validate_skill import validate_skill


def test_validate_skill_accepts_clean_root():
    result = validate_skill(".")

    assert result == {"ok": True, "errors": []}


def test_validate_skill_rejects_missing_required_file(tmp_path):
    result = validate_skill(tmp_path)

    assert result["ok"] is False
    assert any("SKILL.md" in error for error in result["errors"])
