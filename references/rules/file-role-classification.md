# 文件角色分类规则

> 本文件定义文件的双层角色分类规则（CodePurpose 检测的文件级应用），是 `extract-docs` 分析阶段的前置分类步骤。
>
> **关联文档**：[`codepurpose-detection.md`](codepurpose-detection.md)（模块级 CodePurpose 检测信号）、[`../workflow/extract-docs.md`](../workflow/extract-docs.md)（分析执行流程）

---

## 第一层：路径/文件名模式快速分类（优先，无需读文件内容）

在读取每个文件之前，先按以下两层规则确定文件的角色标签，角色标签将用于生成文档时的针对性描述。

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
| `Command` | 路径含 `/commands/`、`/cli/`、`/cmd/`、文件名含 `command`、`cli` | `commands/deploy.ts` |
| `Test` | 文件名含 `.test.`、`.spec.`、路径含 `/__tests__/` | `user.test.ts` |
| `Other` | 以上规则均不匹配时的兜底分类 | `misc/helpers.ts` |

---

## 第二层：语义推断（仅在第一层无法确定时使用）

当路径规则无法确定角色时，读取文件内容的前 1,000 字符，根据以下信号推断：

- 含大量 HTTP 路由注册（`app.get`、`router.post`、`@GetMapping`）→ `Api`
- 含数据库查询（`SELECT`、`.query(`、`ORM.find`）→ `Dao`
- 含 UI 渲染逻辑（`render(`、`return <`、`template:`）→ `Widget` 或 `Page`
- 含配置常量（大量 `const CONFIG_`、`env.`）→ `Config`

### 语言特定信号（通用规则无法判断时适用）

| 语言 | 代码信号 | 推断角色 |
|------|---------|---------|
| **Go** | 含 `http.HandleFunc`、`gin.GET`、`echo.GET`、`mux.Handle` | `Api` |
| **Go** | 含 `sql.Query`、`db.Exec`、`gorm.Find`、`sqlx.Get` | `Dao` |
| **Go** | 含 `func main()` 且在 `main` package | `Entry` |
| **Rust** | 含 `#[tokio::main]` 或 `fn main()` | `Entry` |
| **Rust** | 含 `impl Trait`（Trait 为外部接口名） | `Service` |
| **Rust** | 含 `axum::Router`、`actix_web::HttpServer` | `Api` |
| **Java/Kotlin** | 含 `@RestController`、`@Controller` 注解 | `Api` |
| **Java/Kotlin** | 含 `@Repository`、`@Mapper` 注解 | `Dao` |
| **Java/Kotlin** | 含 `@Service`、`@Component`（无 `@Controller`） | `Service` |
| **Java/Kotlin** | 含 `@Entity`、`@Table` 注解 | `Model` |
| **Java/Kotlin** | 含 `@SpringBootApplication`、`fun main(` | `Entry` |
| **Python** | 含 `@app.route`、`@router.get`、`@router.post` | `Api` |
| **Python** | 继承 `BaseModel`（Pydantic）、`SQLModel` | `Model` |
| **Python** | 含 `if __name__ == "__main__"` 且调用核心业务函数 | `Entry` |
| **Python** | 含 `@pytest.fixture` 或函数名以 `test_` 开头 | `Test` |

> **应用顺序**：第一层路径规则 → 第二层通用语义规则 → 本语言特定信号表。只有前两步都无法确定时才查此表。
