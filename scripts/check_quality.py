#!/usr/bin/env python3
"""
DeepWiki 文档质量检查脚本
检查生成的文档是否符合 v3.0.2 质量标准
"""

import os
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


@dataclass
class QualityMetrics:
    """单个文档的质量指标"""
    file_path: str
    line_count: int = 0
    section_count: int = 0  # H2 章节数
    subsection_count: int = 0  # H3 章节数
    diagram_count: int = 0  # Mermaid 图表数
    class_diagram_count: int = 0  # classDiagram 数量
    code_example_count: int = 0  # 代码示例数
    table_count: int = 0  # 表格数
    cross_link_count: int = 0  # 交叉链接数
    has_source_tracing: bool = False  # 是否有源码追溯
    has_best_practices: bool = False  # 是否有最佳实践章节
    has_performance: bool = False  # 是否有性能优化章节
    has_troubleshooting: bool = False  # 是否有错误处理/调试章节
    source_link_valid_count: int = 0  # 有效的源码链接数
    source_link_broken_count: int = 0  # 失效的源码链接数
    source_link_invalid_lines: int = 0  # 行号超出文件范围的链接数
    source_link_corrected: int = 0  # 可自动修正的链接数
    quality_level: str = "basic"  # basic / standard / professional
    issues: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """质量检查报告"""
    wiki_path: str
    check_time: str
    total_docs: int = 0
    professional_count: int = 0
    standard_count: int = 0
    basic_count: int = 0
    docs: List[QualityMetrics] = field(default_factory=list)
    summary_issues: List[str] = field(default_factory=list)


def analyze_document(file_path: str, structure_path: str = None,
                    project_root: str = None) -> QualityMetrics:
    """分析单个文档的质量"""
    metrics = QualityMetrics(file_path=file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        metrics.issues.append(f"无法读取文件: {e}")
        return metrics

    metrics.line_count = len(lines)

    # 统计 H2 章节 (##)
    metrics.section_count = len(re.findall(r'^## ', content, re.MULTILINE))

    # 统计 H3 章节 (###)
    metrics.subsection_count = len(re.findall(r'^### ', content, re.MULTILINE))

    # 统计 Mermaid 图表
    mermaid_blocks = re.findall(r'```mermaid[\s\S]*?```', content)
    metrics.diagram_count = len(mermaid_blocks)

    # 统计 classDiagram
    metrics.class_diagram_count = len(re.findall(r'classDiagram', content))

    # 统计代码示例 (排除 mermaid)
    all_code_blocks = re.findall(r'```(?!mermaid)[\s\S]*?```', content)
    metrics.code_example_count = len(all_code_blocks)

    # 统计表格：识别表格分隔线（含 --- 的行）来精确计数表格数量
    # Markdown 表格分隔线格式：| --- | --- | 或 |---|---|
    separator_lines = re.findall(r'^\|[\s\-:|]+\|[\s\-:|]*$', content, re.MULTILINE)
    metrics.table_count = len(separator_lines)

    # 统计交叉链接 (排除外部链接)
    internal_links = re.findall(r'\[.*?\]\((?!http).*?\.md.*?\)', content)
    metrics.cross_link_count = len(internal_links)

    # 检查源码追溯
    metrics.has_source_tracing = bool(
        re.search(r'\*\*Section sources\*\*|\*\*Diagram sources\*\*|file://', content)
    )

    # 检查关键章节
    content_lower = content.lower()
    metrics.has_best_practices = bool(
        re.search(r'最佳实践|best practice', content_lower)
    )
    metrics.has_performance = bool(
        re.search(r'性能优化|性能考量|performance', content_lower)
    )
    metrics.has_troubleshooting = bool(
        re.search(r'错误处理|调试|故障排除|troubleshoot|debug', content_lower)
    )

    # 源码链接有效性验证
    if project_root and metrics.has_source_tracing:
        valid, broken = validate_source_links(content, project_root)
        metrics.source_link_valid_count = valid
        metrics.source_link_broken_count = broken
        # 行号有效性验证
        line_result = validate_source_link_with_lines(content, project_root)
        metrics.source_link_invalid_lines = line_result['invalid_lines']
        metrics.source_link_corrected = line_result['corrected']

    # 评估质量等级
    metrics.quality_level = evaluate_quality_level(metrics)

    # 生成问题列表
    metrics.issues = generate_issues(metrics, structure_path=structure_path)

    return metrics


def validate_source_links(content: str, project_root: str) -> Tuple[int, int]:
    """
    验证文档中 file:// 链接指向的源文件是否存在。

    从文档内容中提取所有 file:///path/to/file.ext 和 file:///path/to/file.ext#L行号 链接，
    检查对应的文件在项目目录中是否存在。

    Returns:
        (valid_count, broken_count)
    """
    file_links = re.findall(r'file:///([^)\s#]+)', content)
    if not file_links:
        return 0, 0

    valid = 0
    broken = 0
    seen = set()  # 去重：同一文件链接只检查一次

    for link_path in file_links:
        # 路径还原：Markdown 渲染中反斜杠用于转义
        normalized = link_path.replace('\\', '/')
        if normalized in seen:
            continue
        seen.add(normalized)

        # 尝试在项目根目录下查找文件
        # file:// 路径通常是绝对路径或项目相对路径
        full_path = os.path.normpath(os.path.join(project_root, normalized))

        # 也尝试直接作为绝对路径
        abs_path = os.path.normpath(normalized)

        if os.path.isfile(full_path) or os.path.isfile(abs_path):
            valid += 1
        else:
            broken += 1

    return valid, broken


def validate_source_link_with_lines(content: str, project_root: str) -> Dict[str, int]:
    """
    验证文档中 file:// 链接的文件存在性和行号有效性。

    从文档内容中提取所有 file:///path/to/file.ext#L行号 链接，
    检查文件是否存在，以及行号是否在有效范围内。

    Returns:
        {
            'valid': 有效链接数,
            'broken': 文件不存在的链接数,
            'invalid_lines': 行号超出范围的链接数,
            'corrected': 可自动修正的链接数
        }
    """
    link_pattern = re.compile(r'file:///([^)\s#]+)(?:#L(\d+)(?:-L(\d+))?)?')
    matches = link_pattern.findall(content)
    
    if not matches:
        return {'valid': 0, 'broken': 0, 'invalid_lines': 0, 'corrected': 0}
    
    result = {'valid': 0, 'broken': 0, 'invalid_lines': 0, 'corrected': 0}
    seen = set()
    
    for link_path, line_start, line_end in matches:
        normalized = link_path.replace('\\', '/')
        cache_key = (normalized, line_start, line_end)
        if cache_key in seen:
            continue
        seen.add(cache_key)
        
        full_path = os.path.normpath(os.path.join(project_root, normalized))
        abs_path = os.path.normpath(normalized)
        
        actual_path = None
        if os.path.isfile(full_path):
            actual_path = full_path
        elif os.path.isfile(abs_path):
            actual_path = abs_path
        
        if not actual_path:
            result['broken'] += 1
            continue
        
        if not line_start:
            result['valid'] += 1
            continue
        
        try:
            line_start_int = int(line_start)
            line_end_int = int(line_end) if line_end else line_start_int
            
            with open(actual_path, 'r', encoding='utf-8', errors='ignore') as f:
                total_lines = len(f.readlines())
            
            if line_start_int < 1 or line_end_int > total_lines:
                result['invalid_lines'] += 1
                if line_start_int >= 1 and line_start_int <= total_lines:
                    result['corrected'] += 1
            else:
                result['valid'] += 1
        except Exception:
            result['invalid_lines'] += 1
    
    return result


def evaluate_quality_level(m: QualityMetrics) -> str:
    """基于语义检查清单评估质量等级

    源码追溯是硬性门槛（SKILL.md 强制要求）：
    缺少源码追溯时，质量等级上限为 basic，无论其他指标如何。
    源码链接全部失效时，同样降级为 basic。
    """
    # 源码追溯硬性门槛
    if not m.has_source_tracing:
        return "basic"

    # 源码链接有效性检查：如果存在源码链接但全部失效，降级为 basic
    if m.has_source_tracing and m.source_link_valid_count == 0 and m.source_link_broken_count > 0:
        return "basic"

    must_total = 2
    must_met = 0

    # 必须有（源码追溯已通过门槛，不再计入评分）
    if m.code_example_count >= 1:
        must_met += 1
    if m.section_count >= 3:
        must_met += 1

    should_total = 3
    should_met = 0

    # 建议有
    if m.diagram_count >= 1:
        should_met += 1
    if m.cross_link_count >= 1:
        should_met += 1
    if m.has_troubleshooting:
        should_met += 1

    nice_total = 3
    nice_met = 0

    # 加分项
    if m.has_best_practices:
        nice_met += 1
    if m.has_performance:
        nice_met += 1
    if m.class_diagram_count >= 1:
        nice_met += 1

    # 加权评分: must 50%, should 30%, nice 20%
    score = (must_met / must_total) * 50 + (should_met / should_total) * 30 + (nice_met / nice_total) * 20

    if score >= 80:
        return "professional"
    elif score >= 50:
        return "standard"
    else:
        return "basic"


def calculate_expected_metrics(file_path: str, structure_path: str = None) -> Dict[str, int]:
    """基于模块复杂度动态计算期望指标

    优先从 structure.json 读取 importance_score 作为判断依据，
    仅在无 structure.json 时回退到文件名启发式匹配。
    """
    # 默认期望值
    expected = {
        "min_lines": 100,
        "min_sections": 6,
        "min_diagrams": 1,
        "min_examples": 2,
    }

    file_name = os.path.basename(file_path).replace('.md', '')
    module_name = file_name

    # 尝试从 structure.json 读取模块重要性
    importance_score = None
    if structure_path:
        try:
            with open(structure_path, 'r', encoding='utf-8') as f:
                structure = json.load(f)
            for mod in structure.get('modules', []):
                if mod.get('name') == module_name:
                    importance_score = mod.get('importance_score')
                    break
        except Exception:
            pass

    # 基于客观数据（importance_score）判断
    if importance_score is not None:
        if importance_score >= 0.6:
            expected["min_lines"] = 200
            expected["min_sections"] = 8
            expected["min_diagrams"] = 2
            expected["min_examples"] = 3
        elif importance_score >= 0.4:
            expected["min_lines"] = 120
            expected["min_sections"] = 6
            expected["min_diagrams"] = 1
            expected["min_examples"] = 2
        else:
            expected["min_lines"] = 80
            expected["min_sections"] = 5
            expected["min_diagrams"] = 1
            expected["min_examples"] = 2
        return expected

    # 回退：文件名启发式（仅在无 structure.json 时使用）
    # 索引文件检测
    if file_name in ['index', '_index', 'TOC', 'doc-map']:
        expected["min_lines"] = 50
        expected["min_sections"] = 3
        expected["min_diagrams"] = 1
        expected["min_examples"] = 0
        return expected

    # 核心模块检测（使用更精确的精确匹配，减少误判）
    core_keywords = ['core', 'agent', 'editor', 'main', 'client']
    is_core = file_name.lower() in core_keywords or any(
        file_name.lower() == kw for kw in core_keywords
    )

    # 工具/配置模块检测
    util_keywords = ['util', 'helper', 'common', 'shared', 'constant', 'config', 'type']
    is_util = file_name.lower() in util_keywords or any(
        file_name.lower() == kw for kw in util_keywords
    )

    if is_core:
        expected["min_lines"] = 200
        expected["min_sections"] = 8
        expected["min_diagrams"] = 2
        expected["min_examples"] = 3
    elif is_util:
        expected["min_lines"] = 80
        expected["min_sections"] = 5
        expected["min_diagrams"] = 1
        expected["min_examples"] = 2

    return expected


def generate_issues(m: QualityMetrics, structure_path: str = None) -> List[str]:
    """生成问题列表（基于动态期望值）"""
    issues = []

    # 动态计算期望指标
    expected = calculate_expected_metrics(m.file_path, structure_path=structure_path)
    
    # 基于动态期望值检查
    if m.line_count < expected["min_lines"]:
        issues.append(f"行数不足: {m.line_count}/{expected['min_lines']} (基于模块复杂度)")
    
    if m.section_count < expected["min_sections"]:
        issues.append(f"章节数不足: {m.section_count}/{expected['min_sections']}")
    
    if m.diagram_count < expected["min_diagrams"]:
        issues.append(f"图表数不足: {m.diagram_count}/{expected['min_diagrams']}")
    
    if m.class_diagram_count < 1 and expected["min_diagrams"] >= 2:
        issues.append("核心模块缺少 classDiagram 类图")
    
    if m.code_example_count < expected["min_examples"]:
        issues.append(f"代码示例不足: {m.code_example_count}/{expected['min_examples']}")
    
    if not m.has_source_tracing:
        issues.append("缺少源码追溯 (file:// 链接)")

    if m.source_link_broken_count > 0:
        issues.append(f"失效的源码链接: {m.source_link_broken_count} 个 (有效: {m.source_link_valid_count})")

    if m.source_link_invalid_lines > 0:
        msg = f"行号超出范围的源码链接: {m.source_link_invalid_lines} 个"
        if m.source_link_corrected > 0:
            msg += f" (可自动修正: {m.source_link_corrected})"
        issues.append(msg)

    if m.cross_link_count < 1:
        issues.append("缺少相关文档交叉链接")
    
    return issues


def check_wiki_quality(wiki_path: str) -> QualityReport:
    """检查整个 Wiki 目录的质量"""
    report = QualityReport(
        wiki_path=wiki_path,
        check_time=datetime.now().isoformat()
    )

    wiki_dir = Path(wiki_path) / "wiki"
    if not wiki_dir.exists():
        report.summary_issues.append(f"Wiki 目录不存在: {wiki_dir}")
        return report

    # 自动定位 structure.json 用于模块重要性查询
    structure_path = Path(wiki_path) / "cache" / "structure.json"
    structure_str = str(structure_path) if structure_path.exists() else None

    # 推断项目根目录（.deepwiki 的父目录）
    deepwiki_dir = Path(wiki_path)
    project_root = str(deepwiki_dir.parent) if deepwiki_dir.name == '.deepwiki' else None

    # 遍历所有 .md 文件
    for md_file in wiki_dir.rglob("*.md"):
        metrics = analyze_document(
            str(md_file),
            structure_path=structure_str,
            project_root=project_root,
        )
        report.docs.append(metrics)
        report.total_docs += 1
        
        if metrics.quality_level == "professional":
            report.professional_count += 1
        elif metrics.quality_level == "standard":
            report.standard_count += 1
        else:
            report.basic_count += 1
    
    return report


def print_report(report: QualityReport, verbose: bool = False):
    """打印质量报告"""
    print("\n" + "=" * 60)
    print("📊 DeepWiki 文档质量检查报告")
    print("=" * 60)
    print(f"📁 Wiki 路径: {report.wiki_path}")
    print(f"🕐 检查时间: {report.check_time}")
    print()
    
    # 总体统计
    print("## 📈 总体统计\n")
    print(f"| 指标 | 数值 |")
    print(f"|------|------|")
    print(f"| 文档总数 | {report.total_docs} |")
    print(f"| 🟢 Professional | {report.professional_count} ({report.professional_count/max(1,report.total_docs)*100:.1f}%) |")
    print(f"| 🟡 Standard | {report.standard_count} ({report.standard_count/max(1,report.total_docs)*100:.1f}%) |")
    print(f"| 🔴 Basic | {report.basic_count} ({report.basic_count/max(1,report.total_docs)*100:.1f}%) |")

    # 源码链接有效性汇总
    total_valid = sum(d.source_link_valid_count for d in report.docs)
    total_broken = sum(d.source_link_broken_count for d in report.docs)
    if total_valid > 0 or total_broken > 0:
        print(f"| 源码链接 | 有效: {total_valid} / 失效: {total_broken} |")
    print()
    
    # 需要改进的文档
    basic_docs = [d for d in report.docs if d.quality_level == "basic"]
    standard_docs = [d for d in report.docs if d.quality_level == "standard"]
    
    if basic_docs:
        print("## 🔴 需要升级的文档 (Basic)\n")
        print("| 文档 | 行数 | 章节 | 图表 | 问题数 |")
        print("|------|------|------|------|--------|")
        for doc in basic_docs:
            rel_path = os.path.basename(doc.file_path)
            print(f"| {rel_path} | {doc.line_count} | {doc.section_count} | {doc.diagram_count} | {len(doc.issues)} |")
        print()
    
    if standard_docs:
        print("## 🟡 可优化的文档 (Standard)\n")
        print("| 文档 | 行数 | 章节 | 图表 | 问题数 |")
        print("|------|------|------|------|--------|")
        for doc in standard_docs:
            rel_path = os.path.basename(doc.file_path)
            print(f"| {rel_path} | {doc.line_count} | {doc.section_count} | {doc.diagram_count} | {len(doc.issues)} |")
        print()
    
    # 详细问题列表
    if verbose:
        print("## 📋 详细问题列表\n")
        for doc in report.docs:
            if doc.issues:
                rel_path = os.path.relpath(doc.file_path, report.wiki_path)
                print(f"### {rel_path} [{doc.quality_level.upper()}]\n")
                for issue in doc.issues:
                    print(f"- ⚠️ {issue}")
                print()
    
    # 改进建议
    print("## 💡 改进建议\n")
    if report.basic_count > 0:
        print(f"- 运行 `升级 wiki` 命令升级 {report.basic_count} 个 Basic 级文档")
    if not any(d.has_source_tracing for d in report.docs):
        print("- 添加源码追溯 (Section sources / Diagram sources)")
    if not any(d.class_diagram_count > 0 for d in report.docs):
        print("- 为核心类添加 classDiagram 类图")
    
    print()
    print("=" * 60)
    
    # 返回退出码
    if report.basic_count > report.total_docs * 0.5:
        return 2  # 超过50%是 basic，严重
    elif report.basic_count > 0:
        return 1  # 有 basic 文档，警告
    else:
        return 0  # 全部达标


def save_report_json(report: QualityReport, output_path: str):
    """保存报告为 JSON"""
    data = {
        "wiki_path": report.wiki_path,
        "check_time": report.check_time,
        "summary": {
            "total": report.total_docs,
            "professional": report.professional_count,
            "standard": report.standard_count,
            "basic": report.basic_count
        },
        "docs": []
    }
    
    for doc in report.docs:
        data["docs"].append({
            "file": doc.file_path,
            "metrics": {
                "lines": doc.line_count,
                "sections": doc.section_count,
                "diagrams": doc.diagram_count,
                "class_diagrams": doc.class_diagram_count,
                "code_examples": doc.code_example_count,
                "tables": doc.table_count,
                "cross_links": doc.cross_link_count,
                "has_source_tracing": doc.has_source_tracing,
                "source_link_valid": doc.source_link_valid_count,
                "source_link_broken": doc.source_link_broken_count,
                "has_best_practices": doc.has_best_practices,
                "has_performance": doc.has_performance,
                "has_troubleshooting": doc.has_troubleshooting
            },
            "quality_level": doc.quality_level,
            "issues": doc.issues
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"📄 报告已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="DeepWiki 文档质量检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python check_quality.py /path/to/project/.deepwiki
  python check_quality.py . --verbose
  python check_quality.py . --json report.json
        """
    )
    parser.add_argument(
        "wiki_path",
        nargs="?",
        default=".deepwiki",
        help="Wiki 目录路径 (默认: .deepwiki)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细问题列表"
    )
    parser.add_argument(
        "--json",
        metavar="FILE",
        help="将报告保存为 JSON 文件"
    )
    
    args = parser.parse_args()
    
    # 检查路径
    wiki_path = args.wiki_path
    if not os.path.exists(wiki_path):
        print(f"❌ 路径不存在: {wiki_path}")
        return 1
    
    # 执行检查
    report = check_wiki_quality(wiki_path)
    
    # 打印报告
    exit_code = print_report(report, verbose=args.verbose)
    
    # 保存 JSON
    if args.json:
        save_report_json(report, args.json)
    
    return exit_code


if __name__ == "__main__":
    exit(main())
