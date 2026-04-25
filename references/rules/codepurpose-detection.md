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
| **Test** | 文件名含 `.test.`、`.spec.`、路径含 `/__tests__/` |
| **Database** | 路径含 `/db/`、`/database/`、`/migrations/`、扩展名 `.sql`、`.prisma` |
| **Other** | 以上均不匹配时的兜底分类 |

> **`file-role-classification.md`** 已合并入本文，仅保留为兼容指针，不再包含规则内容。

---

## Layer 2: 语义推理（仅在 Layer 1 无法确定时使用）

当路径规则无法确定角色时，读取文件内容的前 1,000 字符，根据以下信号推断：

- 含大量 HTTP 路由注册（`app.get`、`router.post`、`@GetMapping`）→ `Api`
- 含数据库查询（`SELECT`、`.query(`、`ORM.find`）→ `Dao`
- 含 UI 渲染逻辑（`render(`、`return <`、`template:`）→ `Widget` 或 `Page`
- 含配置常量（大量 `const CONFIG_`、`env.`）→ `Config`

---

## 语言特定信号

当 Layer 1 路径规则和 Layer 2 通用语义规则均无法确定角色时，使用以下语言特定的代码模式信号表。表中按语言分组，列出信号模式及其对应的推断角色。

| 语言 | 信号模式 | 角色 |
|------|---------|------|
| **Go** | `http.HandleFunc`、`gin.GET`、`echo.GET`、`mux.Handle`、`http.Listen` | `Api` |
| **Go** | `sql.Query`、`sql.Exec`、`database/sql` import、`gorm.Find`、`sqlx.Get` | `Dao` |
| **Go** | `func main()` 且在 `package main` | `Entry` |
| **Go** | `fmt.Fprintf`、`log.Printf` | `Util` |
| **Rust** | `#[tokio::main]`、`fn main()` | `Entry` |
| **Rust** | `impl Trait for`（Trait 为外部接口名） | `Service` |
| **Rust** | `axum::Router`、`warp::Filter`、`actix_web::HttpServer` | `Api` |
| **Rust** | `#[derive(Debug, Clone)]` 等派生宏作用于 struct | `Model` |
| **Rust** | `#[cfg(test)]`、`#[test]` | `Test` |
| **Java** | `@RestController`、`@GetMapping`、`@PostMapping`、`@Controller` | `Api` |
| **Java** | `@Repository`、`extends JpaRepository`、`@Mapper` | `Dao` |
| **Java** | `@Service`、`@Component`（无 `@Controller`） | `Service` |
| **Java** | `@Entity`、`@Table`、`@Column` | `Model` |
| **Java** | `@SpringBootApplication` | `Entry` |
| **Kotlin** | `@RestController`、`@GetMapping`、`@PostMapping` | `Api` |
| **Kotlin** | `@Service`、`@Component`（无 `@Controller`） | `Service` |
| **Kotlin** | `@Entity`、`data class` | `Model` |
| **Kotlin** | `@SpringBootApplication`、`fun main(` | `Entry` |
| **Python** | `@app.route`、`@router.get`、`@router.post`、`@router.` | `Api` |
| **Python** | `@app.get`、`@app.post`（FastAPI）、`@bp.route`（Flask Blueprint） | `Api` |
| **Python** | `@app.middleware`、`@middleware`（FastAPI/Starlette） | `Service` |
| **Python** | 继承 `BaseModel`（Pydantic）、`SQLModel`、`class.*BaseModel`、`class.*Schema` | `Model` |
| **Python** | `@db.session`、`SessionLocal`、`async_session`（SQLAlchemy） | `Dao` |
| **Python** | `if __name__ == "__main__"` | `Entry` |
| **Python** | `@pytest.fixture`、`@pytest.mark`、函数名以 `test_` 开头 | `Test` |
| **TypeScript/JavaScript** | `@RestController`、`@Get`、`@Post`（NestJS）、`app.get(`、`router.get(`（Express/Fastify） | `Api` |
| **TypeScript/JavaScript** | `export default function`、`export default class` 且文件在 `pages/` 或 `app/` | `Page` |
| **TypeScript/JavaScript** | `export function`、`export const` 且文件在 `components/`、`hooks/`、`composables/` | `Widget` |
| **TypeScript/JavaScript** | `createContext`、`useContext`、`provide/inject`（React/Vue） | `Service` |
| **TypeScript/JavaScript** | `useState`、`useReducer`、`createStore`、`defineStore` | `Service` |
| **TypeScript/JavaScript** | `export interface`、`export type`、`z.object`（Zod）、`class.*Schema` | `Model` |
| **TypeScript/JavaScript** | `.env.`、`process.env.`、`import.meta.env`（Vite） | `Config` |
| **TypeScript/JavaScript** | `describe(`、`it(`、`test(`、`expect(`（Jest/Vitest） | `Test` |
| **TypeScript/JavaScript** | `export default` 且文件名为 `main`、`index`、`server` | `Entry` |
| **C#** | `[ApiController]`、`[HttpGet]`、`[HttpPost]`、`ControllerBase` | `Api` |
| **C#** | `[Service]`、`IHostedService`、`BackgroundService` | `Service` |
| **C#** | `[Repository]`、`DbContext`、`DbSet<>` | `Dao` |
| **C#** | `[Entity]`、`[Table]`、`record` 类型 | `Model` |
| **C#** | `IConfiguration`、`IOptions<>`、`appsettings.json` 引用 | `Config` |
| **C#** | `static void Main`、`Program.cs` | `Entry` |
| **C#** | `[Fact]`、`[Theory]`、`[TestMethod]`（xUnit/NUnit/MSTest） | `Test` |

---

## 应用顺序

**Layer 1 路径/文件名规则** → **Layer 2 通用语义推理** → **语言特定信号表**。只有前两步都无法确定时才查语言特定信号表。

---

## 多语言混合项目

项目包含多种编程语言时（如 fullstack-framework 的 TypeScript + Python），按以下规则处理：

1. **语言特定信号按文件扩展名匹配**：每个文件只查其对应语言的信号行（`.ts` 文件查 TypeScript 行，`.py` 文件查 Python 行）
2. **Layer 1 优先**：路径规则（如 `/pages/`、`/api/`）跨语言通用，始终优先于语言特定信号
3. **模块级语言**：模块的主要语言由该模块内文件数最多的语言决定；代码示例使用模块自身语言
4. **前端/后端分离检测**：`/frontend/`、`/client/`、`/web/` 目录下的模块优先使用 TypeScript/JavaScript 信号；`/backend/`、`/server/`、`/api/` 目录下的模块优先使用后端语言信号

---

## 模块级汇总

模块的主 `code_purpose` 由该模块内高重要性文件的角色综合得出：

- 入口文件优先级最高，决定启动链路说明
- `Api`、`Service`、`Agent` 文件决定主要运行路径
- `Model`、`Dao`、`Config` 文件作为支撑结构，不应单独覆盖主职责
- 若模块包含多种角色，使用最能解释读者任务的角色作为主 `code_purpose`

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

## 组件选择引用

本文只维护 CodePurpose 检测信号和条件组件触发信号。

- CodePurpose → 默认组件集：见 [`components-guide.md`](components-guide.md) 的"CodePurpose 组件映射"章节
- Archetype 覆写规则：见 [`components-registry.yaml`](components-registry.yaml) 的 `archetype_overrides`
