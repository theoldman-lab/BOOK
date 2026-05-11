#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用 Markdown 合并脚本
读取 toc.py 生成的 Content.md 索引文件，将其中引用的 .md 文件合并为单一文件：
- 保留 Content.md 中的标题层级作为大纲结构
- 将每个链接对应的 .md 文件内容插入到对应位置
- 自动处理 URL 编码路径（兼容 toc.py 的 ENCODE_PATH）
"""

import os
import re
import sys
import urllib.parse

# ========== 配置区域 ==========
CONTENT_FILE = "Content.md"       # 输入的索引文件路径
OUTPUT_FILE = "Merged.md"         # 输出的合并文件名

# 是否在文件开头添加目录（仅标题列表，不含文件正文）
INCLUDE_TOC = False

# 是否在每个被合并的文件内容前插入其来源文件名作为提示
SHOW_SOURCE_FILE = False

# 文件内容前的额外标题级别提升（0 = 不做额外提升）
# 例如设为 1 则每个文件的 # 标题变为 ##，以此类推
EXTRA_HEADING_LEVEL = 2
# ==============================


def get_workspace_name():
    """获取当前工作区目录名"""
    return os.path.basename(os.path.abspath("."))


def get_user_input():
    """交互式获取用户配置"""
    print("\n" + "="*60)
    print("Markdown 文件合并工具")
    print("="*60)
    
    # 获取当前工作区名称作为默认输出文件名
    default_output = f"{get_workspace_name()}.md"
    
    # 1. 输入目录路径
    print(f"\n当前工作目录: {os.path.abspath('.')}")
    content_file = input(f"\n请输入 Content.md 文件路径 (直接回车使用默认: {CONTENT_FILE}): ").strip()
    if not content_file:
        content_file = CONTENT_FILE
    
    # 检查文件是否存在
    while not os.path.exists(content_file):
        print(f"错误：文件不存在 - {content_file}")
        content_file = input("请重新输入 Content.md 文件路径: ").strip()
        if not content_file:
            content_file = CONTENT_FILE
    
    # 2. 输出文件名
    output_file = input(f"\n请输入输出文件名 (直接回车使用: {default_output}): ").strip()
    if not output_file:
        output_file = default_output
    
    # 确保输出文件有 .md 扩展名
    if not output_file.endswith('.md'):
        output_file += '.md'
    
    # 3. 配置选项
    print("\n" + "-"*40)
    print("配置选项（直接回车使用默认值）:")
    
    # 是否生成目录
    include_toc_input = input(f"是否在文件开头生成目录？(y/n, 默认: {'y' if INCLUDE_TOC else 'n'}): ").strip().lower()
    if include_toc_input in ['y', 'yes', '是']:
        include_toc = True
    elif include_toc_input in ['n', 'no', '否']:
        include_toc = False
    else:
        include_toc = INCLUDE_TOC
    
    # 是否显示来源文件
    show_source_input = input(f"是否在每个章节前显示来源文件？(y/n, 默认: {'y' if SHOW_SOURCE_FILE else 'n'}): ").strip().lower()
    if show_source_input in ['y', 'yes', '是']:
        show_source = True
    elif show_source_input in ['n', 'no', '否']:
        show_source = False
    else:
        show_source = SHOW_SOURCE_FILE
    
    # 标题提升级别
    extra_level_input = input(f"标题提升级别 (0-6, 默认: {EXTRA_HEADING_LEVEL}): ").strip()
    if extra_level_input:
        try:
            extra_level = int(extra_level_input)
            if extra_level < 0 or extra_level > 6:
                print("警告：级别超出范围(0-6)，使用默认值")
                extra_level = EXTRA_HEADING_LEVEL
        except ValueError:
            print("警告：输入无效，使用默认值")
            extra_level = EXTRA_HEADING_LEVEL
    else:
        extra_level = EXTRA_HEADING_LEVEL
    
    return content_file, output_file, include_toc, show_source, extra_level


def url_decode_path(path: str) -> str:
    """尝试 URL 解码路径，若路径存在则返回解码后的路径"""
    try:
        decoded = urllib.parse.unquote(path)
        return decoded
    except Exception:
        return path


def parse_content_file(filepath: str) -> list:
    """
    解析 Content.md，返回结构化数据
    返回 list of dict:
      - {"type": "heading", "level": int, "text": str}
      - {"type": "link", "name": str, "path": str}  (path 为原始链接文本)
      - {"type": "blank"}
    """
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            # 空行
            if line.strip() == "":
                entries.append({"type": "blank"})
                continue
            # 标题行
            heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if heading_match:
                entries.append({
                    "type": "heading",
                    "level": len(heading_match.group(1)),
                    "text": heading_match.group(2).strip(),
                })
                continue
            # 链接行: - [name](path)
            link_match = re.match(r"^-\s+\[([^\]]+)\]\(([^)]+)\)", line)
            if link_match:
                entries.append({
                    "type": "link",
                    "name": link_match.group(1).strip(),
                    "path": link_match.group(2).strip(),
                })
                continue
            # 其他行：当作普通文本保留
            entries.append({"type": "text", "content": line})
    return entries


def resolve_file_path(link_path: str, content_dir: str) -> str | None:
    """根据链接路径和 Content.md 所在目录，解析出实际文件路径"""
    decoded = url_decode_path(link_path)
    full = os.path.normpath(os.path.join(content_dir, decoded))
    if os.path.isfile(full):
        return full
    # 回退：尝试不解码的原始路径
    raw_full = os.path.normpath(os.path.join(content_dir, link_path))
    if os.path.isfile(raw_full):
        return raw_full
    return None


def read_file_content(filepath: str) -> str:
    """读取 .md 文件内容"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"> *[读取文件失败: {filepath} - {e}]*\n"


def adjust_headings(content: str, extra_levels: int) -> str:
    """
    将内容中所有 # 标题提升 extra_levels 级
    例如 extra_levels=1 时，# -> ##，## -> ###
    """
    if extra_levels <= 0:
        return content

    def _repl(match):
        level = len(match.group(1))
        new_level = level + extra_levels
        if new_level > 6:
            new_level = 6
        return "#" * new_level + match.group(2)

    return re.sub(r"^(#{1,6})(\s.*)", _repl, content, flags=re.MULTILINE)


def generate_merged(content_file: str, output_file: str, include_toc: bool, 
                   show_source: bool, extra_level: int):
    """主逻辑：解析 Content.md 并生成合并文件"""
    content_dir = os.path.dirname(os.path.abspath(content_file))
    entries = parse_content_file(content_file)

    output_lines = []
    toc_lines = []  # 用于生成可选目录
    stats = {"files_merged": 0, "files_missed": 0}

    for entry in entries:
        if entry["type"] == "heading":
            heading_line = f"{'#' * entry['level']} {entry['text']}"
            output_lines.append(heading_line)
            output_lines.append("")
            if include_toc:
                # 生成锚点ID（转换为小写，空格替换为连字符）
                anchor = entry['text'].lower().replace(' ', '-').replace('　', '-')
                # 移除特殊字符
                anchor = re.sub(r'[^\w\-]', '', anchor)
                toc_lines.append(f"{'  ' * (entry['level'] - 1)}- [{entry['text']}](#{anchor})")

        elif entry["type"] == "link":
            name = entry["name"]
            link_path = entry["path"]
            file_path = resolve_file_path(link_path, content_dir)

            # 生成链接项（用于 TOC）
            if include_toc:
                anchor = name.lower().replace(' ', '-').replace('　', '-')
                anchor = re.sub(r'[^\w\-]', '', anchor)
                toc_lines.append(f"{'  ' * 2}- [{name}](#{anchor})")

            # 在正文中插入章节标题
            # output_lines.append(f"## {name}")
            # output_lines.append("")

            if file_path:
                if show_source:
                    rel_path = os.path.relpath(file_path, content_dir)
                    output_lines.append(f"> *来源: {rel_path}*")
                    output_lines.append("")
                content = read_file_content(file_path)
                if extra_level > 0:
                    content = adjust_headings(content, extra_level)
                # 去除文件首尾多余空行
                content = content.strip()
                output_lines.append(content)
                output_lines.append("")
                stats["files_merged"] += 1
            else:
                output_lines.append(f"> *[文件未找到: {link_path}]*")
                output_lines.append("")
                stats["files_missed"] += 1

        elif entry["type"] == "blank":
            # 仅在上一行非空时添加空行，避免连续空行
            if output_lines and output_lines[-1] != "":
                output_lines.append("")

        elif entry["type"] == "text":
            output_lines.append(entry["content"])

    # 移除末尾多余空行
    while output_lines and output_lines[-1] == "":
        output_lines.pop()

    merged_content = "\n".join(output_lines)

    # 如果开启目录，在文件头部插入
    if include_toc and toc_lines:
        toc_header = "# 目录\n\n" + "\n".join(toc_lines) + "\n\n---\n\n"
        merged_content = toc_header + merged_content

    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(merged_content)

    # 打印统计信息
    print("\n" + "="*60)
    print("合并完成！")
    print("="*60)
    print(f"Content 文件: {content_file}")
    print(f"输出文件: {os.path.abspath(output_file)}")
    print(f"已合并: {stats['files_merged']} 个文件")
    if stats["files_missed"] > 0:
        print(f"未找到: {stats['files_missed']} 个文件")
    print(f"文件大小: {os.path.getsize(output_file):,} 字节")
    print("-"*40)


def quick_mode(content_file=None, output_file=None):
    """快速模式：使用命令行参数或默认配置"""
    if content_file is None:
        content_file = CONTENT_FILE
    if output_file is None:
        output_file = f"{get_workspace_name()}.md"
    
    if not os.path.exists(content_file):
        print(f"错误：Content 文件不存在 - {content_file}")
        return False
    
    generate_merged(content_file, output_file, INCLUDE_TOC, SHOW_SOURCE_FILE, EXTRA_HEADING_LEVEL)
    return True


def interactive_mode():
    """交互模式：让用户选择配置"""
    print("\n请选择运行模式:")
    print("1. 快速模式 (使用默认配置)")
    print("2. 交互模式 (自定义配置)")
    print("3. 退出")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    
    if choice == '1':
        print("\n使用快速模式...")
        return quick_mode()
    elif choice == '2':
        print("\n进入交互模式...")
        content_file, output_file, include_toc, show_source, extra_level = get_user_input()
        generate_merged(content_file, output_file, include_toc, show_source, extra_level)
        return True
    elif choice == '3':
        print("退出程序。")
        return False
    else:
        print("无效选项，使用快速模式。")
        return quick_mode()


def main():
    """主函数：支持命令行参数和交互式输入"""
    # 检查是否有命令行参数
    if len(sys.argv) >= 2:
        # 命令行模式
        content_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else f"{get_workspace_name()}.md"
        
        if not os.path.exists(content_file):
            print(f"错误：Content 文件不存在 - {content_file}")
            return
        
        # 支持更多命令行参数
        # 用法: python merge.py content.md output.md [--toc] [--source] [--level N]
        include_toc = '--toc' in sys.argv
        show_source = '--source' in sys.argv
        
        extra_level = EXTRA_HEADING_LEVEL
        for i, arg in enumerate(sys.argv):
            if arg == '--level' and i+1 < len(sys.argv):
                try:
                    extra_level = int(sys.argv[i+1])
                except ValueError:
                    pass
        
        generate_merged(content_file, output_file, include_toc, show_source, extra_level)
    else:
        # 无参数时启动交互模式
        interactive_mode()


if __name__ == "__main__":
    main()