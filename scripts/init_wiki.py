#!/usr/bin/env python3
"""
DeepWiki 初始化脚本
创建 .deepwiki 目录结构和默认配置
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from common import CACHE_SCHEMA_VERSION


def get_default_config() -> str:
    """返回默认配置文件内容"""
    return '''# DeepWiki 配置文件

# 生成选项
generation:
  language: zh                   # zh / en / both
  include_diagrams: true         # 生成 Mermaid 架构图
  include_examples: true         # 包含代码使用示例
  link_to_source: true           # 代码块链接到源码
  max_file_size: 100000          # 跳过大于此大小的文件（字节）

# 排除规则（涵盖所有支持语言的依赖目录与构建产物）
exclude:
  # 通用
  - .git
  - .deepwiki

  # JavaScript / TypeScript / Node.js
  - node_modules          # npm / yarn / pnpm / bun 依赖
  - .pnpm-store
  - dist
  - build
  - out
  - .next                 # Next.js 构建产物
  - .nuxt                 # Nuxt.js 构建产物
  - .svelte-kit           # SvelteKit 构建产物
  - .output               # Nuxt 3 输出
  - coverage
  - .nyc_output
  - .turbo                # Turborepo 缓存

  # Python
  - __pycache__
  - "*.pyc"
  - venv
  - .venv
  - env
  - .env
  - eggs
  - .eggs
  - "*.egg-info"
  - .tox
  - .pytest_cache
  - .mypy_cache
  - .ruff_cache
  - htmlcov               # pytest-cov 报告
  - site-packages

  # Go
  - vendor                # go mod vendor

  # Rust
  - target                # cargo build 产物

  # Java / Kotlin
  - .gradle
  - .gradle-home
  - build                 # Gradle 构建产物（已含）
  - out                   # IntelliJ IDEA 输出（已含）
  - target                # Maven 构建产物（已含）
  - .m2                   # Maven 本地仓库（项目内）
  - classes
  - "*.class"

  # C# / .NET
  - bin
  - obj
  - packages              # NuGet 本地包
  - .vs                   # Visual Studio 缓存

  # Ruby
  - .bundle
  - vendor/bundle         # Bundler 依赖

  # PHP
  - vendor                # Composer 依赖（已含）

  # 通用构建 / 缓存
  - .cache
  - tmp
  - temp
  - logs
  - "*.log"
'''


def get_default_meta() -> dict:
    """返回默认元数据

    modules 字段预定义每个模块的元数据结构，确保 Agent 在运行时
    生成一致的结构而非随机追加字段。
    """
    return {
        "version": "2.1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": None,
        "files_documented": 0,
        "modules_count": 0,
        "modules": {}
    }


def get_default_module_meta() -> dict:
    """返回单个模块的默认元数据模板"""
    return {
        "quality_level": None,    # basic / standard / professional
        "section_count": 0,
        "word_count": 0,
        "diagram_count": 0,
        "last_updated": None
    }


def init_deep_wiki(project_root: str, force: bool = False) -> dict:
    """
    初始化 .deepwiki 目录
    
    Args:
        project_root: 项目根目录
        force: 是否强制重新初始化
        
    Returns:
        初始化结果
    """
    root = Path(project_root)
    wiki_dir = root / ".deepwiki"

    result = {
        "success": True,
        "created": [],
        "skipped": [],
        "message": ""
    }

    # 检查是否已存在
    if wiki_dir.exists():
        if not force:
            result["success"] = False
            result["message"] = ".deepwiki 目录已存在。使用 force=True 重新初始化。"
            return result
        else:
            # 备份现有配置
            config_path = wiki_dir / "config.yaml"
            if config_path.exists():
                backup_path = wiki_dir / "config.yaml.bak"
                shutil.copy(config_path, backup_path)
                result["skipped"].append("config.yaml (已备份)")

    try:
        # 创建目录结构
        directories = [
            ".deepwiki",
            ".deepwiki/cache",
            ".deepwiki/wiki",
            ".deepwiki/wiki/concepts",
            ".deepwiki/wiki/capabilities",
            ".deepwiki/wiki/internals",
            ".deepwiki/wiki/reference",
            ".deepwiki/wiki/assets",
        ]

        for dir_path in directories:
            full_path = root / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                result["created"].append(dir_path)

        # 创建配置文件
        config_path = wiki_dir / "config.yaml"
        if not config_path.exists() or force:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(get_default_config())
            result["created"].append("config.yaml")

        # 创建元数据文件
        meta_path = wiki_dir / "meta.json"
        if not meta_path.exists() or force:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(get_default_meta(), f, indent=2, ensure_ascii=False)
            result["created"].append("meta.json")

        # 创建空的缓存文件
        cache_files = {
            "cache/checksums.json": {"cache_schema_version": CACHE_SCHEMA_VERSION, "checksums": {}},
            "cache/structure.json": {
                "cache_schema_version": CACHE_SCHEMA_VERSION,
                "project_name": "",
                "project_type": [],
                "languages": [],
                "entry_points": [],
                "modules": [],
                "core_files": [],
                "high_priority_files": [],
                "directories": [],
                "file_types": {},
                "size_distribution": {},
                "docs_found": [],
                "stats": {
                    "total_files": 0,
                    "code_files": 0,
                    "core_files_count": 0,
                    "high_priority_files_count": 0,
                    "total_modules": 0,
                    "total_directories": 0,
                    "total_docs": 0
                }
            },
            "cache/progress.json": {
                "cache_schema_version": CACHE_SCHEMA_VERSION,
                "last_updated": None,
                "phases": {
                    "overview": {
                        "status": "pending",
                        "documents": {
                            "overview.md": "pending",
                            "getting-started.md": "pending",
                            "doc-map.md": "pending"
                        }
                    },
                    "analysis": {
                        "status": "pending",
                        "mode": "serial",
                        "modules": {}
                    },
                    "details": {"status": "pending", "modules": {}},
                    "menu": {"status": "pending"}
                }
            },
        }

        for cache_file, default_content in cache_files.items():
            cache_path = wiki_dir / cache_file
            if not cache_path.exists():
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f, indent=2, ensure_ascii=False)
                result["created"].append(cache_file)

        # 创建 .gitignore
        gitignore_path = wiki_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write("cache/\n*.bak\n")
            result["created"].append(".gitignore")

    except (PermissionError, OSError) as e:
        result["success"] = False
        result["message"] = f"初始化失败: {e}"
        return result

    result["message"] = f"成功初始化 .deepwiki 目录，创建了 {len(result['created'])} 个文件/目录"
    return result


def print_result(result: dict):
    """打印初始化结果"""
    if result["success"]:
        print("✅", result["message"])
        if result["created"]:
            print("\n创建的文件/目录:")
            for item in result["created"]:
                print(f"  + {item}")
        if result["skipped"]:
            print("\n跳过的文件:")
            for item in result["skipped"]:
                print(f"  - {item}")
    else:
        print("❌", result["message"])


if __name__ == '__main__':
    import sys
    
    project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    force = '--force' in sys.argv
    
    result = init_deep_wiki(project_path, force)
    print_result(result)
