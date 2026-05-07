"""Tests for user-forced serial DeepWiki generation."""

from pathlib import Path


ROOT = Path(__file__).parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_skill_declares_serial_generation_as_hard_switch():
    text = _read("SKILL.md")

    assert "串行生成文档" in text
    assert "全量串行生成" in text
    assert "不得调用、派遣、spawn subagent" in text
    assert "用户指定串行优先" in text


def test_batch_scheduling_disables_subagents_when_user_requests_serial():
    text = _read("references/rules/batch-scheduling.md")

    assert "并行阈值全部失效" in text
    assert "不得派遣或 spawn subagent" in text
    assert '"mode": "serial"' in text


def test_subagent_workflows_define_serial_entrypoint():
    for rel_path in [
        "references/workflow/extract-docs.md",
        "references/workflow/generate-module-docs.md",
    ]:
        text = _read(rel_path)
        assert "## 串行模式" in text
        assert "串行生成文档" in text
        assert "禁止调用 `spawn_agent`" in text
