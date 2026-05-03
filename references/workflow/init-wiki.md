# init-wiki

`python scripts/wiki/init_wiki.py <项目路径> [--force] [--if-not-exists]`

前置：无 | 后置：`analyze-project`

输出：`.deepwiki/config.yaml`、`.deepwiki/meta.json`、`state/`、`cache/`、`wiki/`

## 用法

```bash
# 首次初始化
python scripts/wiki/init_wiki.py <项目目录绝对路径>

# 强制重新初始化（删除已有 .deepwiki/ 并重建）
python scripts/wiki/init_wiki.py <项目目录绝对路径> --force

# CI / 自动化场景（已存在则静默跳过）
python scripts/wiki/init_wiki.py <项目目录绝对路径> --if-not-exists
```

 `.deepwiki/` 已存在时默认停止并提示使用 `--force`。
