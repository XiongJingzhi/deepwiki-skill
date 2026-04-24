# Menu Archetypes 分组思路库

> 本文档为步骤 7 生成 `menu.json` 时的**第三层兜底参考**，用于处理无强依赖关系、`semantic_group` 置信度低、或孤岛模块的归属决策。
>
> **优先级规则：依赖数据（层1）> semantic_group（层2）> 本文档（层3）**
>
> 每种原型提供：常见语义主题（分组灵感）、粒度建议、常见反模式。

---

## 通用规则（所有原型适用）

- 菜单语义名称面向**读者理解**，不使用文件路径或技术术语
- 顶层区块建议 3-6 个；超过 6 个信号需要合并相邻主题
- 首区块固定为项目概览（"Overview" / "入门"），尾区块为贡献/扩展指引
- 单个模块的"孤岛组"除非重要性极高，否则归入最近邻主题
- 避免以 CodePurpose 枚举（Service / Util / Model）直接命名菜单分区

---

## web-service（后端服务类）

**常见语义主题：**
- 请求处理与路由（Routing / Handlers）
- 认证与鉴权（Auth & Authorization）
- 核心业务逻辑（Domain / Business Logic）
- 数据访问层（Data Access / Repository）
- 外部集成（External Integrations / Clients）
- 配置与启动（Configuration & Bootstrap）

**粒度建议：** 顶层 4-6 区块；业务逻辑复杂时拆出子分区（如"订单流程"/"支付流程"）

**反模式：**
- ❌ 把所有 Model 归一组、所有 Service 归一组——这是按技术层归类，不是按业务语义
- ❌ 路由文件和 Handler 分到两组（它们通常高度耦合，应合并）

---

## sdk-library（SDK / 开发库类）

**常见语义主题：**
- 快速开始（Getting Started）
- 核心 API（Core API）
- 高级用法（Advanced Usage）
- 插件与扩展（Plugins & Extensions）
- 类型与接口定义（Types & Interfaces）
- 工具函数（Utilities）

**粒度建议：** 以 API surface 为主轴，读者是开发者——优先暴露"他们最常用的"而非"内部实现"

**反模式：**
- ❌ 把所有 internal 模块平铺在菜单里——内部实现细节不应占据顶层导航
- ❌ 把 utils 拆为多个小组——通用工具通常合并为一个区块

---

## spa-frontend（单页前端应用类）

**常见语义主题：**
- 页面与路由（Pages & Routing）
- UI 组件（UI Components）
- 状态管理（State Management）
- 数据请求与 API 集成（Data Fetching）
- 主题与样式（Theme & Styling）
- 工具与钩子（Utilities & Hooks）

**粒度建议：** 以用户功能区域为分组首选（如"用户中心"/"工作台"），组件库单独成区

**反模式：**
- ❌ 按目录层级（`components/` / `pages/` / `hooks/`）直接翻译为菜单——菜单应按功能语义而非目录结构
- ❌ 把每个 Page 都独立成一个顶层区块——Page 数量多时应按功能域聚合

---

## cli-tool（命令行工具类）

**常见语义主题：**
- 命令参考（Commands Reference）
- 配置（Configuration）
- 插件与扩展（Plugins & Extensions）
- 集成与工作流（Integrations）
- 核心引擎（Core Engine / Internals）

**粒度建议：** 以"用户目标"为导向——用户使用 CLI 想完成什么任务，按任务归组

**反模式：**
- ❌ 把每个子命令都展开为独立区块——相似命令应归入同一"命令类别"区块
- ❌ 将 `main.ts` / `cli.ts` 单独成组——入口文件通常归入"核心引擎"

---

## agent-project（AI Agent / 智能体项目类）

**常见语义主题：**
- Agent 核心与调度（Agent Core & Orchestration）
- 工具与技能集（Tools & Skills）
- 记忆与上下文管理（Memory & Context）
- 规划与推理（Planning & Reasoning）
- LLM 接入与适配（LLM Integration）
- 流程与工作流定义（Workflows & Pipelines）
- 知识库与检索（Knowledge & Retrieval）
- 评估与可观测性（Evaluation & Observability）

**粒度建议：** 以 Agent 能力维度分组（"能做什么"而非"怎么实现"）；工具/技能数量多时按功能域聚合（如"文件操作工具"/"网络工具"）；LLM 接入层单独成区（支持多 provider 时尤其重要）

**反模式：**
- ❌ 把每个工具/技能都单独列为顶层区块——工具应按功能域聚合后再展开
- ❌ 把 LLM 调用代码分散归入"工具"——LLM 接入是独立的基础设施层，应单独成区
- ❌ 把 Prompt 模板文件归入"配置"——Prompt 通常是推理逻辑的一部分，归入"规划与推理"或对应工具区
- ❌ 把 Memory 和 RAG/检索混为一组——短期上下文管理（Memory）与长期知识检索（Retrieval）职责不同，应分区

---

## ml-project（机器学习 / AI 项目类）

**常见语义主题：**
- 数据处理与预处理（Data & Preprocessing）
- 模型定义与架构（Model Architecture）
- 训练流程（Training Pipeline）
- 推理与部署（Inference & Serving）
- 评估与指标（Evaluation & Metrics）
- 实验配置（Experiment Config）

**粒度建议：** 按 ML 生命周期阶段分组；配置和实验管理单独成区

**反模式：**
- ❌ 把所有 Python 脚本平铺——需按 ML 阶段聚合
- ❌ 把数据加载和特征工程拆成两个顶层区块——通常归入同一"数据处理"区

---

## fullstack-framework（全栈框架类）

**常见语义主题：**
- 框架核心（Core Framework）
- 路由与请求处理（Routing）
- 模板与渲染（Templating / Rendering）
- 数据层（Data Layer / ORM）
- 中间件与插件（Middleware & Plugins）
- CLI 与工具链（CLI & Tooling）
- 扩展与生态（Extensions & Ecosystem）

**粒度建议：** 以框架的"核心概念"为分组；工具链和扩展在核心稳定后单独列出

**反模式：**
- ❌ 按前后端目录（`frontend/` / `backend/`）机械划分——全栈框架通常有跨层的核心概念

---

## generic（通用 / 未分类项目）

**策略：** 无法匹配以上原型时，回退到纯数据驱动分组，不参考任何预设主题。

**兜底原则：**
1. 依赖关系最强的模块聚合为核心区块
2. 被最多模块依赖（高 imported_by 数）的模块排在前面
3. 配置 / 工具类模块归入"Infrastructure"区块
4. 无依赖关系的孤岛模块，按 `code_purpose` 粗归类后末尾列出

**反模式：**
- ❌ 强行套用其他原型的语义主题（如给脚本集合套 web-service 的"认证与鉴权"）
