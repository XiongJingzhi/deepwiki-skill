# 批次调度策略

> 本文档定义 DeepWiki 管线中两个并行阶段的统一调度规则：`extract-docs`（模块分析）和 `generate-module-docs`（文档生成）。两个阶段共享相同的调度框架。

## 何时启用并行

只有任务单元之间相互独立、写入目标互不覆盖时才启用并行。适合并行的任务包括：

- `extract-docs`：按模块分析。
- `generate-module-docs`：按页面计划项或模块页面生成。
- 质量修复：按 Basic 文档或失败模块定向重生成。

不适合并行的步骤包括初始化、全局结构提取、架构骨架生成、分析校验、文档拓扑规划、菜单生成和 finalize 聚合检查；这些步骤需要全局一致输入或写同一个聚合文件，应串行执行。

| 模块总数 | 策略 |
|---------|------|
| ≤ 5 | 串行（单 Agent 顺序处理） |
| 6–15 | 并行推荐（每批 3 个模块） |
| > 15 | 并行必须（按重要性/优先级排序分批，每批 3 个） |

## 批次控制

- **批次大小**：每批最多 3 个模块
- **排序依据**：模块 `importance_score`（extract-docs）或 CodePurpose 优先级（generate-module-docs）降序
- **批次间隔**：同批所有任务完成后再启动下一批
- **自动继续**：不暂停，不需要用户确认

## 进度追踪

使用 `cache/progress.json` 追踪每个模块的处理状态：

```json
{
  "phases": {
    "<phase>": {
      "status": "in_progress",
      "mode": "subagent",
      "modules": {
        "core": {"status": "completed", "agent": "subagent-1"},
        "auth": {"status": "in_progress", "agent": "subagent-2"},
        "api":  {"status": "pending"}
      }
    }
  }
}
```

状态转换：`pending` → `in_progress` → `completed` / `failed`

## 串行降级

当 subagent 不可用时，自动降级为主 Agent 串行：
- **触发条件**：subagent 启动失败，或输出质量不达标
- **降级后** `mode` 记录为 `"serial"`，无需用户干预

## 写入安全（并发保障）

多个 subagent 并发写入同一文件时必须使用**增量追加模式**：
1. 读取现有文件
2. 更新或新增当前模块的 key
3. 写回文件

**不能**直接覆盖整个文件（会导致竞态条件丢失其他 subagent 的结果）。
