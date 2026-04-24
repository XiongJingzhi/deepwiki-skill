# 系统参考

> 本文档涵盖两部分：`.deepwiki/` 输出目录结构说明，以及 `scripts/` 辅助脚本的使用参考。

## 输出目录结构（.deepwiki/）

`.deepwiki/` 目录下各文件的用途说明：

| 文件 | 说明 |
|------|------|
| `config.yaml` | 生成设置（语言、排除规则、功能开关） |
| `meta.json` | 生成器版本、时间戳、每个模块的元数据（质量等级、章节数、最后更新时间） |
| `cache/checksums.json` | 文件哈希值，用于增量变更检测（含 `cache_schema_version` 版本控制） |
| `cache/structure.json` | 解析后的项目结构（模块、入口点、技术栈，含 `cache_schema_version` 版本控制） |
| `cache/project-digest.md` | 精简项目概要（`analyze-project` 自动生成），约 3K tokens，供 AI 步骤复用，是 structure.json 的 AI 消费优化视图 |
| `cache/code-structure.json` | 代码结构提取结果（调用图、代码模式、关键时序、导入关系） |
| `cache/architecture-skeleton-input.json` | `generate-skeleton` 脚本段提取的精简摘要，供 AI 生成全局架构骨架时读取（约 5-15K tokens；瞬态文件，仅作为 AI 步骤输入） |
| `cache/architecture-skeleton.json` | `generate-skeleton` AI段生成的全局架构骨架，供 `extract-docs`～`generate-module-docs` 注入全局上下文（含模块分组、架构分层、关键数据流） |
| `cache/module-analysis.json` | `extract-docs` 语义分析结果缓存（每模块：CodePurpose、公开接口列表、已选文档组件、设计洞察、依赖提示），供 `synthesize-deps` 和 `generate-module-docs` 复用 |
| `cache/progress.json` | 分阶段任务状态机（overview/menu/details 三阶段，每模块 pending/in_progress/completed/failed，含 subagent/serial 模式标记） |
| `wiki/overview.md` | 项目概览文档，含项目定位、技术栈、系统架构图、模块列表（`generate-overview` 生成） |
| `wiki/getting-started.md` | 快速开始文档，含前置条件、安装步骤、第一个示例、常见问题 |
| `wiki/doc-map.md` | 文档关系图、阅读路径、依赖矩阵（`generate-menu` 生成） |
| `wiki/menu.json` | 层级化导航菜单（概览 → 模块 → 更多），自动由 `generate_menu.py` 生成 |
| `wiki/modules/` | 每个项目模块一个文件，含深度分析 |
| `wiki/api/` | 每个模块的 API 参考，含签名、类型和示例 |

## 脚本参考（scripts/）

> **重要**：所有脚本均位于 **DeepWiki 技能目录**（本 SKILL.md 所在目录）的 `scripts/` 子目录下，需从技能目录运行，项目路径作为参数传入。

### 脚本列表

| 脚本 | 工作流工具名 | 用途 |
|------|------------|------|
| `scripts/init_wiki.py <项目路径>` | `init-wiki` | 初始化 .deepwiki 目录 |
| `scripts/analyze_project.py <项目路径>` | `analyze-project` | 分析项目结构和技术栈（同时生成 `cache/project-digest.md`） |
| `scripts/extract_structure.py <项目路径>` | `extract-structure` | 提取调用图、代码模式、关键时序和导入关系 |
| `scripts/generate_skeleton.py <项目路径>` | `generate-skeleton` | 从确定性缓存文件提取精简摘要，输出 `cache/architecture-skeleton-input.json` |
| `scripts/detect_changes.py <项目路径>` | `detect-changes` | 检测文件变更，用于增量更新（含反向依赖传播） |
| `scripts/extract_doc_comments.py <文件路径>` | `extract-docs`（预提取子步骤） | 从源码提取文档注释 |
| `scripts/check_analysis_quality.py <项目路径>` | `check-analysis-quality` | 检查 `module-analysis.json` 是否满足最低质量标准（支持 `--verbose` 和 `--json`） |
| `scripts/check_doc_quality.py <.deepwiki路径>` | `generate-module-docs`（收尾质检） | 检查文档质量（含源码链接有效性验证） |
| `scripts/generate_menu.py <wiki目录路径> [项目名称]` | `generate-menu` | 生成层级化导航菜单 menu.json（支持 `--reconcile` 校验模式） |
| `scripts/fix_mermaid.py <.deepwiki路径>` | `generate-module-docs`（Mermaid 修复子步骤） | 修复 Mermaid 图表语法错误（支持 `--dry-run` 和 `--json`） |

### 使用示例

> 请将 `$SKILL_DIR` 替换为本 SKILL.md 所在的实际目录，`$PROJECT_DIR` 替换为目标项目的绝对路径。

```bash
# 切换到技能目录
cd $SKILL_DIR

# 初始化新 wiki
python scripts/init_wiki.py $PROJECT_DIR

# 强制重新初始化（覆盖已有 .deepwiki/ 目录的配置和缓存）
python scripts/init_wiki.py $PROJECT_DIR --force

# 分析项目结构
python scripts/analyze_project.py $PROJECT_DIR

# generate-skeleton：提取架构骨架输入数据（AI 再根据输出生成 architecture-skeleton.json）
python scripts/generate_skeleton.py $PROJECT_DIR

# 检测文件变更
python scripts/detect_changes.py $PROJECT_DIR

# 提取代码结构（调用图、模式、导入关系）
python scripts/extract_structure.py $PROJECT_DIR

# 提取源码注释
python scripts/extract_doc_comments.py /path/to/src/utils.ts

# check-analysis-quality：检查分析质量门控
python scripts/check_analysis_quality.py $PROJECT_DIR
python scripts/check_analysis_quality.py $PROJECT_DIR --verbose
python scripts/check_analysis_quality.py $PROJECT_DIR --json gate-report.json

# 检查文档质量（基本 / 详细报告 / 导出 JSON）
python scripts/check_doc_quality.py $PROJECT_DIR/.deepwiki
python scripts/check_doc_quality.py $PROJECT_DIR/.deepwiki --verbose
python scripts/check_doc_quality.py $PROJECT_DIR/.deepwiki --json report.json

# 生成导航菜单
python scripts/generate_menu.py $PROJECT_DIR/.deepwiki/wiki "项目名称"

# generate-menu --reconcile：generate-module-docs 全部完成后校验并修正菜单
python scripts/generate_menu.py $PROJECT_DIR/.deepwiki/wiki "项目名称" --reconcile --verbose

# 修复 Mermaid 图表语法
python scripts/fix_mermaid.py $PROJECT_DIR/.deepwiki
python scripts/fix_mermaid.py $PROJECT_DIR/.deepwiki --dry-run
python scripts/fix_mermaid.py $PROJECT_DIR/.deepwiki --json report.json
```

### generate_menu.py --reconcile 模式说明

`--reconcile` 模式在 `generate-module-docs` 所有详细文档生成完毕后运行，执行以下操作：

1. 读取已有的 `menu.json`（`generate-menu` 生成的规划菜单）
2. 扫描 `wiki/` 目录下的实际文件
3. **校验并修正**：
   - 用实际文件的 H1 标题替换预设的模块名称
   - 将 `"planned": true` 标记移除（文档已实际生成）
   - 移除规划中存在但实际未生成文档的模块条目
   - 补充实际生成但规划中遗漏的文件（如插件产出的额外文档）
4. 输出校验报告：新增/移除/修改的条目数量
