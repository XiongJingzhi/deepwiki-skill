# Docmap 生成指南

> **适用工具：** `generate-menu`
> **关联规则：** `../rules/quality-standards.md`、`../rules/components-guide.md`

---

## 文档语言

读取项目 `.deepwiki/config.yaml` 中 `generation.language` 的值（`zh` / `en` / `both`），所有文档内容（章节标题、正文、表格、注释说明）必须使用该语言撰写。代码标识符和专有名词保持原文。默认为 `zh`。

---

## 页面骨架（文档地图）

## 文档地图骨架

```markdown
# 文档地图

> {PROJECT_NAME} 文档导航与阅读路径

---

## 文档结构图

[architecture-diagram 变体：文档层级图]

---

## 阅读路径推荐

> **规则**：每个步骤必须是可跳转链接，格式为 `[文档标题](相对路径.md)`。

### 新手入门

1. [项目概览](overview.md) — 了解项目目标和整体架构
2. [快速开始](getting-started.md) — 环境搭建与第一个示例
3. [核心模块](deep-dive/core.md) — 理解最关键的模块

### 架构理解

1. [项目概览](overview.md) — 架构全景与设计决策
2. [核心模块](deep-dive/core.md) — 主流程与核心逻辑
3. [模块依赖关系](#模块依赖矩阵) — 各模块之间的依赖图

### API 查阅

1. [API 接口索引](reference/api-surface.md) — 所有对外接口汇总
2. [核心服务](deep-dive/service.md) — 具体 API 实现细节
3. [使用示例](getting-started.md#示例) — 典型调用场景

### archetype 特化路径

根据项目 archetype 替换或调整阅读路径（以上 3 条路径为 generic 默认值）。
路径中每一步均须替换为实际存在的文档链接：

| archetype | 路径 1 | 路径 2 | 路径 3 |
|-----------|--------|--------|--------|
| web-service | API 速查 | 认证与权限 | 部署运维 |
| fullstack-framework | 前端页面 | 后端 API | 数据层 |
| agent-project | Agent 架构 | 工具注册 | 记忆系统 |
| cli-tool | 命令速查 | 插件开发 | 配置详解 |
| ml-project | 环境搭建 | 训练流程 | 推理部署 |
| sdk-library | 快速上手 | 接口与配置索引 | 高级用法 |
| spa-frontend | 页面路由 | 状态管理 | API 集成 |
| monorepo | 工作区结构 | 核心包文档 | 跨包开发 |
| data-pipeline | 数据源配置 | 流水线构建 | 监控告警 |
| microservice | 服务发现 | 服务间通信 | 数据库迁移 |
| generic | 新手入门 | 架构理解 | API 查阅 |

---

## 文档索引

> **规则**：每个模块条目必须是可跳转链接，格式为 `[文档标题](相对路径.md)`，不得使用纯文本名称。

### 概览

| 文档 | 说明 |
|------|------|
| [项目概览](overview.md) | 项目目标、架构全景、技术栈 |
| [快速开始](getting-started.md) | 环境搭建、第一个示例 |
| [文档地图](doc-map.md) | 本页，导航与阅读路径 |

### 深入理解

| 文档 | 说明 |
|------|------|
| [核心模块](deep-dive/core.md) | 核心逻辑与执行流程 |
| [认证与鉴权](deep-dive/auth.md) | 用户认证决策与权限校验 |
| [数据访问层](deep-dive/dao.md) | 持久化与缓存策略 |

### 参考资料

| 文档 | 说明 |
|------|------|
| [API 接口索引](reference/api-surface.md) | 所有对外接口与配置项汇总 |

---

## 模块依赖矩阵

[decision-table 变体：模块依赖关系]

---

## 更新日志

[链接或简要说明]
```

---

---

## menu.json 模板

## menu.json 模板

> `menu.json` 定义整个 wiki 的导航层级。由 generate-menu 生成，generate-module-docs 引用各模块在菜单中的位置生成面包屑和前后链接。

### JSON 结构

```json
{
  "version": "1.0",
  "generated_at": "2024-01-01T00:00:00Z",
  "items": [
    {
      "title": "概览",
      "items": [
        { "title": "首页",     "path": "overview.md" },
        { "title": "文档地图", "path": "doc-map.md" },
        { "title": "快速开始", "path": "getting-started.md" }
      ]
    },
    {
      "title": "认证与鉴权",
      "items": [
        { "title": "认证核心逻辑", "path": "deep-dive/auth.md" },
        { "title": "权限模型核心逻辑", "path": "deep-dive/permissions.md" }
      ]
    },
    {
      "title": "深入理解",
      "items": [
        {
          "title": "核心引擎",
          "items": [
            { "title": "调度器", "path": "deep-dive/engine/scheduler.md" },
            { "title": "执行器", "path": "deep-dive/engine/executor.md" }
          ]
        },
        {
          "title": "存储层",
          "items": [
            { "title": "数据库访问", "path": "deep-dive/storage/dao.md" },
            { "title": "缓存策略", "path": "deep-dive/storage/cache.md" }
          ]
        }
      ]
    },
    {
      "title": "贡献指南",
      "items": [
        { "title": "贡献指南", "path": "contributing.md" }
      ]
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `items[].title` | string | 面向读者的分区名称（中文或英文） |
| `items[].items` | array | 分区下的导航条目（2 级） |
| `items[].title` | string | 导航显示名称 |
| `items[].path` | string | 相对 `wiki/` 目录的文件路径；支持 `deep-dive/<name>.md`（平铺）或 `deep-dive/<子目录>/<name>.md`（分组）。**叶子节点才有 `path`，有 `items` 子分组的节点不设 `path`** |
| `items[].items` | array | 可选，3 级子菜单条目；仅在模块较多且需要按主题聚合时使用，避免深层嵌套 |
| `items[].planned` | boolean | `true` = 文档尚未生成（增量模式占位），默认 `false` |

### AI 生成菜单 5 条规则

1. **按读者旅程排序**：首区块"概览"→ "理解项目"→ "深入理解"→ "参考资料"→ 尾区块"贡献指南"
2. **语义命名**：`title` 面向读者（"认证与鉴权"），不使用路径（"src/auth"）或 CodePurpose 枚举（"Service"）
3. **层级不超过 3 级**：`items > items`（最多再加一层 `items`）；模块较少时优先平铺，避免无必要的深层嵌套
4. **首区块固定**：概览区块始终最前。尾区块（贡献指南）仅当项目包含 CONTRIBUTING.md 或类似文件时添加，不应强制生成。
5. **增量占位**：增量更新时已知但未生成的文档，添加 `"planned": true`，不留空条目

---
