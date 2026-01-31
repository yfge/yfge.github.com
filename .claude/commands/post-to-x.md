将 Markdown 文章发布到 X.com 文章撰写器

用户参数: $ARGUMENTS

## 执行步骤

1. 运行脚本发布文章到 X.com：

```bash
python scripts/post-to-x.py $ARGUMENTS --title
```

2. 等待用户粘贴标题后，运行：

```bash
python scripts/post-to-x.py $ARGUMENTS --body
```

如果用户没有提供文章路径参数，脚本会自动使用 `_posts/` 目录下最新的文章。

## 可用选项

- `--title`: 只复制标题
- `--body`: 只复制正文
- `--md`: 保留 Markdown 格式

## 工作流程

1. 先复制标题 → 用户在 X.com 标题栏粘贴
2. 再复制正文 → 用户在 X.com 正文区粘贴
