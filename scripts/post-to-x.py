#!/usr/bin/env python3
"""
将 Markdown 博客文章发布到 X.com 文章编辑器

使用方式:
    python scripts/post-to-x.py [文章路径] [选项]

选项:
    --title  只复制标题
    --body   只复制正文（富文本）
"""

import os
import re
import sys
import subprocess
import glob
import tempfile
from pathlib import Path


def get_latest_post(posts_dir: str) -> str:
    """获取最新的博客文章"""
    pattern = os.path.join(posts_dir, "*.md")
    posts = glob.glob(pattern)
    if not posts:
        raise FileNotFoundError(f"在 {posts_dir} 中没有找到文章")
    posts.sort(reverse=True)
    return posts[0]


def parse_front_matter(content: str) -> tuple[dict, str]:
    """解析 YAML front matter 和正文"""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    front_matter = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                value = [t.strip().strip("'\"") for t in value[1:-1].split(",")]
            elif value.startswith("'") or value.startswith('"'):
                value = value.strip("'\"")
            front_matter[key] = value

    body = parts[2].strip()
    return front_matter, body


def markdown_to_html(md: str) -> str:
    """将 Markdown 转换为 HTML（用于富文本复制）

    X.com 编辑器支持：标题、粗体、斜体、列表、引用、链接
    不支持代码块，所以代码块转换为引用块
    """
    html = md

    # 移除正文开头的一级标题（与文章标题重复）
    html = re.sub(r"^#\s+[^\n]+\n+", "", html)

    # 代码块 - 转换为引用块（X.com 不支持代码块）
    def format_code_block(match):
        code = match.group(2).strip()
        # 转义 HTML
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # 每行加上引用
        lines = code.split("\n")
        quoted = "<br>".join(lines)
        return f"<blockquote><code>{quoted}</code></blockquote>"

    html = re.sub(r"```(\w*)\n(.*?)```", format_code_block, html, flags=re.DOTALL)

    # 行内代码
    def format_inline_code(match):
        code = match.group(1)
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<code>{code}</code>"

    html = re.sub(r"`([^`]+)`", format_inline_code, html)

    # 图片 - 转换为占位符
    html = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"<em>[图片: \1]</em>", html)

    # 链接
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)

    # 标题 - 按顺序处理，从大到小
    html = re.sub(r"^#{5}\s+(.+)$", r"<h5>\1</h5>", html, flags=re.MULTILINE)
    html = re.sub(r"^#{4}\s+(.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
    html = re.sub(r"^#{3}\s+(.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^#{2}\s+(.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)

    # 粗体和斜体（先处理粗体，再处理斜体）
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"__(.+?)__", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"_(.+?)_", r"<em>\1</em>", html)

    # 引用块
    def format_blockquote(match):
        lines = match.group(0)
        content = re.sub(r"^>\s*", "", lines, flags=re.MULTILINE)
        return f"<blockquote>{content}</blockquote>"

    html = re.sub(r"(^>\s*.+$\n?)+", format_blockquote, html, flags=re.MULTILINE)

    # 无序列表
    def format_ul(match):
        items = match.group(0)
        list_items = re.findall(r"^[-*+]\s+(.+)$", items, re.MULTILINE)
        if list_items:
            li_tags = "".join(f"<li>{item}</li>" for item in list_items)
            return f"<ul>{li_tags}</ul>"
        return items

    html = re.sub(r"(^[-*+]\s+.+$\n?)+", format_ul, html, flags=re.MULTILINE)

    # 有序列表
    def format_ol(match):
        items = match.group(0)
        list_items = re.findall(r"^\d+[.)]\s+(.+)$", items, re.MULTILINE)
        if list_items:
            li_tags = "".join(f"<li>{item}</li>" for item in list_items)
            return f"<ol>{li_tags}</ol>"
        return items

    html = re.sub(r"(^\d+[.)]\s+.+$\n?)+", format_ol, html, flags=re.MULTILINE)

    # 表格 - 转换为列表格式（X.com 不支持表格）
    def format_table(match):
        table_text = match.group(0)
        lines = [l.strip() for l in table_text.strip().split("\n") if l.strip()]

        # 解析表头
        if not lines:
            return table_text

        header_line = lines[0]
        headers = [h.strip() for h in header_line.strip("|").split("|")]

        # 跳过分隔行 (|---|---|)
        data_start = 1
        if len(lines) > 1 and re.match(r"^\|?[\s\-:|]+\|?$", lines[1]):
            data_start = 2

        # 解析数据行，转换为列表
        result = []
        for line in lines[data_start:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            items = []
            for i, cell in enumerate(cells):
                if cell:
                    if i < len(headers) and headers[i]:
                        items.append(f"<strong>{headers[i]}</strong>: {cell}")
                    else:
                        items.append(cell)
            if items:
                result.append("<li>" + " | ".join(items) + "</li>")

        if result:
            return "<ul>" + "".join(result) + "</ul>"
        return table_text

    # 匹配 Markdown 表格
    html = re.sub(r"(\|[^\n]+\|\n)+", format_table, html)

    # 水平线
    html = re.sub(r"^---+$", r"<hr>", html, flags=re.MULTILINE)
    html = re.sub(r"^\*\*\*+$", r"<hr>", html, flags=re.MULTILINE)

    # 段落处理
    lines = html.split("\n")
    result = []
    paragraph = []

    block_tags = r"^<(h[1-6]|ul|ol|blockquote|hr|pre)"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if paragraph:
                text = " ".join(paragraph)
                if not re.match(block_tags, text):
                    result.append(f"<p>{text}</p>")
                else:
                    result.append(text)
                paragraph = []
        elif re.match(block_tags, stripped):
            if paragraph:
                text = " ".join(paragraph)
                if not re.match(block_tags, text):
                    result.append(f"<p>{text}</p>")
                else:
                    result.append(text)
                paragraph = []
            result.append(stripped)
        else:
            paragraph.append(stripped)

    if paragraph:
        text = " ".join(paragraph)
        if not re.match(block_tags, text):
            result.append(f"<p>{text}</p>")
        else:
            result.append(text)

    html = "\n".join(result)
    html = re.sub(r"\n{3,}", "\n\n", html)

    return html.strip()


def format_tags_as_hashtags(tags) -> str:
    """将 tags 转换为 hashtag 格式"""
    if not tags:
        return ""
    if isinstance(tags, str):
        tags = [tags]
    hashtags = []
    for tag in tags:
        clean_tag = re.sub(r"[^\w\u4e00-\u9fff]", "", str(tag))
        if clean_tag:
            hashtags.append(f"#{clean_tag}")
    return " ".join(hashtags)


def copy_to_clipboard(text: str) -> bool:
    """复制纯文本到剪贴板"""
    try:
        process = subprocess.Popen(
            ["pbcopy"],
            stdin=subprocess.PIPE,
            env={**os.environ, "LANG": "en_US.UTF-8"}
        )
        process.communicate(text.encode("utf-8"))
        return process.returncode == 0
    except Exception as e:
        print(f"复制失败: {e}")
        return False


def copy_html_to_clipboard(html: str, script_dir: Path) -> bool:
    """使用虚拟环境复制 HTML 富文本到剪贴板"""
    project_root = script_dir.parent
    venv_python = project_root / ".venv" / "bin" / "python"
    copy_script = script_dir / "copy_html_clipboard.py"

    if not venv_python.exists():
        print(f"错误: 虚拟环境不存在，请先运行:")
        print(f"  python3 -m venv .venv && .venv/bin/pip install pyobjc-framework-Cocoa")
        return False

    try:
        # 写入临时 HTML 文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            temp_path = f.name

        result = subprocess.run(
            [str(venv_python), str(copy_script), "--file", temp_path],
            capture_output=True,
            text=True
        )

        os.unlink(temp_path)

        if result.returncode != 0:
            print(f"错误: {result.stderr}")
            return False
        return True

    except Exception as e:
        print(f"复制失败: {e}")
        return False


def open_x_article_editor():
    """打开 X.com 文章编辑器"""
    url = "https://x.com/i/articles/new"
    try:
        subprocess.run(["open", url], check=True)
        return True
    except Exception as e:
        print(f"打开浏览器失败: {e}")
        return False


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    posts_dir = project_root / "_posts"

    # 解析参数
    title_only = "--title" in sys.argv
    body_only = "--body" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    # 确定文章路径
    if args:
        post_path = args[0]
        if not os.path.isabs(post_path):
            post_path = project_root / post_path
    else:
        post_path = get_latest_post(str(posts_dir))

    print(f"📄 文章: {post_path}")

    # 读取文章
    with open(post_path, "r", encoding="utf-8") as f:
        content = f.read()

    meta, body = parse_front_matter(content)
    title = meta.get("title", "无标题")
    tags = meta.get("tags", [])

    print(f"📝 标题: {title}")
    print(f"🏷️  标签: {tags}")

    hashtags = format_tags_as_hashtags(tags)

    if title_only:
        print("\n📋 复制标题...")
        if copy_to_clipboard(title):
            print("✅ 标题已复制")
        else:
            return 1

    elif body_only:
        print("\n📋 复制正文（富文本）...")
        html_body = markdown_to_html(body)
        html_content = f"{html_body}\n<p>{hashtags}</p>"

        if copy_html_to_clipboard(html_content, script_dir):
            print("✅ 正文已复制（富文本格式）")
        else:
            print("⚠️  富文本复制失败，使用纯文本...")
            # 回退到纯文本
            plain = re.sub(r'<[^>]+>', '', html_content)
            copy_to_clipboard(plain)
            print("✅ 正文已复制（纯文本）")

    else:
        # 完整流程
        print("\n" + "="*50)
        print("📋 发布到 X.com")
        print("="*50)

        # 步骤1: 复制标题
        print("\n【1】复制标题...")
        copy_to_clipboard(title)
        print(f"   ✅ 已复制: {title[:50]}...")

        # 打开编辑器
        print("\n【2】打开 X.com 编辑器...")
        open_x_article_editor()

        input("\n   👉 在标题栏粘贴后按 Enter 继续...")

        # 步骤2: 复制正文
        print("\n【3】复制正文（富文本）...")
        html_body = markdown_to_html(body)
        html_content = f"{html_body}\n<p>{hashtags}</p>"

        if copy_html_to_clipboard(html_content, script_dir):
            print("   ✅ 正文已复制（富文本格式）")
        else:
            print("   ⚠️  富文本失败，使用纯文本...")
            plain = re.sub(r'<[^>]+>', '', html_content)
            copy_to_clipboard(plain)

        print("\n   👉 在正文区域粘贴 (Cmd+V)")
        print("\n📌 代码块已转为引用格式（X.com 不支持代码块）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
