"""mermaid - Mermaid 图表修复包。

模块结构：
    extractor   - 从 Markdown 提取 mermaid 块 + MermaidBlock 数据类
    fixers      - 正则修复器（fix_flowchart / fix_class_diagram 等）
    validator   - mmdc 语法校验（不可用时自动降级）
    repairer    - AI 修复 Prompt 构建 + error report 管理
    orchestrator - 编排完整修复流程（正则 → 校验 → AI 修复）
"""

from .extractor import MermaidBlock, extract_and_fix, extract_and_fix_file, extract_mermaid_blocks
from .fixers import fix_mermaid_block
from .orchestrator import run, run_apply_fix, run_regex_pass, run_validate_pass
from .repairer import apply_fix, build_prompt, write_error_report
from .validator import ValidationResult, check_mmdc_available, validate_block, validate_blocks

__all__ = [
    # extractor
    "MermaidBlock",
    "extract_mermaid_blocks",
    "extract_and_fix",
    "extract_and_fix_file", 
    # fixers
    "fix_mermaid_block",
    # validator
    "ValidationResult",
    "check_mmdc_available",
    "validate_block",
    "validate_blocks",
    # repairer
    "build_prompt",
    "write_error_report",
    "apply_fix",
    # orchestrator
    "run",
    "run_regex_pass",
    "run_validate_pass",
    "run_apply_fix",
]
