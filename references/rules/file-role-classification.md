# 文件角色分类规则

> 本文件定义文件级双层角色分类规则，是 `extract-docs` 分析阶段的前置分类步骤。
>
> **关联文档**：[`codepurpose-detection.md`](codepurpose-detection.md)（CodePurpose 检测与组件触发）、[`../workflow/extract-docs.md`](../workflow/extract-docs.md)（分析执行流程）

---

## 目标

在读取源码前，先给每个文件标注一个面向文档生成的角色标签。角色标签用于决定：

- 文件读取深度
- 模块主 CodePurpose
- 需要生成的文档组件
- 是否需要代码示例、图表、API 表或错误表

## 第一层：路径与文件名规则

优先使用路径、目录名、文件名和扩展名判断。命中第一层时通常不需要继续推断。

| CodePurpose | 路径/文件名信号 |
|-------------|----------------|
| `Entry` | `main.*`、`index.*`、`app.*`、`server.*`、`cmd/*`、`bin/*` |
| `Agent` | 路径或文件名包含 `agent`、`planner`、`executor`、`tool`、`memory` |
| `Page` | 路径包含 `/pages/`、`/views/`、`/screens/`、`/routes/` |
| `Widget` | 路径包含 `/components/`、`/widgets/`、`/ui/`、`/hooks/` |
| `Service` | 路径或文件名包含 `service`、`manager`、`processor`、`handler` |
| `Api` | 路径包含 `/api/`、`/endpoint/`、`/controller/`、`/routes/` |
| `Dao` | 路径包含 `/dao/`、`/repository/`、`/persistence/`、`/store/` |
| `Model` | 路径包含 `/models/`、`/entities/`、`/schema/`、`/types/`、`/data/` |
| `Config` | 路径包含 `/config/`，或扩展名为 `.toml`、`.yaml`、`.yml`、`.env` |
| `Util` | 路径包含 `/utils/`、`/helpers/`、`/lib/`、`/shared/` |
| `Command` | 路径包含 `/commands/`、`/cli/`、`/cmd/` |
| `Test` | 文件名包含 `.test.`、`.spec.`，或路径包含 `/tests/`、`/__tests__/` |
| `Database` | 路径包含 `/db/`、`/database/`、`/migrations/`，或扩展名为 `.sql`、`.prisma` |
| `Other` | 以上均不匹配时的兜底分类 |

## 第二层：语义推断

当路径规则无法确定角色时，读取文件内容的关键片段，根据代码信号推断。

通用语义规则：

- 含大量 HTTP 路由注册，如 `app.get`、`router.post`、`@GetMapping` → `Api`
- 含数据库查询或 ORM 操作，如 `SELECT`、`.query(`、`Repository`、`ORM.find` → `Dao`
- 含 UI 渲染逻辑，如 `render(`、`return <`、`template:` → `Widget` 或 `Page`
- 含配置常量或环境变量读取，如 `CONFIG_`、`process.env`、`env.` → `Config`

### 语言特定信号

当前两层通用规则仍无法确定时，按文件语言使用以下信号。

| 语言 | 代码信号 | 推断角色 |
|------|---------|---------|
| **Go** | 含 `http.HandleFunc`、`gin.GET`、`echo.GET`、`mux.Handle` | `Api` |
| **Go** | 含 `sql.Query`、`db.Exec`、`gorm.Find`、`sqlx.Get` | `Dao` |
| **Go** | 含 `func main()` 且在 `package main` | `Entry` |
| **Rust** | 含 `#[tokio::main]` 或 `fn main()` | `Entry` |
| **Rust** | 含 `impl Trait`，且 Trait 表示外部接口或业务能力 | `Service` |
| **Rust** | 含 `axum::Router`、`actix_web::HttpServer`、`warp::Filter` | `Api` |
| **Java/Kotlin** | 含 `@RestController`、`@Controller`、`@GetMapping`、`@PostMapping` | `Api` |
| **Java/Kotlin** | 含 `@Repository`、`@Mapper`、`JpaRepository` | `Dao` |
| **Java/Kotlin** | 含 `@Service`、`@Component`，且无 Controller 注解 | `Service` |
| **Java/Kotlin** | 含 `@Entity`、`@Table`、`data class` | `Model` |
| **Java/Kotlin** | 含 `@SpringBootApplication`、`fun main(` | `Entry` |
| **Python** | 含 `@app.route`、`@router.get`、`@router.post`、`@app.get` | `Api` |
| **Python** | 继承 `BaseModel`、`SQLModel`，或类名包含 `Schema` | `Model` |
| **Python** | 含 `SessionLocal`、`async_session`、`db.session` | `Dao` |
| **Python** | 含 `if __name__ == "__main__"` 且调用核心业务函数 | `Entry` |
| **Python** | 含 `@pytest.fixture` 或函数名以 `test_` 开头 | `Test` |
| **TypeScript/JavaScript** | 含 `app.get(`、`router.get(`、`@Get`、`@Post` | `Api` |
| **TypeScript/JavaScript** | 含 JSX/TSX 渲染、React/Vue/Svelte 组件导出 | `Widget` 或 `Page` |
| **TypeScript/JavaScript** | 含 `createContext`、`defineStore`、`useReducer` | `Service` |
| **TypeScript/JavaScript** | 含 `export interface`、`export type`、`z.object` | `Model` |

> **应用顺序**：第一层路径规则 → 第二层通用语义规则 → 语言特定信号。只有前两步都无法确定时才查语言特定信号表。

## 模块级汇总

模块的主 `code_purpose` 由该模块内高重要性文件的角色综合得出：

- 入口文件优先级最高，决定启动链路说明
- `Api`、`Service`、`Agent` 文件决定主要运行路径
- `Model`、`Dao`、`Config` 文件作为支撑结构，不应单独覆盖主职责
- 若模块包含多种角色，使用最能解释读者任务的角色作为主 `code_purpose`

完整组件触发和 CodePurpose 映射见 [`codepurpose-detection.md`](codepurpose-detection.md)。
