# 文件分析指南

本文档定义第 4 步深度阅读源码中使用的文件角色分类规则和分档读取深度策略。

## 文件角色分类（双层分类）

在读取每个文件之前，先按以下两层规则确定文件的角色标签，角色标签将用于生成文档时的针对性描述。

### 第一层：路径/文件名模式快速分类（优先，无需读文件内容）

| 角色标签 | 路径/文件名信号 | 示例 |
|---------|---------------|------|
| `Entry` | 文件名为 main、index、app、mod | `main.py`、`index.ts` |
| `Agent` | 路径或文件名含 `agent` | `src/agent/planner.ts` |
| `Page` | 路径含 `/pages/`、`/views/`、`/screens/` | `pages/home.tsx` |
| `Widget` | 路径含 `/components/`、`/widgets/`、`/ui/` | `components/Button.vue` |
| `Api` | 路径含 `/api/`、`/endpoint/`、`/controller/` | `api/user.ts` |
| `Service` | 路径或文件名含 `service` | `services/auth.ts` |
| `Dao` | 路径含 `/dao/`、`/repository/`、`/persistence/` | `dao/user.repo.ts` |
| `Model` | 路径含 `/models/`、`/entities/`、`/data/` | `models/user.ts` |
| `Config` | 路径含 `/config/`、文件名含 `config`、扩展名为 `.toml/.yaml/.env` | `config/database.yaml` |
| `Database` | 扩展名为 `.sql`、路径含 `/database/`、`/db/`、`/migrations/` | `migrations/001_init.sql` |
| `Util` | 路径含 `/utils/`、`/helpers/`、文件名含 `util`、`helper` | `utils/format.ts` |
| `Test` | 文件名含 `.test.`、`.spec.`、路径含 `/__tests__/` | `user.test.ts` |

### 第二层：语义推断（仅在第一层无法确定时使用）

当路径规则无法确定角色时，读取文件内容的前 1,000 字符，根据以下信号推断：

- 含大量 HTTP 路由注册（`app.get`、`router.post`、`@GetMapping`）→ `Api`
- 含数据库查询（`SELECT`、`.query(`、`ORM.find`）→ `Dao`
- 含 UI 渲染逻辑（`render(`、`return <`、`template:`）→ `Widget` 或 `Page`
- 含配置常量（大量 `const CONFIG_`、`env.`）→ `Config`

---

## 分档读取深度

根据 `complexity_score` 和 `important_lines_count` 决定每个文件的分析深度，避免在低价值文件上浪费 Token：

| complexity_score | important_lines_count | 分析深度 | 操作 |
|-----------------|----------------------|---------|------|
| > 50 | 任意 | **深度分析** | 读取全文，追踪函数调用，提取完整接口表 |
| 20–50 | ≥ 10 | **标准分析** | 读取前 8,000 字节 + 所有重要代码行，提取主要接口 |
| 20–50 | < 10 | **快速浏览** | 读取前 3,000 字节，仅提取导出声明 |
| < 20 | 任意 | **快速浏览** | 读取前 2,000 字节，记录模块职责即可 |

> **重要行优先保留**：当文件需要截断时，优先保留含 `export`、`def`、`fn`、`class`、`import`、`interface`、`@decorator` 的行（即 `important_lines_count` 统计的行类型）。

---

## 读取优先级顺序

按以下优先级读取源文件：

1. **入口文件优先**：先读取 `entry_points` 中的文件，理解项目启动流程。
2. **高优先级文件优先**：从 `high_priority_files` 列表（`importance_score >= 0.6`）按评分降序进行深度分析。
3. **核心文件次之**：从 `core_files` 列表中按 `importance_score` 降序读取，应用分档深度策略。
4. **模块内读取顺序**：对每个模块，先读其 `core_files` 中的文件，再读其他文件。

**技巧**：从模块的入口文件或桶文件（如 `index.ts`、`__init__.py`）开始了解公共接口，然后读取实现文件了解内部逻辑。对于大文件，先关注导出的符号（`important_lines`），再根据需要读取上下文。
