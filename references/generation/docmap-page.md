# Docmap 生成指南

> **适用工具：** `generate-menu`
> **关联规则：** `../rules/quality-standards.md`、`../rules/components.md`

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

### 新手入门

[步骤列表：首页 → 快速开始 → 核心模块]

### 架构理解

[步骤列表：架构文档 → 模块文档 → 设计决策]

### API 查阅

[步骤列表：API 索引 → 具体 API → 使用示例]

---

## 文档索引

[api-table 变体：按类别列出所有文档]

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

> `menu.json` 定义整个 wiki 的导航层级。由步骤 7 生成，步骤 8 引用各模块在菜单中的位置生成面包屑和前后链接。

### JSON 结构

```json
{
  "version": "1.0",
  "generated_at": "2024-01-01T00:00:00Z",
  "sections": [
    {
      "id": "overview",
      "title": "概览",
      "fixed": true,
      "items": [
        { "id": "home",         "title": "首页",     "path": "index.md" },
        { "id": "architecture", "title": "架构总览", "path": "architecture.md" },
        { "id": "doc-map",      "title": "文档地图", "path": "doc-map.md" },
        { "id": "quickstart",   "title": "快速开始", "path": "quick-start.md" }
      ]
    },
    {
      "id": "auth",
      "title": "认证与鉴权",
      "items": [
        { "id": "auth-core",    "title": "认证核心",   "path": "modules/auth.md" },
        { "id": "permissions",  "title": "权限模型",   "path": "modules/permissions.md" }
      ]
    },
    {
      "id": "contributing",
      "title": "贡献指南",
      "fixed": true,
      "items": [
        { "id": "contributing", "title": "贡献指南", "path": "contributing.md" }
      ]
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `sections[].id` | string | 分区唯一标识（英文，用于锚点） |
| `sections[].title` | string | 面向读者的语义名称（中文或英文） |
| `sections[].fixed` | boolean | `true` = 首尾固定区块，步骤 7 不得调整顺序 |
| `items[].id` | string | 条目唯一标识 |
| `items[].title` | string | 导航显示名称 |
| `items[].path` | string | 相对 `wiki/` 目录的文件路径 |
| `items[].planned` | boolean | `true` = 文档尚未生成（增量模式占位），默认 `false` |

### AI 生成菜单 5 条规则

1. **按读者旅程排序**：首区块"概览"→ 核心业务模块 → 周边模块 → 尾区块"贡献指南"
2. **语义命名**：`title` 面向读者（"认证与鉴权"），不使用路径（"src/auth"）或 CodePurpose 枚举（"Service"）
3. **层级不超过 3 级**：`sections > items`（最多再加一层 `sub-items`），避免深层嵌套
4. **固定首尾**：`"fixed": true` 的 Overview 区块始终最前，Contributing 区块始终最后
5. **增量占位**：增量更新时已知但未生成的文档，添加 `"planned": true`，不留空条目

---
