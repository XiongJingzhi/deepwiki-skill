"""Tests for the prompt-file dispatch contract across subagent workflows."""

from pathlib import Path


ROOT = Path(__file__).parent.parent


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_all_subagent_workflows_require_cached_prompt_file_dispatch():
    """Every subagent workflow should forbid hand-written dispatch prompts."""
    required = [
        "Prompt 文件即唯一输入",
        "必须读取生成的 prompt 文件完整内容",
        "禁止手写、摘要、改写或重新解释 subagent prompt",
        "跳过此步骤视为本阶段失败",
    ]
    workflow_paths = [
        "references/workflow/extract-docs.md",
        "references/workflow/generate-module-docs.md",
        "references/workflow/finalize-wiki.md",
    ]

    for rel_path in workflow_paths:
        text = _read(rel_path)
        for marker in required:
            assert marker in text, f"{rel_path} missing dispatch marker: {marker}"


def test_shared_batch_rules_define_prompt_file_lock():
    """Shared scheduling rules should route subagents through cached prompt files."""
    text = _read("references/rules/batch-scheduling.md")

    assert "Subagent Prompt 文件锁" in text
    assert "cache/prompts/" in text
    assert "FULL content" in text
    assert "DO NOT rewrite" in text


def test_subagent_templates_define_dumb_executor_boundary():
    """Subagents should fail on unclear prompts instead of improvising."""
    template_paths = [
        "references/subagents/extract-docs.md",
        "references/subagents/generate-module-docs.md",
        "references/subagents/quality-fix.md",
    ]

    for rel_path in template_paths:
        text = _read(rel_path)
        assert "纯执行器边界" in text
        assert "不得推断缺失指令" in text
        assert "不要自行补写 prompt" in text
