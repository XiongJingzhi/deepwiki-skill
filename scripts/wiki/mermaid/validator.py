"""validator.py - 调用 mmdc 校验 mermaid 语法。

mmdc 不可用时自动降级，返回 skipped=True，不阻断流程。

公共接口：
    check_mmdc_available() -> bool
    validate_block(diagram_text, block_id) -> ValidationResult
    validate_blocks(blocks) -> List[ValidationResult]
"""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .extractor import MermaidBlock


# mmdc 可用性缓存（进程内单例，避免重复 which 调用）
_MMDC_AVAILABLE: Optional[bool] = None


def check_mmdc_available() -> bool:
    """检查 mmdc（@mermaid-js/mermaid-cli）是否可用。"""
    global _MMDC_AVAILABLE
    if _MMDC_AVAILABLE is None:
        _MMDC_AVAILABLE = shutil.which('mmdc') is not None
    return _MMDC_AVAILABLE


@dataclass
class ValidationResult:
    """单个 mermaid 块的校验结果。"""
    block_id: str
    ok: bool                    # True = 语法正确
    skipped: bool               # True = mmdc 不可用，已跳过
    error_msg: Optional[str]    # mmdc 输出的错误信息
    error_lines: List[int] = field(default_factory=list)  # 出错行号（如能解析）


def validate_block(diagram_text: str, block_id: str = "block") -> ValidationResult:
    """用 mmdc 校验单个 mermaid 块语法。

    流程：
    1. 若 mmdc 不可用，返回 skipped=True。
    2. 将 diagram_text 写入临时文件，调用 mmdc --input ... --output /dev/null。
    3. 解析退出码与 stderr。

    Args:
        diagram_text: 图表文本（不含 ```mermaid 围栏）。
        block_id:     块标识，用于日志。

    Returns:
        ValidationResult
    """
    if not check_mmdc_available():
        return ValidationResult(block_id=block_id, ok=True, skipped=True, error_msg=None)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "diagram.mmd"
        # mmdc 需要 PNG/SVG 输出；/dev/null 在 Windows 下不可用，改用临时 SVG
        output_path = Path(tmpdir) / "out.svg"
        input_path.write_text(diagram_text, encoding='utf-8')

        try:
            result = subprocess.run(
                ['mmdc', '--input', str(input_path), '--output', str(output_path),
                 '--puppeteerConfigFile', '/dev/null'],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                block_id=block_id, ok=False, skipped=False,
                error_msg="mmdc timeout (15s)",
            )
        except Exception as e:
            return ValidationResult(
                block_id=block_id, ok=False, skipped=False,
                error_msg=f"mmdc execution error: {e}",
            )

        if result.returncode == 0:
            return ValidationResult(block_id=block_id, ok=True, skipped=False, error_msg=None)

        # 提取错误信息
        stderr = (result.stderr or '').strip()
        stdout = (result.stdout or '').strip()
        error_msg = stderr or stdout or f"mmdc exit code {result.returncode}"

        # 尝试从错误信息中提取行号
        error_lines = _parse_error_lines(error_msg)

        return ValidationResult(
            block_id=block_id, ok=False, skipped=False,
            error_msg=error_msg, error_lines=error_lines,
        )


def validate_blocks(blocks: List[MermaidBlock]) -> List[ValidationResult]:
    """批量校验多个 mermaid 块。

    若 mmdc 不可用，全部返回 skipped=True（快速短路，不重复检查）。

    Args:
        blocks: MermaidBlock 列表。

    Returns:
        ValidationResult 列表，顺序与 blocks 一致。
    """
    if not check_mmdc_available():
        return [
            ValidationResult(block_id=b.block_id, ok=True, skipped=True, error_msg=None)
            for b in blocks
        ]
    return [validate_block(b.text, b.block_id) for b in blocks]


def _parse_error_lines(error_msg: str) -> List[int]:
    """尝试从 mmdc 错误输出中解析出错行号。"""
    import re
    lines = []
    # 常见格式：line 5, col 10 或 at line 5
    for m in re.finditer(r'\bline[:\s]+(\d+)', error_msg, re.IGNORECASE):
        try:
            lines.append(int(m.group(1)))
        except ValueError:
            pass
    return lines
