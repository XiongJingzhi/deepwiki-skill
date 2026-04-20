#!/usr/bin/env python3
"""
项目结构分析脚本 v3.0
扫描项目目录，识别项目类型、模块结构和文档位置
支持文件重要性评分、核心代码识别、目录分析
输出适配 .deepwiki 目录结构
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone

# 忽略的目录
IGNORE_DIRS = {
    'node_modules', '.git', 'dist', 'build', '__pycache__',
    '.next', '.nuxt', 'coverage', '.nyc_output', 'vendor',
    'venv', '.venv', 'env', '.env', 'eggs', '.eggs',
    '.tox', '.cache', '.pytest_cache', '.mypy_cache',
    '.deepwiki', '.agent'
}

# 忽略的文件
IGNORE_FILES = {
    '.DS_Store', 'Thumbs.db', '.gitignore', '.gitattributes',
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'poetry.lock', 'Pipfile.lock', 'composer.lock'
}

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

# 代码文件扩展名
CODE_EXTENSIONS = {
    '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',
    '.py', '.pyi',
    '.go',
    '.rs',
    '.java', '.kt', '.scala',
    '.rb',
    '.php',
    '.cs', '.fs',
    '.vue', '.svelte', '.astro'
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
                        import re
                        for d in deps_std:
                            match = re.match(r'^([a-zA-Z0-9_-]+)', d)
                            if match:
                                all_deps.add(match.group(1))
                                
                    if 'fastapi' in all_deps: types.append('fastapi')
                    if 'django' in all_deps: types.append('django')
                    if 'flask' in all_deps: types.append('flask')
                    
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


def discover_modules(root_path: Path, exclude_dirs: Set[str] = None,
                    all_files: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """发现项目模块，基于文件重要性计算模块优先级"""
    if exclude_dirs is None:
        exclude_dirs = IGNORE_DIRS

    # 根目录扁平结构时，额外跳过这些非业务目录，避免将工具目录误识别为业务模块
    FLAT_STRUCTURE_SKIP = {
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

    for src_dir in src_dirs:
        src_path = root_path / src_dir
        if not src_path.exists():
            continue

        for item in src_path.iterdir():
            if item.is_dir() and item.name not in exclude_dirs:
                file_count = sum(1 for f in item.rglob('*')
                               if f.is_file() and f.suffix in CODE_EXTENSIONS
                               and not any(p in f.parts for p in exclude_dirs))

                if file_count > 0:
                    modules.append({
                        'name': item.name,
                        'path': str(item.relative_to(root_path)).replace('\\', '/'),
                        'files': file_count,
                        'type': categorize_module(item.name),
                    })

    # 如果没有找到明确的模块，尝试根目录下的主要目录（扁平结构）
    if not modules:
        skip_dirs = exclude_dirs | FLAT_STRUCTURE_SKIP
        for item in root_path.iterdir():
            if item.is_dir() and item.name not in skip_dirs and not item.name.startswith('.'):
                file_count = sum(1 for f in item.rglob('*')
                               if f.is_file() and f.suffix in CODE_EXTENSIONS
                               and not any(p in f.parts for p in skip_dirs))
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


# ---- 文件重要性评分因子 ----

# 主要语言扩展名（高权重）
PRIMARY_LANG_EXTENSIONS = {
    '.rs', '.py', '.java', '.kt', '.cpp', '.c', '.go',
    '.rb', '.php', '.swift', '.dart', '.cs',
}

# JS/TS 生态扩展名
JS_TS_EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'}

# 前端框架扩展名
FRONTEND_EXTENSIONS = {'.vue', '.svelte', '.astro', '.wxml', '.ttml'}

# 数据库相关扩展名
DB_EXTENSIONS = {'.sql', '.prisma', '.graphql', '.gql'}

# 构建配置扩展名
BUILD_EXTENSIONS = {
    '.gradle', '.gradle.kts', '.pom', '.xml', 'Makefile',
    'CMakeLists.txt', 'Cargo.toml', 'go.mod', 'package.json',
}

# 配置文件扩展名
CONFIG_EXTENSIONS = {
    '.toml', '.yaml', '.yml', '.json', '.ini', '.env',
    '.properties', '.conf', '.cfg',
}

# 样式文件扩展名
STYLE_EXTENSIONS = {'.css', '.scss', '.sass', '.less', '.styl', '.wxss'}

# 模板/标记扩展名
TEMPLATE_EXTENSIONS = {'.html', '.htm', '.hbs', '.mustache', '.ejs', '.jinja2', '.j2'}

# 锁文件扩展名
LOCK_EXTENSIONS = {'.lock', '.lockb'}


def _should_ignore_path(path: Path) -> bool:
    """检查路径是否应被忽略"""
    return any(part in IGNORE_DIRS for part in path.parts)


def calculate_file_importance(file_path: Path, root_path: Path, size: int) -> float:
    """
    使用加权多因子模型计算文件重要性评分 (0.0 - 1.0)

    因子参考 deepwiki-rs 的重要性评分引擎：
    - 源码目录 (+0.3): 路径包含 src 或 lib
    - 入口点 (+0.2): 路径包含 main 或 index
    - 配置 (+0.1): 路径包含 config 或 setup
    - 适中大小 (+0.2): 文件大小在 1KB - 50KB 之间
    - 语言类型: 根据扩展名加权
    - 数据库路径 (+0.15): 路径包含 database/schema/migrations
    - 锁文件 (+0.05): .lock 扩展名
    - 业务关键词 (+0.15): 路径/文件名包含核心业务角色词（agent/service/controller 等）
    """
    score = 0.0
    rel_path = str(file_path.relative_to(root_path)).replace('\\', '/')
    rel_lower = rel_path.lower()
    ext = file_path.suffix.lower()

    # 路径因子
    parts = Path(rel_path).parts

    # 源码目录
    if 'src' in parts or 'lib' in parts:
        score += 0.3

    # 入口点
    name_stem = file_path.stem.lower()
    if name_stem in ('main', 'index', 'app', 'mod'):
        score += 0.2
    elif 'cmd' in parts or 'bin' in parts:
        score += 0.15

    # 配置
    if any(k in rel_lower for k in ('config', 'setup', 'setting')):
        score += 0.1

    # 业务关键词：文件名/路径包含核心业务角色词时额外加分
    # 参考 deepwiki-rs 的 CodePurpose 分类：Agent/Service/Controller/Router/Repository 等
    BUSINESS_KEYWORDS = {
        'agent', 'service', 'controller', 'router', 'handler',
        'repository', 'dao', 'entity', 'model', 'middleware',
        'store', 'reducer', 'action', 'selector',
        'client', 'server', 'gateway', 'proxy',
        'factory', 'builder', 'manager', 'provider', 'resolver',
    }
    name_lower = file_path.stem.lower()
    path_parts_lower = {p.lower() for p in parts}
    if name_lower in BUSINESS_KEYWORDS or any(kw in name_lower for kw in BUSINESS_KEYWORDS):
        score += 0.15
    elif path_parts_lower & BUSINESS_KEYWORDS:
        score += 0.1  # 目录名匹配时加分略低

    # 文件大小因子
    if 1024 <= size <= 51200:  # 1KB - 50KB
        score += 0.2
    elif 100 <= size < 1024:  # 100B - 1KB
        score += 0.1

    # 扩展名因子
    if ext in PRIMARY_LANG_EXTENSIONS:
        score += 0.3
    elif ext in JS_TS_EXTENSIONS:
        score += 0.3
    elif ext in FRONTEND_EXTENSIONS:
        score += 0.3
    elif ext in DB_EXTENSIONS:
        score += 0.25
    elif ext in BUILD_EXTENSIONS:
        score += 0.15
    elif ext in CONFIG_EXTENSIONS:
        score += 0.1
    elif ext in STYLE_EXTENSIONS:
        score += 0.1
    elif ext in TEMPLATE_EXTENSIONS:
        score += 0.1
    elif ext in LOCK_EXTENSIONS:
        score += 0.05

    # 数据库路径
    if any(k in rel_lower for k in ('database', 'schema', 'migration', 'migrations')):
        score += 0.15

    return min(score, 1.0)


def estimate_complexity(file_path: Path) -> int:
    """
    估算代码复杂度（简化版圈复杂度）

    基于控制流关键字和定义数量：
    - if/elif/else, while, for, match/switch/case, try/except/catch, &&, ||
    - 函数/类/方法定义数量
    返回一个相对值（不严格等于圈复杂度），用于判断文件分析深度。
    """
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return 0

    import re
    lines = content.split('\n')
    non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith(('#', '//', '/*', '*'))]
    loc = len(non_empty_lines)

    # 控制流关键字
    control_flow_pattern = r'\b(if|elif|else|while|for|foreach|match|switch|case|try|except|catch|finally|\.and\(|\.or\()'
    control_flow_count = len(re.findall(control_flow_pattern, content))

    # 函数/方法/类定义
    def_pattern = r'\b(?:def|func|fn|function|method|class|struct|enum|trait|interface|impl|type)\s+\w+'
    def_count = len(re.findall(def_pattern, content))

    # 简化复杂度: (控制流 * 2 + 定义数) 归一化到合理范围
    raw = (control_flow_count * 2 + def_count)
    if loc > 0:
        complexity = min(int(raw * 100 / max(loc, 1)), 100)
    else:
        complexity = 0

    return complexity


def count_important_lines(file_path: Path) -> int:
    """
    统计文件中"重要代码行"数量。

    重要代码行是指含有接口定义、导出声明、导入声明等对文档生成高价值的行。
    参考 deepwiki-rs 的 is_important_line() 设计：这些行在内容截断时会被优先保留。

    重要行关键字：
    - 定义类: def, fn, func, function, class, struct, enum, trait, interface, impl, type
    - 导出类: export, pub, public, module.exports
    - 导入类: import, use, require, include, from ... import
    - 注解类: @decorator, #[attr], TODO, FIXME, NOTE
    """
    import re
    try:
        lines = file_path.read_text(encoding='utf-8', errors='ignore').split('\n')
    except Exception:
        return 0

    # 重要行模式（多语言通用）
    important_patterns = [
        r'^\s*(?:export\s+)?(?:async\s+)?(?:def|fn|func|function)\s+\w+',  # 函数定义
        r'^\s*(?:export\s+)?(?:abstract\s+)?class\s+\w+',                   # 类定义
        r'^\s*(?:pub\s+)?(?:struct|enum|trait|interface|impl)\s+\w+',       # Rust/Go 类型
        r'^\s*(?:export\s+)?type\s+\w+\s*[=<{(]',                          # 类型别名/定义
        r'^\s*(?:export\s+)?(?:const|let|var)\s+\w+.*=',                    # 导出常量
        r'^\s*(?:import|from|use|require|include)\b',                        # 导入语句
        r'^\s*(?:export\s+default|module\.exports)',                         # 模块导出
        r'^\s*@\w+',                                                         # 装饰器/注解
        r'^\s*#\[',                                                           # Rust 属性
        r'(?:TODO|FIXME|HACK|NOTE|WARN|XXX)\s*[:\(]',                       # 重要注释标记
    ]

    count = 0
    for line in lines:
        for pattern in important_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                count += 1
                break  # 一行只计一次

    return count


def scan_files(root_path: Path) -> List[Dict[str, Any]]:
    """
    扫描所有非忽略文件，计算元数据和重要性评分

    返回文件列表，按重要性评分降序排列。
    包含所有文件类型（不仅是代码文件），用于全面的 project view。
    """
    files = []
    for f in root_path.rglob('*'):
        if not f.is_file():
            continue
        if _should_ignore_path(f):
            continue
        if f.name in IGNORE_FILES:
            continue
        # 排除二进制文件
        ext = f.suffix.lower()
        if ext in {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
                   '.woff', '.woff2', '.ttf', '.eot', '.otf',
                   '.zip', '.tar', '.gz', '.rar', '.7z',
                   '.exe', '.dll', '.so', '.dylib', '.bin',
                   '.wasm', '.mp4', '.mp3', '.pdf', '.doc', '.docx'}:
            continue

        try:
            size = f.stat().st_size
        except OSError:
            size = 0

        rel_path = str(f.relative_to(root_path)).replace('\\', '/')
        is_code = ext in CODE_EXTENSIONS
        importance = calculate_file_importance(f, root_path, size)
        complexity = estimate_complexity(f) if is_code else 0
        important_lines = count_important_lines(f) if is_code else 0

        files.append({
            'path': rel_path,
            'name': f.name,
            'size': size,
            'extension': ext,
            'is_code': is_code,
            'importance_score': round(importance, 2),
            'complexity_score': complexity,
            'important_lines_count': important_lines,
            'is_core': importance >= 0.5,
            # 高优先级档位：score >= 0.6，用于关系分析和深度分析阶段的精确过滤
            # 参考 deepwiki-rs：关系分析阶段仅处理 importance_score >= 0.6 的文件
            'is_high_priority': importance >= 0.6,
        })

    # 按重要性评分降序
    files.sort(key=lambda x: x['importance_score'], reverse=True)
    return files


def scan_directories(root_path: Path) -> List[Dict[str, Any]]:
    """
    扫描目录结构，计算目录重要性评分

    因子:
    - 核心源码 (+0.4): 名称为 src 或 lib
    - 核心模块 (+0.3): 名称包含 core 或 main
    - 文件丰富 (+0.2): 包含超过 5 个代码文件
    - 深层嵌套 (+0.1): 包含超过 2 个子目录
    """
    directories = []
    for dir_path in root_path.rglob('*'):
        if not dir_path.is_dir():
            continue
        if _should_ignore_path(dir_path):
            continue

        rel_path = str(dir_path.relative_to(root_path)).replace('\\', '/')
        name = dir_path.name

        try:
            code_file_count = sum(
                1 for f in dir_path.iterdir()
                if f.is_file() and f.suffix in CODE_EXTENSIONS
            )
            subdir_count = sum(
                1 for d in dir_path.iterdir()
                if d.is_dir() and d.name not in IGNORE_DIRS and not d.name.startswith('.')
            )
        except PermissionError:
            continue

        # 目录重要性评分
        score = 0.0
        if name in ('src', 'lib', 'pkg', 'cmd', 'internal'):
            score += 0.4
        if any(k in name.lower() for k in ('core', 'main', 'engine', 'kernel')):
            score += 0.3
        if code_file_count > 5:
            score += 0.2
        elif code_file_count > 0:
            score += 0.1
        if subdir_count > 2:
            score += 0.1

        directories.append({
            'path': rel_path,
            'name': name,
            'file_count': code_file_count,
            'subdirectory_count': subdir_count,
            'importance_score': round(min(score, 1.0), 2),
        })

    # 按重要性降序
    directories.sort(key=lambda x: x['importance_score'], reverse=True)
    return directories


def compute_file_stats(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算文件类型分布和大小分布统计"""
    # 文件类型分布（仅代码文件）
    file_types: Dict[str, int] = {}
    for f in files:
        if f['is_code']:
            ext = f['extension']
            file_types[ext] = file_types.get(ext, 0) + 1

    # 按数量降序排列
    file_types = dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True))

    # 大小分布
    size_distribution = {'tiny': 0, 'small': 0, 'medium': 0, 'large': 0}
    for f in files:
        size = f['size']
        if size < 1024:         # < 1KB
            size_distribution['tiny'] += 1
        elif size < 10240:      # 1KB - 10KB
            size_distribution['small'] += 1
        elif size < 51200:      # 10KB - 50KB
            size_distribution['medium'] += 1
        else:                   # > 50KB
            size_distribution['large'] += 1

    return {
        'file_types': file_types,
        'size_distribution': size_distribution,
    }


def find_documentation(root_path: Path) -> List[str]:
    """发现现有文档"""
    doc_patterns = [
        'README.md', 'README.*.md', 'readme.md',
        'CHANGELOG.md', 'HISTORY.md', 'changelog.md',
        'CONTRIBUTING.md', 'ARCHITECTURE.md', 'DESIGN.md',
        'API.md', 'SECURITY.md', 'LICENSE', 'LICENSE.md',
        'docs/*.md', 'documentation/*.md'
    ]
    
    docs = []
    for pattern in doc_patterns:
        if '*' in pattern:
            docs.extend(str(p.relative_to(root_path)) for p in root_path.glob(pattern))
        elif (root_path / pattern).exists():
            docs.append(pattern)
    
    return docs


def analyze_project(project_root: str, save_to_cache: bool = True) -> Dict[str, Any]:
    """
    完整分析项目结构

    Args:
        project_root: 项目根目录
        save_to_cache: 是否保存到 .deepwiki/cache/structure.json

    Returns:
        项目结构数据（含文件级元数据、重要性评分、核心文件识别）
    """
    root = Path(project_root)

    # 检测项目类型
    project_types = detect_project_types(root)

    # 检测项目主要语言
    languages = detect_project_languages(root)

    # 发现入口文件
    entry_points = find_entry_points(root, project_types)

    # 扫描所有文件（含重要性评分和复杂度估算）
    all_files = scan_files(root)

    # 核心文件: importance_score >= 0.5
    core_files = [f for f in all_files if f['is_core']]

    # 高优先级文件: importance_score >= 0.6（用于关系分析和深度分析的精确过滤）
    high_priority_files = [f for f in all_files if f.get('is_high_priority')]

    # 发现模块（传入文件数据用于计算模块重要性）
    modules = discover_modules(root, all_files=all_files)

    # 发现文档
    docs = find_documentation(root)

    # 扫描目录
    directories = scan_directories(root)

    # 文件统计
    file_stats = compute_file_stats(all_files)

    # 仅代码文件列表（用于向后兼容）
    code_file_count = sum(1 for f in all_files if f['is_code'])

    result = {
        'project_name': root.name,
        'project_type': project_types,
        'languages': languages,
        'entry_points': entry_points,
        'modules': modules,
        'core_files': core_files,
        'high_priority_files': high_priority_files,
        'directories': directories,
        'file_types': file_stats['file_types'],
        'size_distribution': file_stats['size_distribution'],
        'docs_found': docs,
        'stats': {
            'total_files': len(all_files),
            'code_files': code_file_count,
            'core_files_count': len(core_files),
            'high_priority_files_count': len(high_priority_files),
            'total_modules': len(modules),
            'total_directories': len(directories),
            'total_docs': len(docs),
        },
        'analyzed_at': datetime.now(timezone.utc).isoformat()
    }

    # 保存到缓存
    if save_to_cache:
        wiki_dir = root / '.deepwiki'
        if wiki_dir.exists():
            cache_path = wiki_dir / 'cache' / 'structure.json'
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def print_analysis(result: Dict[str, Any]):
    """打印分析结果"""
    stats = result['stats']
    print(f"项目: {result['project_name']}")
    print(f"技术栈: {', '.join(result['project_type']) or '未知'}")
    if result.get('languages'):
        print(f"语言: {', '.join(result['languages'])}")
    print(f"统计: {stats['code_files']} 个代码文件, "
          f"{stats['core_files_count']} 个核心文件, "
          f"{stats['high_priority_files_count']} 个高优先级文件, "
          f"{stats['total_modules']} 个模块, "
          f"{stats['total_files']} 个总文件")

    if result['entry_points']:
        print(f"\n入口文件:")
        for entry in result['entry_points']:
            print(f"  - {entry}")

    if result['modules']:
        print(f"\n模块 (按重要性排序):")
        for module in result['modules'][:10]:
            score = module.get('importance_score', 0)
            core = module.get('core_files_count', 0)
            print(f"  - {module['name']} ({module['files']} 文件, "
                  f"重要性: {score}, 核心文件: {core})")

    if result.get('high_priority_files'):
        print(f"\n高优先级文件 (importance >= 0.6, 用于关系分析):")
        for f in result['high_priority_files'][:10]:
            print(f"  - {f['path']} (评分: {f['importance_score']}, "
                  f"复杂度: {f['complexity_score']}, 重要行: {f['important_lines_count']})")
        if len(result['high_priority_files']) > 10:
            print(f"  ... 共 {len(result['high_priority_files'])} 个高优先级文件")

    if result.get('core_files'):
        print(f"\n核心文件 (importance >= 0.5):")
        for f in result['core_files'][:15]:
            print(f"  - {f['path']} (评分: {f['importance_score']}, "
                  f"复杂度: {f['complexity_score']}, 重要行: {f['important_lines_count']})")
        if len(result['core_files']) > 15:
            print(f"  ... 共 {len(result['core_files'])} 个核心文件")

    if result['docs_found']:
        print(f"\n现有文档:")
        for doc in result['docs_found']:
            print(f"  - {doc}")

    if result.get('file_types'):
        print(f"\n文件类型分布:")
        for ext, count in list(result['file_types'].items())[:8]:
            print(f"  - {ext}: {count}")


if __name__ == '__main__':
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    result = analyze_project(project_path, save_to_cache=False)
    print_analysis(result)
