"""文件重要性评分、归一化"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Union


# ---- archetype 感知权重配置 ----
# 各 archetype 对应的维度权重（path / identity / language / size / import_degree）
ARCHETYPE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "fullstack-framework": {"path": 0.25, "identity": 0.25, "language": 0.25, "size": 0.10, "import_degree": 0.15},
    "agent-project": {"path": 0.20, "identity": 0.30, "language": 0.20, "size": 0.10, "import_degree": 0.20},
    "ml-project": {"path": 0.25, "identity": 0.20, "language": 0.25, "size": 0.10, "import_degree": 0.20},
    "web-service": {"path": 0.30, "identity": 0.25, "language": 0.20, "size": 0.10, "import_degree": 0.15},
    "spa-frontend": {"path": 0.20, "identity": 0.20, "language": 0.25, "size": 0.15, "import_degree": 0.20},
    "cli-tool": {"path": 0.20, "identity": 0.30, "language": 0.25, "size": 0.10, "import_degree": 0.15},
    "sdk-library": {"path": 0.15, "identity": 0.20, "language": 0.30, "size": 0.10, "import_degree": 0.25},
    "data-pipeline": {"path": 0.25, "identity": 0.20, "language": 0.25, "size": 0.10, "import_degree": 0.20},
    "microservice": {"path": 0.25, "identity": 0.25, "language": 0.25, "size": 0.10, "import_degree": 0.15},
    "desktop-app": {"path": 0.25, "identity": 0.25, "language": 0.25, "size": 0.10, "import_degree": 0.15},
    "mobile-app": {"path": 0.25, "identity": 0.25, "language": 0.25, "size": 0.10, "import_degree": 0.15},
    "serverless": {"path": 0.25, "identity": 0.25, "language": 0.25, "size": 0.10, "import_degree": 0.15},
    "generic": {"path": 0.30, "identity": 0.25, "language": 0.30, "size": 0.15, "import_degree": 0.00},
}

# 默认权重（无 archetype 或未识别时使用，import_degree 权重为 0 以保持向后兼容）
DEFAULT_WEIGHTS = ARCHETYPE_WEIGHTS["generic"]


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

# 构建配置扩展名（仅包含以 . 开头的真正扩展名）
BUILD_EXTENSIONS = {
    '.gradle', '.pom', '.xml',
}

# 构建配置文件名（无扩展名或特殊文件名，与 BUILD_EXTENSIONS 分开管理）
BUILD_FILENAMES = {
    'Makefile', 'CMakeLists.txt', 'Cargo.toml', 'go.mod', 'package.json',
    'build.gradle', 'build.gradle.kts',
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


def calculate_file_importance(file_path: Path, root_path: Path, size: int,
                              return_breakdown: bool = False,
                              archetype: Optional[str] = None,
                              import_degree: int = 0) -> Union[float, dict]:
    """
    使用分组互斥加权模型计算文件重要性评分 (0.0 - 1.0)

    将所有因子划分为 5 个独立分组，每组内部互斥取最高分，
    组间加权求和，避免原线性累加模型导致的分数堆叠问题。
    权重根据 archetype 动态调整。

    分组：
    - 路径组：文件所在目录对重要性的贡献，互斥取最高
        src/lib → 1.0 | cmd/bin → 0.8 | 数据库路径 → 0.6 | 根目录 → 0.3
    - 身份组：文件名/路径语义对重要性的贡献，互斥取最高
        入口点(main/index/app/mod) → 1.0 | 业务关键词(文件名) → 0.8
        业务关键词(目录名) → 0.5 | 配置/setup → 0.3
    - 语言组：扩展名对重要性的贡献，互斥取最高
        主要语言(.py/.go/.rs/.java等) → 1.0 | JS/TS/前端 → 1.0
        DB(.sql/.graphql) → 0.9 | 构建文件 → 0.5
        配置(.yaml/.json等) → 0.4 | 样式/模板 → 0.3 | 锁文件 → 0.1
    - 大小组：文件体积对重要性的贡献，互斥取最高
        1KB-50KB(适中) → 1.0 | 100B-1KB(小文件) → 0.5
    - 入度组：文件被其他文件 import 的次数
        10 次以上 → 1.0 | 线性归一化到 0-1

    Args:
        file_path: 文件路径
        root_path: 项目根路径
        size: 文件大小（字节）
        return_breakdown: 是否返回各组分数明细
        archetype: 项目原型标签（如 "web-service"），用于动态调整权重；
                   为 None 时使用默认权重（import_degree 权重为 0，向后兼容）
        import_degree: 该文件被其他文件 import 的次数（入度）

    Returns:
        float: 总分（默认）
        dict: 包含各组分数和总分（return_breakdown=True 时）
    """
    rel_path = str(file_path.relative_to(root_path)).replace('\\', '/')
    rel_lower = rel_path.lower()
    ext = file_path.suffix.lower()
    parts = Path(rel_path).parts
    name_stem = file_path.stem.lower()

    # ── 路径组 (weight=0.30) ─────────────────────────────────────────────────
    # 互斥：取匹配到的最高路径信号
    if 'src' in parts or 'lib' in parts:
        path_score = 1.0
    elif 'cmd' in parts or 'bin' in parts:
        path_score = 0.8
    elif any(k in rel_lower for k in ('database', 'schema', 'migration', 'migrations')):
        path_score = 0.6
    elif len(parts) == 1:
        # 根目录下的文件（如 README.md、go.mod）
        path_score = 0.3
    else:
        path_score = 0.2

    # ── 身份组 (weight=0.25) ─────────────────────────────────────────────────
    # 互斥：文件名/路径语义，取最高信号
    BUSINESS_KEYWORDS = {
        'agent', 'service', 'controller', 'router', 'handler',
        'repository', 'dao', 'entity', 'model', 'middleware',
        'store', 'reducer', 'action', 'selector',
        'client', 'server', 'gateway', 'proxy',
        'factory', 'builder', 'manager', 'provider', 'resolver',
    }
    path_parts_lower = {p.lower() for p in parts}

    if name_stem in ('main', 'index', 'app', 'mod'):
        identity_score = 1.0
    elif name_stem in BUSINESS_KEYWORDS or any(kw in name_stem for kw in BUSINESS_KEYWORDS):
        identity_score = 0.8
    elif path_parts_lower & BUSINESS_KEYWORDS:
        identity_score = 0.5
    elif any(k in rel_lower for k in ('config', 'setup', 'setting')):
        identity_score = 0.3
    else:
        identity_score = 0.0

    # ── 语言组 (weight=0.30) ─────────────────────────────────────────────────
    # 互斥：扩展名优先级，取最高匹配
    if ext in PRIMARY_LANG_EXTENSIONS or ext in JS_TS_EXTENSIONS or ext in FRONTEND_EXTENSIONS:
        lang_score = 1.0
    elif ext in DB_EXTENSIONS:
        lang_score = 0.9
    elif ext in BUILD_EXTENSIONS or file_path.name in BUILD_FILENAMES:
        lang_score = 0.5
    elif ext in CONFIG_EXTENSIONS:
        lang_score = 0.4
    elif ext in STYLE_EXTENSIONS or ext in TEMPLATE_EXTENSIONS:
        lang_score = 0.3
    elif ext in LOCK_EXTENSIONS:
        lang_score = 0.1
    else:
        lang_score = 0.0

    # ── 大小组 (weight=0.15) ─────────────────────────────────────────────────
    # 互斥：文件大小信号
    if 1024 <= size <= 51200:    # 1KB - 50KB，最有价值的大小区间
        size_score = 1.0
    elif 100 <= size < 1024:     # 100B - 1KB，小文件次之
        size_score = 0.5
    else:
        size_score = 0.0

    # ── 入度组 (import_degree) ──────────────────────────────────────────────
    # 归一化到 0-1，10 次以上 import = 最高分
    import_degree_score = min(import_degree / 10.0, 1.0)

    # ── 加权求和（archetype 感知）─────────────────────────────────────────────
    weights = ARCHETYPE_WEIGHTS.get(archetype, DEFAULT_WEIGHTS) if archetype else DEFAULT_WEIGHTS

    score = (
        path_score             * weights["path"] +
        identity_score         * weights["identity"] +
        lang_score             * weights["language"] +
        size_score             * weights["size"] +
        import_degree_score    * weights["import_degree"]
    )
    final_score = round(min(score, 1.0), 4)

    if return_breakdown:
        return {
            'total': final_score,
            'path_score': path_score,
            'identity_score': identity_score,
            'lang_score': lang_score,
            'size_score': size_score,
            'import_degree_score': import_degree_score,
            'weights': dict(weights),
        }
    return final_score


def _percentile_to_score(percentile: float) -> float:
    """将百分位排名转换为归一化分数"""
    if percentile >= 0.90:
        return 1.0
    elif percentile >= 0.70:
        return 0.8
    elif percentile >= 0.50:
        return 0.6
    elif percentile >= 0.30:
        return 0.4
    else:
        return 0.2


def normalize_path_scores(files: List[Dict[str, Any]], modules: List[Dict[str, Any]],
                          archetype: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    模块内百分位归一化 path_score，重新计算重要性评分。

    解决问题：原 path_score 对所有 src/ 下的文件均为 1.0，
    导致 constants.py 和 engine.py 无法区分。

    方法：在每个模块内部，按 raw_path_score 计算百分位排名，
    将百分位映射为归一化后的 path_score_normalized，
    然后使用 archetype 对应的动态权重重新计算总重要性评分。
    import_degree 不参与百分位归一化（它是全局信号），保持原值。

    Args:
        files: 文件列表（需包含 raw_path_score 字段）
        modules: 模块列表（需包含 path 字段）
        archetype: 项目原型标签（如 "web-service"），用于动态调整权重

    Returns:
        更新后的文件列表（含 path_score_normalized 和重新计算的 importance_score）
    """
    if not files or not modules:
        return files

    # 获取 archetype 对应权重
    weights = ARCHETYPE_WEIGHTS.get(archetype, DEFAULT_WEIGHTS) if archetype else DEFAULT_WEIGHTS

    # 按模块分组文件
    for mod in modules:
        mod_path = mod.get('path', '').replace('\\', '/')
        if not mod_path:
            continue

        # 收集属于该模块的文件
        mod_prefix = mod_path + '/'
        mod_files = [f for f in files if f['path'].startswith(mod_prefix) or f['path'] == mod_path]

        if len(mod_files) < 2:
            # 模块内少于 2 个文件，跳过百分位计算，但仍需设置归一化字段和重算评分
            for f in mod_files:
                f['path_score_normalized'] = f.get('raw_path_score', 1.0)
                import_deg_score = f.get('raw_import_degree_score', 0.0)
                new_score = (
                    f['path_score_normalized'] * weights["path"] +
                    f.get('raw_identity_score', 0.0) * weights["identity"] +
                    f.get('raw_lang_score', 0.0) * weights["language"] +
                    f.get('raw_size_score', 0.0) * weights["size"] +
                    import_deg_score * weights["import_degree"]
                )
                f['importance_score'] = round(min(new_score, 1.0), 2)
                f['is_core'] = f['importance_score'] >= 0.5
                f['is_high_priority'] = f['importance_score'] >= 0.6
            continue

        # 计算百分位排名
        path_scores = [f.get('raw_path_score', 0.5) for f in mod_files]
        for f in mod_files:
            raw_score = f.get('raw_path_score', 0.5)
            # 计算百分位：比当前分数低的文件占比
            percentile = sum(1 for s in path_scores if s < raw_score) / len(path_scores)
            f['path_score_normalized'] = _percentile_to_score(percentile)

            # 重新计算重要性评分（使用归一化后的 path_score + archetype 动态权重）
            import_deg_score = f.get('raw_import_degree_score', 0.0)
            new_score = (
                f['path_score_normalized'] * weights["path"] +
                f.get('raw_identity_score', 0.0) * weights["identity"] +
                f.get('raw_lang_score', 0.0) * weights["language"] +
                f.get('raw_size_score', 0.0) * weights["size"] +
                import_deg_score * weights["import_degree"]
            )
            f['importance_score'] = round(min(new_score, 1.0), 2)
            f['is_core'] = f['importance_score'] >= 0.5
            f['is_high_priority'] = f['importance_score'] >= 0.6

    return files
