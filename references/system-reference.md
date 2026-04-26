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
| `cache/file-hashes.json` | 文件哈希值缓存，供 `detect-changes` 复用（避免二次全量扫描） |
| `cache/parse-results.json` | tree-sitter AST 摘要缓存（定义列表、复杂度统计、重要行、文档注释），供后续步骤复用避免重复解析 |
| `cache/code-structure.json` | 代码结构提取结果（调用图、代码模式、关键时序、导入关系） |
| `cache/architecture-skeleton.json` | `generate-skeleton` AI段生成的全局架构骨架，供 `extract-docs`～`generate-module-docs` 注入全局上下文（含模块分组、架构分层、关键数据流） |
| `cache/module-analysis.json` | `extract-docs` 语义分析结果缓存（每模块：CodePurpose、公开接口列表、已选文档组件、设计洞察、依赖提示），供 `validate-analysis`、`generate-overview`、依赖综合规则和 `generate-module-docs` 复用 |
| `cache/doc-topology.json` | 文档拓扑规划结果：页面列表、页面类型、阅读顺序、页面覆盖的模块或主题。供 `generate-overview`、`generate-menu`、`generate-module-docs` 优先读取；缺失时允许退回磁盘扫描和骨架推断 |
| `cache/generation-plan.json` | 本轮编译计划：要生成的页面、依赖的缓存文件、受影响页面、可跳过页面。供增量更新、菜单生成和页面编译阶段复用 |
| `cache/evidence-index.json` | 证据索引：关键结论到源码事实的映射（文件、行号、调用链、导入关系、入口链路）。供质量检查和跨页面一致性检查使用 |
| `cache/progress.json` | 分阶段任务状态机（overview/menu/details 三阶段，每模块 pending/in_progress/completed/failed，含 subagent/serial 模式标记） |
| `wiki/overview.md` | 项目概览文档，含项目定位、技术栈、系统架构图、模块列表（`generate-overview` 生成） |
| `wiki/getting-started.md` | 快速开始文档，含前置条件、安装步骤、第一个示例、常见问题 |
| `wiki/doc-map.md` | 文档关系图、阅读路径、依赖矩阵（`generate-menu` 生成） |
| `wiki/menu.json` | 层级化导航菜单（概览 → 理解项目 → 能力导览 → 内部实现 → 参考资料 / 更多），自动由 `generate_menu.py` 生成 |
| `wiki/concepts/` | 自上而下的理解材料：架构、设计思路、关键概念、继续开发心智模型 |
| `wiki/capabilities/` | 面向读者任务和系统能力的源码学习页；每页整合流程、核心逻辑、接口、风险和扩展点 |
| `wiki/internals/` | 内部实现与技术支撑页：基础设施、工具、数据访问、配置、适配器等 |
| `wiki/reference/` | 查阅型资料：接口索引、配置索引、Schema、术语表等 |

## 缓存契约索引

> 下表描述 `.deepwiki/cache/` 中间表示的生产者、消费者、AI 写入边界和增量复用策略。对 skill 而言，这些缓存文件是“源码认知编译链”的事实基础，而不是实现细节。

| 缓存文件 | 生产阶段 | 消费阶段 | 是否允许 AI 写入 | 是否允许增量复用 |
|---------|---------|---------|------------------|------------------|
| `cache/structure.json` | `analyze-project` | `extract-structure`、`generate-skeleton`、`detect-changes`、`plan-doc-topology` | 否 | 是 |
| `cache/file-hashes.json` | `analyze-project` | `detect-changes` | 否 | 是 |
| `cache/parse-results.json` | `extract-structure` | `analyze-project`、后续 AST 相关步骤 | 否 | 是 |
| `cache/code-structure.json` | `extract-structure` | `generate-skeleton`、`extract-docs`、`generate-overview`、`plan-doc-topology`、质量检查 | 否 | 是 |
| `cache/architecture-skeleton.json` | `generate-skeleton` | `extract-docs`、`generate-overview`、`generate-module-docs`、`generate-menu` | 是 | 有条件，建议结合变更重新生成 |
| `cache/module-analysis.json` | `extract-docs` | `validate-analysis`、`generate-overview`、`plan-doc-topology`、`generate-module-docs` | 是 | 是，按模块增量覆盖 |
| `cache/doc-topology.json` | `plan-doc-topology` | `generate-overview`、`generate-menu`、`generate-module-docs`、增量更新 | 是，建议以结构化模板输出 | 是，需按页面或主题局部重算 |
| `cache/generation-plan.json` | `plan-doc-topology` | `generate-overview`、`generate-menu`、`generate-module-docs`、`detect-changes` | 否，优先由脚本生成 | 是 |
| `cache/evidence-index.json` | `validate-analysis`（内部调用 `build-evidence-index`）或文档编译后处理 | `check_doc_quality`、`check_cross_module_consistency` | 否，优先由脚本生成 | 是，按页面或 claim 局部更新 |
| `cache/checksums.json` | `detect-changes` | `detect-changes` | 否 | 是 |
| `cache/progress.json` | 多阶段协作更新 | 全流程恢复与重试 | 否 | 是 |

## 脚本参考（scripts/）

> **重要**：所有脚本均位于 **DeepWiki 技能目录**（本 SKILL.md 所在目录）的 `scripts/` 子目录下，需从技能目录运行，项目路径作为参数传入。

### 脚本列表

| 脚本 | 工作流工具名 | 用途 |
|------|------------|------|
| `scripts/init_wiki.py <项目路径>` | `init-wiki` | 初始化 .deepwiki 目录 |
| `scripts/analyze_project.py <项目路径>` | `analyze-project` | 分析项目结构和技术栈 |
| `scripts/extract_structure.py <项目路径>` | `extract-structure` | 提取调用图、代码模式、关键时序和导入关系 |
| `scripts/detect_changes.py <项目路径>` | `detect-changes` | 检测文件变更，用于增量更新（含反向依赖传播） |
| `scripts/extract_doc_comments.py <文件路径>` | `extract-docs`（预提取子步骤） | 从源码提取文档注释 |
| `scripts/check_analysis_quality.py <项目路径>` | `check-analysis-quality` | 检查 `module-analysis.json` 是否满足最低质量标准（支持 `--verbose` 和 `--json`） |
| `scripts/cli.py validate-analysis <项目路径>` | `validate-analysis` | 对外推荐入口：先执行分析质量门禁，通过后构建 `cache/evidence-index.json` |
| `scripts/build_evidence_index.py <项目路径>` | `build-evidence-index` | 从 `module-analysis.json` 构建 `cache/evidence-index.json`，供文档质量检查验证源码证据 |
| `scripts/finalize.py mermaid <.deepwiki路径>` | `finalize mermaid` | 修复 Mermaid 图表语法错误（支持 `--dry-run` 和 `--json`） |
| `scripts/finalize.py quality <.deepwiki路径>` | `finalize quality` | 检查文档质量（含源码链接有效性验证） |
| `scripts/finalize.py consistency <.deepwiki路径>` | `finalize consistency` | 跨模块一致性检查（接口覆盖率、依赖方向） |
| `scripts/generate_menu.py <wiki目录路径> [项目名称]` | `generate-menu` | 生成层级化导航菜单 menu.json（支持 `--reconcile` 校验模式） |

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

# 提取代码结构（调用图、模式、导入关系）
python scripts/extract_structure.py $PROJECT_DIR

# generate-skeleton：纯 AI 步骤，直接读取 structure.json + code-structure.json 生成骨架
# 无需运行脚本

# 检测文件变更（增量更新时使用；全量生成可跳过或由 extract-docs 内部触发）
python scripts/detect_changes.py $PROJECT_DIR

# extract-docs 阶段的源码注释预提取子步骤
python scripts/extract_doc_comments.py /path/to/src/utils.ts

# validate-analysis：对外推荐入口，先检查分析质量，再构建证据索引
python scripts/cli.py validate-analysis $PROJECT_DIR

# plan-doc-topology：生成文档拓扑和本轮编译计划
python scripts/cli.py plan-doc-topology $PROJECT_DIR

# check-analysis-quality：仅用于调试质量门控子步骤
python scripts/check_analysis_quality.py $PROJECT_DIR
python scripts/check_analysis_quality.py $PROJECT_DIR --verbose
python scripts/check_analysis_quality.py $PROJECT_DIR --json gate-report.json

# build-evidence-index：仅用于调试证据索引子步骤
python scripts/build_evidence_index.py $PROJECT_DIR

# 文档质量检查（基本 / 详细报告 / 导出 JSON）
python scripts/finalize.py quality $PROJECT_DIR/.deepwiki
python scripts/finalize.py quality $PROJECT_DIR/.deepwiki --verbose
python scripts/finalize.py quality $PROJECT_DIR/.deepwiki --json report.json

# 生成导航菜单
python scripts/generate_menu.py $PROJECT_DIR/.deepwiki/wiki "项目名称"

# generate-menu --reconcile：generate-module-docs 全部完成后校验并修正菜单
python scripts/generate_menu.py $PROJECT_DIR/.deepwiki/wiki "项目名称" --reconcile --verbose

# 修复 Mermaid 图表语法
python scripts/finalize.py mermaid $PROJECT_DIR/.deepwiki
python scripts/finalize.py mermaid $PROJECT_DIR/.deepwiki --dry-run
python scripts/finalize.py mermaid $PROJECT_DIR/.deepwiki --json report.json
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
