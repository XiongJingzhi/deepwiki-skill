"""模块发现与分类 -- 从 analyze_project.py 提取。

负责扫描项目目录结构，发现业务模块，基于文件重要性计算模块优先级。
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Set

from common import IGNORE_DIRS, CODE_EXTENSIONS
from importance_scoring import calculate_file_importance


def _read_workspace_packages(root_path: Path) -> List[str]:
    """读取 monorepo workspace 配置，返回包目录名列表。"""
    packages = []

    # pnpm-workspace.yaml
    pnpm_ws = root_path / "pnpm-workspace.yaml"
    if pnpm_ws.exists():
        try:
            import yaml
            with open(pnpm_ws, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            for pattern in data.get("packages", []):
                if '/*' in pattern:
                    base = pattern.replace('/*', '').strip()
                    if base and (root_path / base).is_dir():
                        packages.append(base)
        except Exception:
            pass

    # package.json workspaces
    pkg = root_path / "package.json"
    if pkg.exists():
        try:
            with open(pkg, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ws = data.get("workspaces", [])
            if isinstance(ws, list):
                for pattern in ws:
                    if '/*' in pattern:
                        base = pattern.replace('/*', '').strip()
                        if base and (root_path / base).is_dir():
                            packages.append(base)
            elif isinstance(ws, dict):
                # npm workspaces as { "packages": [...] }
                for pattern in ws.get("packages", []):
                    if '/*' in pattern:
                        base = pattern.replace('/*', '').strip()
                        if base and (root_path / base).is_dir():
                            packages.append(base)
        except Exception:
            pass

    return packages


def discover_modules(root_path: Path, exclude_dirs: Set[str] = None,
                    all_files: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """发现项目模块，基于文件重要性计算模块优先级

    扫描策略（两阶段）：
    1. 优先扫描 src/lib/packages/apps/modules 等标准源码目录下的直接子目录。
       此阶段不使用 FLAT_ROOT_SKIP，确保 src/config/、src/models/ 等合法业务模块不被误跳过。
    2. 若第一阶段未发现模块（扁平结构项目），则回退到根目录一级扫描。
       此阶段使用 FLAT_ROOT_SKIP 过滤纯工具/文档目录，避免误识别为业务模块。

    重要：FLAT_ROOT_SKIP 只控制「根目录的哪些一级目录不被识别为模块」，
    不影响已选中模块内部的文件计数（防止模块内 config/ 子目录的文件被漏计）。
    """
    if exclude_dirs is None:
        exclude_dirs = IGNORE_DIRS

    # 扁平结构回退时，用于过滤根目录一级非业务目录的集合。
    # 注意：仅用于判断"某个根目录下的一级目录是否应被识别为业务模块"，
    #       不用于过滤模块内部的文件路径。
    FLAT_ROOT_SKIP = {
        'scripts', 'script', 'tools', 'tool',
        'plugins', 'plugin', 'extensions', 'extension',
        'references', 'reference', 'docs', 'doc', 'documentation',
        'assets', 'asset', 'static', 'public',
        'tests', 'test', '__tests__', 'spec', 'specs',
        'examples', 'example', 'samples', 'sample',
        'fixtures', 'mocks', 'stubs',
        'config', 'configs', 'configuration',
        '.github', '.vscode', '.idea',
    }

    modules = []
    src_dirs = ['src', 'lib', 'packages', 'apps', 'modules']

    # ── 阶段 0：读取 monorepo workspace 配置 ─────────────────────────────────
    workspace_dirs = _read_workspace_packages(root_path)
    if workspace_dirs:
        src_dirs = list(set(workspace_dirs + src_dirs))

    # ── 阶段一：扫描标准源码目录下的子目录 ──────────────────────────────────
    # 此阶段只用 exclude_dirs（技术排除目录），不使用 FLAT_ROOT_SKIP，
    # 确保 src/config/、src/models/ 等合法业务模块不被误跳过。
    for src_dir in src_dirs:
        src_path = root_path / src_dir
        if not src_path.exists():
            continue

        for item in src_path.iterdir():
            if item.is_dir() and item.name not in exclude_dirs:
                file_count = sum(
                    1 for f in item.rglob('*')
                    if f.is_file()
                    and f.suffix in CODE_EXTENSIONS
                    and not any(p in f.parts for p in exclude_dirs)
                )
                if file_count > 0:
                    modules.append({
                        'name': item.name,
                        'path': str(item.relative_to(root_path)).replace('\\', '/'),
                        'files': file_count,
                        'type': categorize_module(item.name),
                    })

    # ── 阶段二：扁平结构回退——扫描根目录一级子目录 ──────────────────────────
    # 仅在阶段一未发现任何模块时触发。
    # FLAT_ROOT_SKIP 只用于入口判断（决定该目录是否作为模块），
    # 统计文件数时仍只排除 exclude_dirs，避免模块内同名子目录文件被漏计。
    if not modules:
        root_skip = exclude_dirs | FLAT_ROOT_SKIP
        for item in root_path.iterdir():
            if (item.is_dir()
                    and item.name not in root_skip
                    and not item.name.startswith('.')):
                file_count = sum(
                    1 for f in item.rglob('*')
                    if f.is_file()
                    and f.suffix in CODE_EXTENSIONS
                    and not any(p in f.parts for p in exclude_dirs)  # 只排除技术目录
                )
                if file_count > 0:
                    modules.append({
                        'name': item.name,
                        'path': item.name,
                        'files': file_count,
                        'type': categorize_module(item.name),
                    })

    # 计算模块重要性: 基于模块内文件的平均重要性
    if all_files:
        for mod in modules:
            mod_prefix = mod['path'] + '/'
            mod_files = [f for f in all_files
                        if f['path'].startswith(mod_prefix) or f['path'] == mod['path']]
            if mod_files:
                avg_score = sum(f['importance_score'] for f in mod_files) / len(mod_files)
                core_count = sum(1 for f in mod_files if f['is_core'])
                mod['importance_score'] = round(avg_score, 2)
                mod['core_files_count'] = core_count
                mod['core_files'] = [f['path'] for f in mod_files if f['is_core']][:20]
            else:
                mod['importance_score'] = 0.0
                mod['core_files_count'] = 0
                mod['core_files'] = []

    # 按重要性降序排列
    modules.sort(key=lambda x: x.get('importance_score', 0), reverse=True)

    return modules


def categorize_module(name: str) -> str:
    """根据名称分类模块"""
    name_lower = name.lower()

    if any(k in name_lower for k in ['component', 'ui', 'view', 'page', 'screen']):
        return 'ui'
    elif any(k in name_lower for k in ['api', 'service', 'handler', 'middleware', 'controller', 'router']):
        return 'api'
    elif any(k in name_lower for k in ['migration', 'entity', 'model', 'schema', 'repository', 'dao']):
        return 'data'
    elif any(k in name_lower for k in ['util', 'helper', 'common', 'shared']):
        return 'utility'
    elif any(k in name_lower for k in ['core', 'lib', 'engine', 'kernel']):
        return 'core'
    elif any(k in name_lower for k in ['config', 'setting']):
        return 'config'
    elif any(k in name_lower for k in ['test', 'spec', '__tests__', '__mocks__']):
        return 'test'
    else:
        return 'module'
