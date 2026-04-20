# Wiki 页面模板

本文件包含用于生成专业 Wiki 页面的 Markdown 模板。

> **AI 指引**：在以下所有代码示例中，请使用**项目的主要编程语言**。将通用占位符替换为目标项目的实际语法。所有代码围栏应使用检测到的语言标识符。

---

## 目录

1. [首页模板](#首页模板)
2. [架构模板](#架构模板)
3. [模块模板](#模块模板)
4. [API 参考模板](#api-参考模板)
5. [快速开始模板](#快速开始模板)
6. [文档地图模板](#文档地图模板)

---

## 首页模板

```markdown
# {{ PROJECT_NAME }}

[![Tech](https://img.shields.io/badge/Tech-{{ TECH_STACK }}-blue)](#tech-stack)
[![Version](https://img.shields.io/badge/Version-{{ VERSION }}-green)](#)

> {{ PROJECT_DESCRIPTION }}

---

## 概述

{{ PROJECT_INTRODUCTION }}

本项目解决以下挑战：
- **挑战 1**：描述...
- **挑战 2**：描述...

典型用例：
- 用例 1
- 用例 2

---

## 架构预览

> 完整的架构详情请参阅 [架构文档](architecture.md)

\`\`\`mermaid
flowchart TB
    subgraph Core["Core Layer"]
        {{ CORE_MODULES }}
    end
    subgraph Support["Support Layer"]
        {{ SUPPORT_MODULES }}
    end
    Core --> Support
    click Core "architecture.md"
\`\`\`

---

## 文档导航

| 分类 | 文档 | 描述 | 适用人群 |
|------|------|------|---------|
| 快速开始 | [快速入门](getting-started.md) | 安装指南 | 新用户 |
| 架构 | [架构文档](architecture.md) | 系统设计 | 架构师、开发者 |
| 模块 | [模块文档](modules/_index.md) | 模块详情 | 开发者 |
| API | [API 参考](api/_index.md) | 完整 API 文档 | 开发者 |
| 索引 | [文档地图](doc-map.md) | 阅读路径 | 所有人 |

---

## 核心特性

| 特性 | 描述 | 模块 |
|------|------|------|
| **{{ FEATURE_1_NAME }}** | {{ FEATURE_1_DESC }} | [`module1`](modules/module1.md) |
| **{{ FEATURE_2_NAME }}** | {{ FEATURE_2_DESC }} | [`module2`](modules/module2.md) |
| **{{ FEATURE_3_NAME }}** | {{ FEATURE_3_DESC }} | [`module3`](modules/module3.md) |

---

## 快速开始

### 安装

\`\`\`bash
{{ INSTALL_COMMAND }}
\`\`\`

### 基本用法

\`\`\`{{ LANG }}
{{ QUICK_EXAMPLE }}
\`\`\`

> 更多示例请参阅 [快速入门指南](getting-started.md)

---

## 项目结构

\`\`\`
{{ PROJECT_NAME }}/
├── {{ DIR_1 }}/              # {{ DIR_1_DESC }}
├── {{ DIR_2 }}/              # {{ DIR_2_DESC }}
├── {{ DIR_3 }}/              # {{ DIR_3_DESC }}
└── {{ CONFIG_FILES }}        # 配置文件
\`\`\`

---

## 核心模块

| 模块 | 职责 | 文档 | API |
|------|------|------|-----|
| [{{ MODULE_1 }}](modules/{{ MODULE_1 }}.md) | {{ MODULE_1_DESC }} | [文档](modules/{{ MODULE_1 }}.md) | [API](api/{{ MODULE_1 }}.md) |
| [{{ MODULE_2 }}](modules/{{ MODULE_2 }}.md) | {{ MODULE_2_DESC }} | [文档](modules/{{ MODULE_2 }}.md) | [API](api/{{ MODULE_2 }}.md) |
| [{{ MODULE_3 }}](modules/{{ MODULE_3 }}.md) | {{ MODULE_3_DESC }} | [文档](modules/{{ MODULE_3 }}.md) | [API](api/{{ MODULE_3 }}.md) |

---

## 技术栈

| 分类 | 技术 | 用途 |
|------|------|------|
| {{ TECH_CATEGORY_1 }} | {{ TECH_1 }} | {{ PURPOSE_1 }} |
| {{ TECH_CATEGORY_2 }} | {{ TECH_2 }} | {{ PURPOSE_2 }} |

---

## 相关链接

- [更新日志](CHANGELOG.md)
- [许可证](LICENSE)
- {{ EXTERNAL_LINKS }}

---

*由 [DeepWiki v{{ DEEP_WIKI_VERSION }}](https://github.com/trsoliu/deepwiki) 自动生成 | {{ GENERATED_AT }}*
```

---

## 架构模板

```markdown
# 架构

> {{ PROJECT_NAME }} 技术架构概述

---

## 概要

### 定位

{{ PROJECT_POSITIONING }}

### 架构风格

本项目采用 **{{ ARCHITECTURE_STYLE }}** 架构：
- {{ ARCH_FEATURE_1 }}
- {{ ARCH_FEATURE_2 }}

---

## 系统架构图

\`\`\`mermaid
flowchart TB
    subgraph Presentation["Presentation Layer"]
        UI["UI Components"]
        Pages["Pages / Routes"]
    end
    subgraph Business["Business Layer"]
        Services["Services"]
        Models["Models"]
    end
    subgraph Data["Data Layer"]
        API["API Client"]
        Store["State Management"]
    end
    subgraph Infrastructure["Infrastructure"]
        Utils["Utilities"]
        Config["Configuration"]
        Logger["Logging"]
    end
    Presentation --> Business
    Business --> Data
    Data --> Infrastructure
    Business --> Infrastructure

    style Presentation fill:#e1f5fe
    style Business fill:#fff3e0
    style Data fill:#e8f5e9
    style Infrastructure fill:#f3e5f5
\`\`\`

---

## 技术栈

| 分类 | 技术 | 版本 | 原因 |
|------|------|------|------|
| {{ CATEGORY_1 }} | {{ TECH_1 }} | {{ VERSION_1 }} | {{ REASON_1 }} |
| {{ CATEGORY_2 }} | {{ TECH_2 }} | {{ VERSION_2 }} | {{ REASON_2 }} |

---

## 模块依赖

\`\`\`mermaid
flowchart LR
    subgraph Core["Core"]
        A["{{ MODULE_A }}"]
        B["{{ MODULE_B }}"]
    end
    subgraph Features["Features"]
        C["{{ MODULE_C }}"]
        D["{{ MODULE_D }}"]
    end
    subgraph Utils["Utilities"]
        E["{{ MODULE_E }}"]
    end
    A --> E
    B --> E
    C --> A
    C --> B
    D --> B
\`\`\`

### 模块详情

#### {{ MODULE_A }}

| 属性 | 值 |
|------|-----|
| **路径** | `{{ MODULE_A_PATH }}` |
| **职责** | {{ MODULE_A_RESPONSIBILITY }} |
| **文档** | [模块](modules/{{ MODULE_A }}.md) \| [API](api/{{ MODULE_A }}.md) |

#### {{ MODULE_B }}

| 属性 | 值 |
|------|-----|
| **路径** | `{{ MODULE_B_PATH }}` |
| **职责** | {{ MODULE_B_RESPONSIBILITY }} |
| **文档** | [模块](modules/{{ MODULE_B }}.md) \| [API](api/{{ MODULE_B }}.md) |

---

## 数据流

\`\`\`mermaid
sequenceDiagram
    autonumber
    participant User
    participant UI
    participant Service
    participant API
    participant Server
    User->>UI: Trigger action
    UI->>Service: Call method
    Service->>Service: Validate
    Service->>API: Request
    API->>Server: HTTP call
    Server-->>API: Response
    API-->>Service: Parse
    Service-->>UI: Update state
    UI-->>User: Render
\`\`\`

---

## 目录结构

\`\`\`
{{ PROJECT_NAME }}/
├── src/                    # 源代码
│   ├── components/         # UI 组件
│   ├── services/           # 业务逻辑
│   ├── utils/              # 工具函数
│   └── config/             # 配置
├── tests/                  # 测试
└── scripts/                # 构建脚本
\`\`\`

---

## 设计模式

| 模式 | 使用位置 | 相关模块 |
|------|---------|---------|
| **{{ PATTERN_1 }}** | {{ PATTERN_1_USAGE }} | {{ PATTERN_1_MODULES }} |
| **{{ PATTERN_2 }}** | {{ PATTERN_2_USAGE }} | {{ PATTERN_2_MODULES }} |

---

## 相关文档

| 文档 | 描述 |
|------|------|
| [首页](index.md) | 项目概述 |
| [模块](modules/_index.md) | 模块详情 |
| [API 参考](api/_index.md) | API 文档 |
| [快速开始](getting-started.md) | 安装指南 |

---

*由 [DeepWiki v{{ DEEP_WIKI_VERSION }}](https://github.com/trsoliu/deepwiki) 自动生成 | {{ GENERATED_AT }}*
```

---

## 模块模板

本模板定义了单个模块文档的结构。
它包含 9 个章节。AI 应根据实际源代码分析为每个章节生成内容。

> **代码示例说明**：所有代码示例必须使用项目的主要语言。对于导入语句，请使用该语言的惯用形式（例如 `require`、`from ... import`、`use`、`include` 等）。请勿硬编码 JavaScript/TypeScript 特有的语法。

```markdown
# {{ MODULE_NAME }}

> {{ MODULE_SHORT_DESC }}

---

## 概述

{{ MODULE_INTRODUCTION }}

本模块属于 {{ PARENT_ARCHITECTURE_LAYER }} 层，
提供 {{ PRIMARY_CAPABILITY }} 功能。

\`\`\`mermaid
flowchart TB
    subgraph System["System"]
        A["Upstream: {{ UPSTREAM_MODULE }}"]
        subgraph Current["{{ MODULE_NAME }}"]
            style Current fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
            M["Core logic"]
        end
        C["Downstream: {{ DOWNSTREAM_MODULE }}"]
    end
    A --> M
    M --> C
\`\`\`

---

## 核心类与函数

\`\`\`mermaid
classDiagram
class {{ CLASS_NAME }} {
  +{{ PROP_1 }} : {{ PROP_1_TYPE }}
  +{{ PROP_2 }} : {{ PROP_2_TYPE }}
  -{{ PRIVATE_PROP }} : {{ PRIVATE_TYPE }}
  +{{ METHOD_1 }}({{ PARAM }}: {{ PARAM_TYPE }}) : {{ RETURN_TYPE }}
  +{{ METHOD_2 }}() : void
}
class {{ RELATED_CLASS }} {
  +{{ RELATED_PROP }} : {{ RELATED_TYPE }}
}
{{ CLASS_NAME }} --> {{ RELATED_CLASS }} : depends on
\`\`\`

**图表来源**：
- [{{ CLASS_FILE }}](file:///{{ CLASS_FILE_PATH }}#L{{ START }}-L{{ END }})

---

## 文件结构

\`\`\`
{{ MODULE_PATH }}/
├── {{ ENTRY_FILE }}         # 模块入口，导出公开接口
├── {{ FILE_1 }}             # {{ FILE_1_DESC }}
├── {{ FILE_2 }}             # {{ FILE_2_DESC }}
└── types.{{ EXT }}          # 类型定义
\`\`\`

| 文件 | 职责 | 导出 |
|------|------|------|
| `{{ ENTRY_FILE }}` | 模块入口 | 所有公开接口 |
| `{{ FILE_1 }}` | {{ FILE_1_RESPONSIBILITY }} | {{ FILE_1_EXPORTS }} |
| `{{ FILE_2 }}` | {{ FILE_2_RESPONSIBILITY }} | {{ FILE_2_EXPORTS }} |

---

## 公开接口

### 接口总览

| 接口 | 类型 | 描述 | 来源 |
|------|------|------|------|
| [`{{ FUNC_1 }}`](#{{ FUNC_1 }}) | 函数 | {{ FUNC_1_SHORT_DESC }} | [链接]({{ FUNC_1_SOURCE }}) |
| [`{{ CLASS_1 }}`](#{{ CLASS_1 }}) | 类 | {{ CLASS_1_SHORT_DESC }} | [链接]({{ CLASS_1_SOURCE }}) |
| [`{{ TYPE_1 }}`](#{{ TYPE_1 }}) | 类型 | {{ TYPE_1_SHORT_DESC }} | [链接]({{ TYPE_1_SOURCE }}) |

### `{{ FUNC_1 }}`

> {{ FUNC_1_ONELINER }}

**函数签名**

\`\`\`{{ LANG }}
{{ FUNC_1_SIGNATURE }}
\`\`\`

**参数**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `{{ PARAM_1 }}` | `{{ PARAM_1_TYPE }}` | {{ PARAM_1_REQUIRED }} | {{ PARAM_1_DEFAULT }} | {{ PARAM_1_DESC }} |

**返回值**

| 类型 | 描述 |
|------|-------------|
| `{{ RETURN_TYPE }}` | {{ RETURN_DESC }} |

**示例**

\`\`\`{{ LANG }}
# 导入（使用项目惯用的导入方式）
<IMPORT_MODULE>

# 基本用法
{{ EXAMPLE_BASIC }}

# 带选项用法
{{ EXAMPLE_WITH_OPTIONS }}
\`\`\`

### `{{ TYPE_1 }}`

\`\`\`{{ LANG }}
{{ TYPE_DEFINITION }}
\`\`\`

| 属性 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `{{ PROP_1 }}` | `{{ PROP_1_TYPE }}` | {{ PROP_1_REQUIRED }} | {{ PROP_1_DESC }} |

---

## 代码示例

> **注意**：以下所有代码均使用项目的主要编程语言。请将 `<IMPORT_MODULE>` 替换为该语言惯用的导入语句。

### 示例 1：{{ USE_CASE_1_TITLE }}

**场景**：{{ USE_CASE_1_SCENARIO }}

\`\`\`{{ LANG }}
<IMPORT_MODULE>

{{ USE_CASE_1_CODE }}
\`\`\`

**预期输出**：

\`\`\`
{{ USE_CASE_1_OUTPUT }}
\`\`\`

### 示例 2：{{ USE_CASE_2_TITLE }}

**场景**：{{ USE_CASE_2_SCENARIO }}

\`\`\`{{ LANG }}
<IMPORT_MODULE>

{{ USE_CASE_2_CODE }}
\`\`\`

### 示例 3：错误处理

\`\`\`{{ LANG }}
<IMPORT_MODULE>

{{ EXAMPLE_ERROR_HANDLING }}
\`\`\`

---

## 依赖关系

\`\`\`mermaid
flowchart LR
    subgraph Deps["Dependencies"]
        D1["{{ DEP_1 }}"]
        D2["{{ DEP_2 }}"]
    end
    M["{{ MODULE_NAME }}"]
    subgraph Dependents["Dependents"]
        R1["{{ DEPENDENT_1 }}"]
    end
    D1 --> M
    D2 --> M
    M --> R1
    style M fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
\`\`\`

| 依赖 | 用途 | 耦合度 |
|------|------|--------|
| [`{{ DEP_1 }}`]({{ DEP_1_LINK }}) | {{ DEP_1_PURPOSE }} | {{ DEP_1_COUPLING }} |
| [`{{ DEP_2 }}`]({{ DEP_2_LINK }}) | {{ DEP_2_PURPOSE }} | {{ DEP_2_COUPLING }} |

---

## 错误处理

| 错误 | 触发条件 | 推荐修复方式 |
|------|---------|-------------|
| `{{ ERROR_1 }}` | {{ ERROR_1_CONDITION }} | {{ ERROR_1_SOLUTION }} |
| `{{ ERROR_2 }}` | {{ ERROR_2_CONDITION }} | {{ ERROR_2_SOLUTION }} |

### 调试提示

1. **{{ DEBUG_TIP_1_TITLE }}** -- {{ DEBUG_TIP_1_DESC }}
2. **{{ DEBUG_TIP_2_TITLE }}** -- {{ DEBUG_TIP_2_DESC }}

---

## 相关文档

| 文档 | 描述 |
|------|------|
| [架构](../architecture.md#{{ MODULE_ANCHOR }}) | 架构中的位置 |
| [API 参考](../api/{{ MODULE_NAME }}.md) | 完整 API 文档 |
| [{{ RELATED_MODULE_1 }}]({{ RELATED_MODULE_1 }}.md) | 相关模块 |
| [{{ RELATED_MODULE_2 }}]({{ RELATED_MODULE_2 }}.md) | 相关模块 |

---

[<- 返回模块列表](_index.md) | [API 参考 ->](../api/{{ MODULE_NAME }}.md)

*由 [DeepWiki v{{ DEEP_WIKI_VERSION }}](https://github.com/trsoliu/deepwiki) 自动生成 | {{ GENERATED_AT }}*
```

---

## API 参考模板

```markdown
# API 参考：{{ MODULE_NAME }}

> {{ MODULE_DESCRIPTION }}

---

## 概述

{{ MODULE_PURPOSE_DETAILED }}

### 导入

> 导入语句请使用项目的主要编程语言。

\`\`\`{{ LANG }}
# 导入特定项（使用该语言惯用的导入方式）
<IMPORT_NAMED> from {{ PACKAGE_PATH }}

# 或导入整个模块
<IMPORT_ALL> from {{ PACKAGE_PATH }}
\`\`\`

### 快速示例

\`\`\`{{ LANG }}
{{ QUICK_EXAMPLE }}
\`\`\`

---

## 接口概览

| 接口 | 类型 | 描述 | 来源 |
|------|------|------|------|
{{ API_OVERVIEW_TABLE }}

---

## 类型定义

### `{{ TYPE_NAME }}`

> {{ TYPE_DESCRIPTION }}

\`\`\`{{ LANG }}
{{ TYPE_DEFINITION }}
\`\`\`

| 属性 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
{{ TYPE_PROPERTIES_TABLE }}

**用法**：

\`\`\`{{ LANG }}
{{ TYPE_USAGE_EXAMPLE }}
\`\`\`

---

## 函数

### `{{ FUNCTION_NAME }}` [源码](file:///{{ SOURCE_PATH }}#L{{ LINE }})

> {{ FUNCTION_ONELINER }}

{{ FUNCTION_DETAILED_DESC }}

**函数签名**

\`\`\`{{ LANG }}
{{ FUNCTION_SIGNATURE }}
\`\`\`

**参数**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
{{ PARAMS_TABLE }}

**返回值**

| 类型 | 描述 |
|------|-------------|
| `{{ RETURN_TYPE }}` | {{ RETURN_DETAILED_DESC }} |

**异常**

| 异常 | 触发条件 | 处理方式 |
|------|---------|---------|
{{ EXCEPTIONS_TABLE }}

**示例**

\`\`\`{{ LANG }}
# 基本用法
{{ EXAMPLE_1 }}

# 完整选项用法
{{ EXAMPLE_2 }}

# 错误处理
{{ EXAMPLE_3 }}
\`\`\`

**相关接口**

| 接口 | 关系 |
|------|------|
| [`{{ RELATED_1 }}`](#{{ RELATED_1 }}) | {{ RELATION_1_DESC }} |

---

## 类

### `{{ CLASS_NAME }}` [源码](file:///{{ CLASS_SOURCE_PATH }}#L{{ CLASS_LINE }})

> {{ CLASS_DESCRIPTION }}

**类图**

\`\`\`mermaid
classDiagram
    class {{ CLASS_NAME }} {
        {{ CLASS_PROPERTIES }}
        {{ CLASS_METHODS }}
    }
    {{ CLASS_RELATIONSHIPS }}
\`\`\`

#### 构造函数

\`\`\`{{ LANG }}
{{ CONSTRUCTOR_SIGNATURE }}
\`\`\`

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
{{ CONSTRUCTOR_PARAMS }}

#### 属性

| 属性 | 类型 | 访问权限 | 描述 |
|------|------|---------|------|
{{ CLASS_PROPERTIES_TABLE }}

#### 方法

##### `{{ METHOD_NAME }}()`

{{ METHOD_DESCRIPTION }}

\`\`\`{{ LANG }}
{{ METHOD_SIGNATURE }}
\`\`\`

**返回值**: `{{ METHOD_RETURN_TYPE }}` -- {{ METHOD_RETURN_DESC }}

#### 完整示例

\`\`\`{{ LANG }}
{{ CLASS_COMPLETE_EXAMPLE }}
\`\`\`

---

## 使用模式

### 模式 1：{{ PATTERN_1_TITLE }}

\`\`\`{{ LANG }}
{{ PATTERN_1_CODE }}
\`\`\`

### 模式 2：{{ PATTERN_2_TITLE }}

\`\`\`{{ LANG }}
{{ PATTERN_2_CODE }}
\`\`\`

---

## 常见问题

### 问：{{ FAQ_1_QUESTION }}

**答**：{{ FAQ_1_ANSWER }}

### 问：{{ FAQ_2_QUESTION }}

**答**：{{ FAQ_2_ANSWER }}

---

## 相关文档

| 文档 | 描述 |
|------|------|
| [模块文档](../modules/{{ MODULE_NAME }}.md) | 模块概述 |
| [架构](../architecture.md) | 系统架构 |

---

[<- 返回 API 列表](_index.md) | [模块文档 ->](../modules/{{ MODULE_NAME }}.md)

*由 [DeepWiki v{{ DEEP_WIKI_VERSION }}](https://github.com/trsoliu/deepwiki) 自动生成 | {{ GENERATED_AT }}*
```

---

## 快速开始模板

```markdown
# 快速开始

> 在几分钟内启动并运行 {{ PROJECT_NAME }}。

---

## 前置条件

| 依赖 | 最低版本 | 检查命令 |
|------|---------|---------|
| {{ DEP_1 }} | {{ DEP_1_MIN }} | `{{ DEP_1_CHECK }}` |
| {{ DEP_2 }} | {{ DEP_2_MIN }} | `{{ DEP_2_CHECK }}` |

---

## 安装

### 通过包管理器安装（推荐）

\`\`\`bash
{{ INSTALL_COMMAND }}
\`\`\`

### 从源码安装

\`\`\`bash
git clone {{ REPO_URL }}
cd {{ PROJECT_NAME }}
{{ BUILD_COMMAND }}
\`\`\`

### 验证安装

\`\`\`bash
{{ VERIFY_COMMAND }}
# 预期输出：{{ VERIFY_OUTPUT }}
\`\`\`

---

## 配置

\`\`\`bash
cp {{ CONFIG_TEMPLATE }} {{ CONFIG_FILE }}
\`\`\`

| 配置项 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `{{ CONFIG_1 }}` | `{{ CONFIG_1_TYPE }}` | `{{ CONFIG_1_DEFAULT }}` | {{ CONFIG_1_DESC }} |

| 环境变量 | 描述 | 示例 |
|---------|------|------|
| `{{ ENV_1 }}` | {{ ENV_1_DESC }} | `{{ ENV_1_EXAMPLE }}` |

---

## 运行

### 开发环境

\`\`\`bash
{{ DEV_COMMAND }}
\`\`\`

### 生产环境

\`\`\`bash
{{ PROD_COMMAND }}
\`\`\`

---

## 第一个示例

### 步骤 1：创建入口文件

\`\`\`{{ LANG }}
{{ EXAMPLE_STEP_1 }}
\`\`\`

### 步骤 2：添加逻辑

\`\`\`{{ LANG }}
{{ EXAMPLE_STEP_2 }}
\`\`\`

### 步骤 3：运行

\`\`\`bash
{{ RUN_EXAMPLE_COMMAND }}
\`\`\`

**预期输出**：

\`\`\`
{{ EXAMPLE_OUTPUT }}
\`\`\`

---

## 下一步

| 目标 | 阅读 |
|------|------|
| 了解架构 | [架构文档](architecture.md) |
| 探索模块 | [模块文档](modules/_index.md) |
| 浏览 API 详情 | [API 参考](api/_index.md) |

---

## 常见问题

### 问：{{ SETUP_FAQ_1_Q }}

**答**：{{ SETUP_FAQ_1_A }}

### 问：{{ SETUP_FAQ_2_Q }}

**答**：{{ SETUP_FAQ_2_A }}

---

[<- 返回首页](index.md) | [架构文档 ->](architecture.md)

*由 [DeepWiki v{{ DEEP_WIKI_VERSION }}](https://github.com/trsoliu/deepwiki) 自动生成 | {{ GENERATED_AT }}*
```

---

## 文档地图模板

```markdown
# 文档地图

> {{ PROJECT_NAME }} 完整文档索引与阅读指南

---

## 文档关系图

\`\`\`mermaid
flowchart TB
    subgraph Entry["Entry"]
        Index["Home<br/>index.md"]
        GS["Getting Started<br/>getting-started.md"]
    end
    subgraph Core["Core Docs"]
        Arch["Architecture<br/>architecture.md"]
        Modules["Modules<br/>modules/"]
        API["API<br/>api/"]
    end
    Index --> GS
    Index --> Arch
    GS --> Arch
    Arch --> Modules
    Arch --> API
    Modules -.-> API

    style Index fill:#e3f2fd
    style Arch fill:#fff3e0
    style Modules fill:#e8f5e9
    style API fill:#fce4ec
\`\`\`

---

## 推荐阅读路径

### 新用户

1. [首页](index.md) -- 项目概述
2. [快速开始](getting-started.md) -- 安装配置
3. [架构文档](architecture.md) -- 系统结构
4. 选择一个 [模块](modules/_index.md) 深入了解

### 架构深入

1. [架构文档](architecture.md) -- 系统设计
2. [模块详情](modules/_index.md) -- 各模块文档

### API 查阅

1. [API 索引](api/_index.md) -- 查找目标 API
2. 具体 API 文档 -- 阅读详情
3. [示例](#) -- 实践练习

---

## 完整文档索引

### 入口文档

| 文档 | 描述 |
|------|------|
| [index.md](index.md) | 项目首页 |
| [getting-started.md](getting-started.md) | 快速入门指南 |
| [architecture.md](architecture.md) | 系统架构 |

### 模块文档

| 模块 | 描述 | API 文档 |
|------|------|---------|
{{ MODULES_INDEX_TABLE }}

### API 文档

| API | 模块 | 描述 |
|-----|------|------|
{{ API_INDEX_TABLE }}

---

## 依赖矩阵

| 模块 | 依赖项 | 被依赖项 |
|------|--------|---------|
{{ DEPENDENCY_MATRIX }}

---

[<- 返回首页](index.md)

*由 [DeepWiki v{{ DEEP_WIKI_VERSION }}](https://github.com/trsoliu/deepwiki) 自动生成 | {{ GENERATED_AT }}*
```
