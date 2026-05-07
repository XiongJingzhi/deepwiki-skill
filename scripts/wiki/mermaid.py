"""Mermaid extraction, regex repair, and optional mmdc validation."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


MERMAID_RE = re.compile(r"```mermaid\s*\n([\s\S]*?)```", re.MULTILINE)
DIAGRAM_TYPE_RE = re.compile(r"^(classDiagram|sequenceDiagram|stateDiagram(?:-v2)?|erDiagram|flowchart|graph)")
SAFE_ID_RE = re.compile(r"^[A-Za-z_][\w-]*$")
FLOW_NODE_ID = r"(?<![\w-])([A-Za-z_][\w-]*)"


def _resolve_wiki_dir(project_path: str | Path) -> Path:
    root = Path(project_path)
    if root.name == "wiki":
        return root
    deepwiki_wiki = root / ".deepwiki" / "wiki"
    if deepwiki_wiki.exists():
        return deepwiki_wiki
    if (root / "wiki").exists():
        return root / "wiki"
    return root


def extract_mermaid_blocks(content: str, file_stem: str = "doc") -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for index, match in enumerate(MERMAID_RE.finditer(content)):
        text = match.group(1)
        first_line = text.strip().splitlines()[0].strip() if text.strip() else ""
        type_match = DIAGRAM_TYPE_RE.match(first_line)
        blocks.append(
            {
                "block_id": f"{file_stem}:{index}",
                "start": match.start(),
                "end": match.end(),
                "text": text,
                "diagram_type": type_match.group(1) if type_match else "unknown",
            }
        )
    return blocks


def _needs_quoting(text: str) -> bool:
    return bool(text) and not SAFE_ID_RE.match(text)


def _quote(text: str) -> str:
    return f'"{text}"'


def _fix_flowchart(text: str) -> Tuple[str, int]:
    fixes = 0

    def quote_label(label: str) -> str:
        nonlocal fixes
        unwrapped = label.lstrip("([{/<\\")
        if _needs_quoting(label) and not (unwrapped.startswith('"') or unwrapped.startswith("'")):
            fixes += 1
            return _quote(label)
        return label

    def fix_node_shape(pattern: str, formatter):
        def repl(match):
            node_id = match.group(1)
            label = match.group(2)
            quoted = quote_label(label)
            if quoted == label:
                return match.group(0)
            return formatter(node_id, quoted)

        return re.sub(pattern, repl, text)

    patterns = [
        (rf"{FLOW_NODE_ID}\[\(([^\]\n]+?)\)\]", lambda node_id, label: f"{node_id}[({label})]"),
        (rf"{FLOW_NODE_ID}\(([^)\n]+?)\)", lambda node_id, label: f"{node_id}({label})"),
        (rf"{FLOW_NODE_ID}\{{([^}}\n]+?)\}}", lambda node_id, label: f"{node_id}{{{label}}}"),
        (rf"{FLOW_NODE_ID}\[([^\]\n]+?)\]", lambda node_id, label: f"{node_id}[{label}]"),
    ]
    for pattern, formatter in patterns:
        text = fix_node_shape(pattern, formatter)

    def fix_edge_label(match):
        nonlocal fixes
        label = match.group(1)
        if _needs_quoting(label) and not label.startswith('"'):
            fixes += 1
            return f"|{_quote(label)}|"
        return match.group(0)

    text = re.sub(r"\|([^|]+)\|", fix_edge_label, text)
    return text, fixes


def _fix_sequence(text: str) -> Tuple[str, int]:
    fixes = 0

    def repl(match):
        nonlocal fixes
        keyword, alias, name = match.group(1), match.group(2), match.group(3)
        if _needs_quoting(name) and not name.startswith('"'):
            fixes += 1
            return f"{keyword} {alias} as {_quote(name)}"
        return match.group(0)

    text = re.sub(r"^\s*(participant|actor)\s+(\w+)\s+as\s+(.+)$", repl, text, flags=re.MULTILINE)
    return text, fixes


def _fix_class_diagram(text: str) -> Tuple[str, int]:
    fixes = 0

    def fix_tilde(match):
        nonlocal fixes
        raw = match.group(1)
        if "~" not in raw:
            return match.group(0)
        parts = [part for part in raw.split("~") if part]
        if len(parts) < 2:
            return match.group(0)
        display = f"{parts[0]}<{', '.join(parts[1:])}>"
        alias = re.sub(r"\W+", "_", parts[0])
        fixes += 1
        return f'class "{display}" as {alias}'

    text = re.sub(r'class\s+"([^"]+)"', fix_tilde, text)
    return text, fixes


def fix_mermaid_text(text: str) -> Tuple[str, int]:
    stripped = text.lstrip()
    first_line = stripped.splitlines()[0].strip() if stripped else ""
    if first_line.startswith(("flowchart", "graph")):
        return _fix_flowchart(text)
    if first_line.startswith("sequenceDiagram"):
        return _fix_sequence(text)
    if first_line.startswith("classDiagram"):
        return _fix_class_diagram(text)
    return text, 0


def _process_content(content: str, file_stem: str) -> Tuple[str, int, int]:
    blocks = extract_mermaid_blocks(content, file_stem)
    new_content = content
    total_fixes = 0
    for block in reversed(blocks):
        fixed, fixes = fix_mermaid_text(block["text"])
        total_fixes += fixes
        if fixes:
            new_content = new_content[: block["start"]] + f"```mermaid\n{fixed}```" + new_content[block["end"] :]
    return new_content, len(blocks), total_fixes


def check_mmdc_available() -> bool:
    return shutil.which("mmdc") is not None


def _validate_block(text: str) -> Optional[str]:
    if not check_mmdc_available():
        return None
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "diagram.mmd"
        output_path = Path(tmpdir) / "out.svg"
        input_path.write_text(text, encoding="utf-8")
        result = subprocess.run(
            ["mmdc", "--input", str(input_path), "--output", str(output_path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    if result.returncode == 0:
        return None
    return (result.stderr or result.stdout or f"mmdc exit code {result.returncode}").strip()


def process_mermaid(project_path: str | Path, dry_run: bool = False, validate: bool = False) -> Dict[str, Any]:
    wiki_dir = _resolve_wiki_dir(project_path)
    report = {
        "files_checked": 0,
        "blocks": 0,
        "fixes": 0,
        "validation_skipped": validate and not check_mmdc_available(),
        "validation_errors": [],
    }
    for md_file in wiki_dir.rglob("*.md"):
        report["files_checked"] += 1
        content = md_file.read_text(encoding="utf-8", errors="replace")
        fixed_content, block_count, fixes = _process_content(content, md_file.stem)
        report["blocks"] += block_count
        report["fixes"] += fixes
        if fixes and not dry_run:
            md_file.write_text(fixed_content, encoding="utf-8")
            content = fixed_content
        if validate and not report["validation_skipped"]:
            for block in extract_mermaid_blocks(content, md_file.stem):
                error = _validate_block(block["text"])
                if error:
                    report["validation_errors"].append(
                        {"file": str(md_file), "block_id": block["block_id"], "error": error}
                    )

    if report["validation_errors"]:
        state_dir = wiki_dir.parent / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "mermaid-errors.json").write_text(
            json.dumps(report["validation_errors"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Repair and validate Mermaid blocks")
    parser.add_argument("project_path")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)
    report = process_mermaid(args.project_path, dry_run=args.dry_run, validate=args.validate)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
