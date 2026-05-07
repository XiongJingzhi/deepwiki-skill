"""Tests for scripts.wiki.postprocess command dispatch."""

import sys
from pathlib import Path

import pytest



def _run_finalize(monkeypatch, argv, returncode=0):
    from scripts.wiki import postprocess as finalize

    calls = []

    class Result:
        def __init__(self, code):
            self.returncode = code

    def fake_run(cmd):
        calls.append(cmd)
        return Result(returncode)

    monkeypatch.setattr(sys, "argv", ["finalize.py"] + argv)
    monkeypatch.setattr(finalize.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as exc:
        finalize.main()

    return exc.value.code, calls


def test_finalize_dispatches_mermaid_with_options(monkeypatch, tmp_path):
    code, calls = _run_finalize(
        monkeypatch,
        ["mermaid", str(tmp_path), "--dry-run", "--validate", "--json", "report.json", "-v"],
    )

    assert code == 0
    assert len(calls) == 1
    cmd = calls[0]
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "scripts.wiki.fix_mermaid"]
    assert cmd[3:] == [str(tmp_path), "--dry-run", "--validate", "--json", "report.json", "-v"]


def test_finalize_dispatches_quality(monkeypatch, tmp_path):
    code, calls = _run_finalize(
        monkeypatch,
        ["quality", str(tmp_path), "--verbose", "--json", "quality.json"],
        returncode=1,
    )

    assert code == 1
    cmd = calls[0]
    assert cmd[1:3] == ["-m", "scripts.quality.check_doc_quality"]
    assert cmd[3:] == [str(tmp_path), "--verbose", "--json", "quality.json"]


def test_finalize_dispatches_consistency(monkeypatch, tmp_path):
    code, calls = _run_finalize(
        monkeypatch,
        ["consistency", str(tmp_path), "--json", "consistency.json"],
    )

    assert code == 0
    cmd = calls[0]
    assert cmd[1:3] == ["-m", "scripts.quality.check_cross_module_consistency"]
    assert cmd[3:] == [str(tmp_path), "--json", "consistency.json"]

