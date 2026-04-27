# init-wiki：初始化

> init-wiki，检查并准备 `.deepwiki/` 目录结构。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/init_wiki.py <项目路径> [--force]` |
| **输入** | 项目目录 |
| **输出** | `.deepwiki/config.yaml`、`.deepwiki/meta.json` |
| **前置** | 无 |
| **后置** | `analyze-project` |

## 检查 `.deepwiki/` 目录

- **不存在**：从**技能目录**运行以下命令创建目录结构（`config.yaml`、`cache/`、`wiki/`）：
  ```bash
  python scripts/init_wiki.py <项目目录绝对路径>
  ```
- **需要重新初始化**：添加 `--force` 参数删除已有 `.deepwiki/` 目录并重新创建干净结构：
  ```bash
  python scripts/init_wiki.py <项目目录绝对路径> --force
  ```
- **已存在**：默认停止并提示使用 `--force`；第一版不做旧 `.deepwiki` 结构兼容或迁移。需要重建时显式运行 `--force`。
