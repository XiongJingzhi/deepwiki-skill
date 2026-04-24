# parallel-analysis：并行批次调度策略

> 本文档补充 `extract-docs.md`，定义模块分析阶段的并行执行规则。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | 无（调度策略文档，由 AI 执行） |
| **输入** | `cache/structure.json`（模块列表+重要性评分） |
| **输出** | `cache/module-analysis.json`（增量写入） |
| **前置** | `detect-changes` |
| **后置** | `check-analysis-quality` |

## 何时启用并行

| 模块总数 | 策略 |
|---------|------|
| ≤ 5 | 串行（单 Agent 顺序处理） |
| 6–15 | 并行推荐（每批 3 个模块） |
| > 15 | 并行必须（按重要性排序分批，每批 3 个） |

## 模块独立性说明

extract-docs 语义分析每个模块**天然独立**——分析模块 A 不需要模块 B 已完成分析。
（注：synthesize-deps才需要等extract-docs全部完成）

## 批次控制

- **批次大小**：每批最多 3 个模块
- **排序依据**：`structure.json` 中模块 `importance_score` 降序；高优先级模块在前批
- **批次间隔**：同批所有 subagent 完成后再启动下一批
- **自动继续**：不暂停，不需要用户确认

## subagent 任务模板

```
任务：分析模块 {module_name}（路径：{module_path}）
共享上下文：
  - cache/structure.json（项目结构）
  - cache/code-structure.json（调用图、模式、时序）
待分析文件：{core_files_list}
输出要求：遵循 workflow/extract-docs.md
  - 完成后以增量追加模式写入 cache/module-analysis.json
  - 每个模块必须写入字段见 extract-docs.md 表格
```

## 进度追踪

使用 `cache/progress.json` 的 `phases.analysis` 字段：

```json
{
  "phases": {
    "analysis": {
      "status": "in_progress",
      "mode": "subagent",
      "modules": {
        "core":   {"status": "completed", "agent": "subagent-1"},
        "auth":   {"status": "in_progress", "agent": "subagent-2"},
        "api":    {"status": "pending"}
      }
    }
  }
}
```

状态转换：`pending` → `in_progress` → `completed` / `failed`

## 串行降级

当 subagent 不可用时，自动降级为主 Agent 串行：
- 触发条件：subagent 启动失败，或输出缺少 `public_interfaces` / `key_insights` 字段
- 降级后 `mode` 记录为 `"serial"`，无需用户干预

## 写入安全（并发保障）

多个 subagent 并发写入 `module-analysis.json` 时必须使用增量追加模式：
1. 读取现有 `module-analysis.json`（若不存在则初始化空结构）
2. 更新或新增当前模块的 key
3. 写回文件

**不能**直接覆盖整个文件（会导致竞态条件丢失其他 subagent 的结果）。
