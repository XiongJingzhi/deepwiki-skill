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
| **Python** | 继承 `BaseModel`（Pydantic）、`SQLModel`、`class.*BaseModel`、`class.*Schema` | `Model` |
| **Python** | `if __name__ == "__main__"` | `Entry` |
| **Python** | `@pytest.fixture`、`@pytest.mark`、函数名以 `test_` 开头 | `Test` |

---

## 应用顺序

**Layer 1 路径/文件名规则** → **Layer 2 通用语义推理** → **语言特定信号表**。只有前两步都无法确定时才查语言特定信号表。

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
| **Command** | overview, architecture-diagram, api-table, code-example, nav-links |
| **Database** | overview, er-diagram, nav-links |
| **Test** | overview, api-table, code-example, nav-links |
| **Other** | overview, api-table, nav-links |
