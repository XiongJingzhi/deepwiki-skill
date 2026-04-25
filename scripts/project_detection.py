"""项目类型检测、包管理器识别、入口文件发现"""

import json
import re
from pathlib import Path
from typing import List

from common import IGNORE_DIRS


# 项目类型检测规则
PROJECT_INDICATORS = {
    'nodejs': ['package.json'],
    'typescript': ['tsconfig.json', 'tsconfig.*.json'],
    'python': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile'],
    'go': ['go.mod', 'go.sum'],
    'rust': ['Cargo.toml'],
    'java': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
    'ruby': ['Gemfile'],
    'php': ['composer.json'],
    'dotnet': ['*.csproj', '*.fsproj', '*.sln'],
    'react': ['package.json'],  # 需进一步检查依赖
    'vue': ['vue.config.js', 'vite.config.ts', 'nuxt.config.ts'],
    'nextjs': ['next.config.js', 'next.config.mjs', 'next.config.ts'],
}



def detect_package_manager(root_path: Path) -> List[str]:
    """检测包管理器"""
    managers = []
    if (root_path / 'package-lock.json').exists():
        managers.append('npm')
    if (root_path / 'yarn.lock').exists():
        managers.append('yarn')
    if (root_path / 'pnpm-lock.yaml').exists():
        managers.append('pnpm')
    if (root_path / 'bun.lockb').exists():
        managers.append('bun')
    return managers


def detect_monorepo_tools(root_path: Path) -> List[str]:
    """检测 Monorepo 工具"""
    tools = []

    # workspace configs
    if (root_path / 'pnpm-workspace.yaml').exists():
        tools.append('pnpm-workspaces')
        if 'monorepo' not in tools: tools.append('monorepo')

    if (root_path / 'lerna.json').exists():
        tools.append('lerna')
        if 'monorepo' not in tools: tools.append('monorepo')

    if (root_path / 'turbo.json').exists():
        tools.append('turborepo')
        if 'monorepo' not in tools: tools.append('monorepo')

    # check package.json for workspaces
    pkg_path = root_path / 'package.json'
    if pkg_path.exists():
        try:
            with open(pkg_path, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                if 'workspaces' in pkg:
                    tools.append('npm-workspaces') # or yarn/bun workspaces, generic term
                    if 'monorepo' not in tools: tools.append('monorepo')
        except Exception:
            pass

    return tools


def detect_project_types(root_path: Path) -> List[str]:
    """检测项目类型"""
    types = []

    # 基础文件检测
    for project_type, indicators in PROJECT_INDICATORS.items():
        for indicator in indicators:
            if '*' in indicator:
                if list(root_path.glob(indicator)):
                    types.append(project_type)
                    break
            elif (root_path / indicator).exists():
                types.append(project_type)
                break

    # 检测包管理器
    types.extend(detect_package_manager(root_path))

    # 检测 Monorepo
    types.extend(detect_monorepo_tools(root_path))

    # Python 深度检测 (pyproject.toml)
    pyproject_path = root_path / 'pyproject.toml'
    if pyproject_path.exists():
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                tomllib = None

        if tomllib:
            try:
                with open(pyproject_path, 'rb') as f:
                    pyproject = tomllib.load(f)

                    # Detect build system
                    build_backend = pyproject.get('build-system', {}).get('build-backend', '')
                    if 'poetry' in build_backend:
                        types.append('poetry')
                    elif 'pdm' in build_backend:
                        types.append('pdm')
                    elif 'setuptools' in build_backend:
                        types.append('setuptools')
                    elif 'flit' in build_backend:
                        types.append('flit')

                    # Detect specific python frameworks in dependencies
                    # Poetry
                    deps = pyproject.get('tool', {}).get('poetry', {}).get('dependencies', {})
                    # Standard project.dependencies
                    deps_std = pyproject.get('project', {}).get('dependencies', [])

                    all_deps = set()
                    if isinstance(deps, dict):
                        all_deps.update(deps.keys())
                    if isinstance(deps_std, list):
                        # Simple parsing for "package>=1.0"
                        for d in deps_std:
                            match = re.match(r'^([a-zA-Z0-9_-]+)', d)
                            if match:
                                all_deps.add(match.group(1))

                    if 'fastapi' in all_deps:
                        types.append('fastapi')
                    if 'django' in all_deps:
                        types.append('django')
                    if 'flask' in all_deps:
                        types.append('flask')

            except Exception:
                pass

    # Node.js 深度检测 (package.json)
    if 'nodejs' in types or (root_path / 'package.json').exists():
        pkg_path = root_path / 'package.json'
        if pkg_path.exists():
            try:
                with open(pkg_path, 'r', encoding='utf-8') as f:
                    pkg = json.load(f)
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}

                    if 'react' in deps and 'react' not in types:
                        types.append('react')
                    if 'vue' in deps and 'vue' not in types:
                        types.append('vue')
                    if 'next' in deps and 'nextjs' not in types:
                        types.append('nextjs')
                    if 'nuxt' in deps or '@nuxt/core' in deps:
                        types.append('nuxt')
            except Exception:
                pass

    # Rust 深度检测 (Cargo.toml)
    cargo_path = root_path / 'Cargo.toml'
    if cargo_path.exists():
        try:
            with open(cargo_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Simple TOML parsing for dependencies
                # Note: A real TOML parser would be better but requires external lib
                if 'actix-web' in content: types.append('actix-web')
                if 'axum' in content: types.append('axum')
                if 'tokio' in content: types.append('tokio')
                if 'tauri' in content: types.append('tauri')
                if 'rocket' in content: types.append('rocket')
        except Exception:
            pass

    # Go 深度检测 (go.mod)
    go_mod_path = root_path / 'go.mod'
    if go_mod_path.exists():
        try:
            with open(go_mod_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'github.com/gin-gonic/gin' in content: types.append('gin')
                if 'github.com/labstack/echo' in content: types.append('echo')
                if 'github.com/gofiber/fiber' in content: types.append('fiber')
                if 'gorm.io/gorm' in content: types.append('gorm')
        except Exception:
            pass

    return list(set(types))



def find_entry_points(root_path: Path, project_types: List[str]) -> List[str]:
    """识别入口文件"""
    entries = []

    # 常见入口文件
    common_entries = [
        'src/index.ts', 'src/index.tsx', 'src/index.js',
        'src/main.ts', 'src/main.tsx', 'src/main.js',
        'src/App.tsx', 'src/App.vue',
        'app/page.tsx', 'pages/index.tsx', 'pages/index.vue',
        'main.py', 'app.py', 'src/main.py',
        'cmd/main.go', 'internal/main.go', 'main.go',
        'src/main.rs', 'src/lib.rs',
        'src/main/java', 'src/main/kotlin',
        'Program.cs', 'Startup.cs',
    ]

    for entry in common_entries:
        if (root_path / entry).exists():
            entries.append(entry)

    return entries


def detect_project_languages(root_path: Path) -> List[str]:
    """基于文件扩展名频率检测项目主要语言"""
    lang_ext_map = {
        'TypeScript': {'.ts', '.tsx'},
        'JavaScript': {'.js', '.jsx', '.mjs', '.cjs'},
        'Python': {'.py', '.pyi'},
        'Go': {'.go'},
        'Rust': {'.rs'},
        'Java': {'.java'},
        'Kotlin': {'.kt'},
        'C#': {'.cs'},
        'Ruby': {'.rb'},
        'PHP': {'.php'},
        'Scala': {'.scala'},
        'F#': {'.fs'},
        'Vue': {'.vue'},
        'Svelte': {'.svelte'},
    }

    counts = {}
    for ext_group, extensions in lang_ext_map.items():
        count = 0
        for ext in extensions:
            count += sum(1 for f in root_path.rglob(f'*{ext}')
                        if not any(p in f.parts for p in IGNORE_DIRS))
        if count > 0:
            counts[ext_group] = count

    # 按文件数降序排列
    sorted_langs = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [lang for lang, _ in sorted_langs]
