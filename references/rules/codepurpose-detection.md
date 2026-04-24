# CodePurpose 检测与条件规则

> 本文件定义 CodePurpose 的检测信号和组件触发条件，作为单一真实来源。

---

## CodePurpose 检测信号

根据文件路径、文件名和内容特征识别模块的 CodePurpose：

| CodePurpose | 检测信号 |
|-------------|----------|
| **Entry** | `main.*`、`index.*`、`app.*` |
| **Agent** | 路径/文件名含 `agent` |
| **Page** | 路径含 `/pages/`、`/views/`、`/screens/` |
| **Widget** | 路径含 `/components/`、`/widgets/`、`/ui/` |
| **Service** | 路径/文件名含 `service` |
| **Api** | 路径含 `/api/`、`/endpoint/`、`/controller/` |
| **Dao** | 路径含 `/dao/`、`/repository/`、`/persistence/` |
| **Model** | 路径含 `/models/`、`/entities/`、`/data/` |
| **Config** | 路径含 `/config/`、扩展名 `.toml/.yaml/.env` |
| **Util** | 路径含 `/utils/`、`/helpers/` |
| **Command** | 路径含 `/commands/`、`/cli/`、`/cmd/` |
| **Database** | 路径含 `/db/`、`/database/`、`/migrations/`、扩展名 `.sql`、`.prisma` |
| **Other** | 以上均不匹配时的兜底分类 |

---

## 条件组件触发规则

根据模块特征添加条件组件：

| 条件 | 添加组件 |
|------|----------|
| 有类定义 | `class-diagram` |
| 复杂度 >= 50 | `code-walkthrough`（如未包含） |
| 依赖数 >= 2 | `dependency-diagram` |
| 有状态管理 | `state-diagram` |
| 有错误定义 | `error-table` |
| 文件数 >= 2 | `file-structure` |
| 公开接口 >= 3 | `usage-patterns` |

---

## CodePurpose → 默认组件集

> 完整映射详见 [`components.md`](components.md) 的"CodePurpose 组件映射"章节。

| CodePurpose | 必需组件 |
|-------------|----------|
| **Entry** | overview, architecture-diagram, sequence-diagram, nav-links |
| **Agent** | overview, sequence-diagram, code-walkthrough, state-diagram, nav-links |
| **Page** | overview, architecture-diagram, api-table, nav-links |
| **Widget** | overview, api-table, code-example, nav-links |
| **Service** | overview, api-table, sequence-diagram, code-walkthrough, nav-links |
| **Api** | overview, api-table, sequence-diagram, code-walkthrough, error-table, nav-links |
| **Dao** | overview, api-table, nav-links |
| **Model** | overview, class-diagram, api-table, nav-links |
| **Config** | overview, api-table, nav-links |
| **Util** | overview, api-table, code-example, nav-links |
