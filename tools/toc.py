#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用目录构建脚本
根据文件夹层级自动生成 Markdown 总目录：
- 自动识别深度，文件夹按层级输出为对应级别的标题
- 最深层级中的 .md 文件输出为链接（无序列表）
- 支持任意深度的目录结构
"""

import os
import re
import urllib.parse

# ========== 配置区域 ==========
ROOT_DIR = "."              # 扫描的根目录
OUTPUT_FILE = "Content.md"  # 输出的目录文件名

# 标题级别对应关系（第N层文件夹使用几级标题）
# 例如：第1层用 ##，第2层用 ###，第3层用 ####
START_HEADING_LEVEL = 1     # 根目录下第一层文件夹从几级标题开始（2 = ##）

# 路径编码：True=URL编码（处理空格等特殊字符），False=不编码
ENCODE_PATH = True

# 忽略的文件夹/文件名称前缀（如 "." 开头的隐藏文件）
IGNORE_PREFIXES = [".", "__", "~"]

# 是否显示空文件夹（作为标题但不含内容）
SHOW_EMPTY_FOLDERS = False
# ==============================


def should_ignore(name: str) -> bool:
    """判断是否应该忽略该文件/文件夹"""
    for prefix in IGNORE_PREFIXES:
        if name.startswith(prefix):
            return True
    return False


def natural_sort_key(s: str):
    """自然排序（按数字大小排序，而非字典序）"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


def get_children_dirs(path: str):
    """获取指定路径下的所有子文件夹（排除忽略项，自然排序）"""
    try:
        dirs = [d for d in os.listdir(path) 
                if os.path.isdir(os.path.join(path, d)) and not should_ignore(d)]
        return sorted(dirs, key=natural_sort_key)
    except PermissionError:
        return []


def get_md_files(path: str):
    """获取指定路径下的所有 .md 文件（排除忽略项，自然排序）"""
    try:
        files = [f for f in os.listdir(path) 
                 if f.endswith(".md") and os.path.isfile(os.path.join(path, f)) 
                 and not should_ignore(f)]
        return sorted(files, key=natural_sort_key)
    except PermissionError:
        return []


def has_visible_content(path: str) -> bool:
    """检查目录下是否有可见的 .md 文件或非空子目录"""
    if get_md_files(path):
        return True
    for subdir in get_children_dirs(path):
        if has_visible_content(os.path.join(path, subdir)):
            return True
    return False


def generate_toc_recursive(path: str, current_depth: int, output_dir: str, 
                           root_path: str = None) -> list:
    """
    递归生成目录
    path: 当前扫描的路径
    current_depth: 当前深度（根目录为0）
    output_dir: 输出文件所在目录（用于计算相对路径）
    root_path: 根目录路径（用于计算相对路径）
    """
    lines = []
    
    if root_path is None:
        root_path = path
    
    # 获取当前目录下的所有子文件夹和 md 文件
    subdirs = get_children_dirs(path)
    md_files = get_md_files(path)
    
    # 如果当前目录是根目录（depth=0），不输出标题，直接递归子目录
    if current_depth > 0:
        # 计算当前文件夹的显示名称
        folder_name = os.path.basename(path)
        
        # 计算标题级别（基于起始级别 + 深度 - 1）
        heading_level = START_HEADING_LEVEL + current_depth - 1
        heading_mark = "#" * heading_level
        
        lines.append(f"{heading_mark} {folder_name}\n")
    
    # 处理 .md 文件（作为链接）
    for md_file in md_files:
        md_name = md_file[:-3]  # 去掉 .md
        md_rel_path = os.path.relpath(
            os.path.join(path, md_file),
            start=output_dir
        )
        md_rel_path = md_rel_path.replace("\\", "/")
        
        if ENCODE_PATH:
            md_rel_path = urllib.parse.quote(md_rel_path, safe="/")
        
        lines.append(f"- [{md_name}]({md_rel_path})")
    
    if md_files:
        lines.append("")  # 文件列表后加空行
    
    # 递归处理子文件夹
    for subdir in subdirs:
        subdir_path = os.path.join(path, subdir)
        
        # 检查子目录是否有可见内容（可选，避免输出空目录）
        if not SHOW_EMPTY_FOLDERS and not has_visible_content(subdir_path):
            continue
        
        sub_lines = generate_toc_recursive(
            subdir_path, current_depth + 1, output_dir, root_path
        )
        lines.extend(sub_lines)
    
    return lines


def main():
    # 确保根目录存在
    root = os.path.abspath(ROOT_DIR)
    if not os.path.exists(root):
        print(f"错误：目录不存在 - {root}")
        return
    
    output_path = os.path.join(root, OUTPUT_FILE)
    output_dir = os.path.dirname(output_path) or "."
    
    print(f"扫描目录: {root}")
    print(f"输出文件: {OUTPUT_FILE}")
    print(f"起始标题级别: {'#' * START_HEADING_LEVEL}")
    print(f"路径编码: {'是' if ENCODE_PATH else '否'}")
    print("-" * 40)
    
    # 生成目录
    toc_lines = generate_toc_recursive(root, 0, output_dir)
    
    # 移除末尾多余空行
    while toc_lines and toc_lines[-1] == "":
        toc_lines.pop()
    
    toc_content = "\n".join(toc_lines)
    
    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(toc_content)
    
    # 统计信息
    line_count = len(toc_lines)
    print(f"✓ 目录已生成: {output_path}")
    print(f"  共 {line_count} 行")


if __name__ == "__main__":
    main()