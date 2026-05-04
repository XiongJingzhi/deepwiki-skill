# generate-skeleton

`python -m scripts.pipeline.generate_skeleton <项目路径>`

前置：`extract-structure` | 后置：`extract-docs`

两步流程：脚本生成确定性字段 → AI 补充语义字段完成骨架。

## 脚本输出

**`cache/architecture-skeleton.json`**（直接写出，含 `_input_summary` 字段供 AI 读取）

```jsonc
{
  "module_groups": [{ "name", "modules", "dominant_purpose" }],
  "architecture_layers": [{ "layer", "modules" }],
  "cross_domain_dependencies": [{ "from", "to", "direction" }],
  "project_nature": "",    // 留给 AI 填写
  "key_data_flows": [],    // 留给 AI 填写
  "_input_summary": {      // 精简模块摘要，供 AI 读骨架时使用，无需加载全量 code-structure.json
    "archetype": "...",
    "project_name": "...",
    "tech_stack": {},
    "modules": [{ "name", "purpose", "importance", "imports" }]
  }
}
```

## AI 补充完成

读取 `cache/architecture-skeleton.json`，利用 `_input_summary` 中的模块摘要作为上下文，补充：
- `project_nature`：一句话描述项目性质和技术栈
- `key_data_flows`：最多 3 条关键数据流描述
- 可选：覆盖 `module_groups` 的 `name`/`role`/`reason` 字段为面向读者的语义描述

补充完成后原地覆写保存同一文件（`_input_summary` 字段可保留或删除）。
