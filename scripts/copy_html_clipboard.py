#!/usr/bin/env python3
"""
将 HTML 内容复制到 macOS 剪贴板（作为富文本）
粘贴时会保留格式（粗体、标题、列表等）

使用方式:
    python copy_html_clipboard.py --html "<h1>标题</h1><p>正文</p>"
    python copy_html_clipboard.py --file content.html
"""

import sys
import argparse


def copy_html_to_clipboard_macos(html_content: str) -> bool:
    """使用 AppKit 将 HTML 复制到 macOS 剪贴板"""
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeHTML, NSPasteboardTypeString

        # 获取系统剪贴板
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()

        # 设置 HTML 内容
        html_data = html_content.encode('utf-8')
        pasteboard.setData_forType_(html_data, NSPasteboardTypeHTML)

        # 同时设置纯文本版本（作为后备）
        # 简单去除 HTML 标签
        import re
        plain_text = re.sub(r'<[^>]+>', '', html_content)
        plain_text = plain_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        pasteboard.setString_forType_(plain_text, NSPasteboardTypeString)

        return True
    except ImportError:
        print("错误: 需要安装 pyobjc-framework-Cocoa")
        print("运行: pip install pyobjc-framework-Cocoa")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='复制 HTML 到剪贴板')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--html', type=str, help='HTML 内容字符串')
    group.add_argument('--file', type=str, help='HTML 文件路径')

    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        html_content = args.html

    if copy_html_to_clipboard_macos(html_content):
        print("✅ HTML 已复制到剪贴板")
        return 0
    else:
        print("❌ 复制失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
