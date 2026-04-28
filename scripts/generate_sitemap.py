#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧农业资讯站 - Sitemap 生成脚本

扫描 docs 目录下的所有文章和页面，生成符合 Sitemap 协议的 sitemap.xml 文件，
用于搜索引擎优化（SEO）。

生成的文件：
- docs/sitemap.xml          # 全站 Sitemap

用法:
    python generate_sitemap.py                    # 使用默认配置
    python generate_sitemap.py --site-url URL     # 指定站点 URL
    python generate_sitemap.py --docs-dir PATH    # 指定 docs 目录
    python generate_sitemap.py --output PATH      # 指定输出路径
"""

import os
import sys
import argparse
import datetime
from xml.sax import saxutils

from utils import (
    CATEGORIES,
    read_frontmatter,
    setup_logger,
    get_docs_dir,
)

logger = setup_logger(__name__)

# 默认站点 URL
DEFAULT_SITE_URL = "https://smart-agri-blog.github.io"

# 页面变更频率配置
CHANGEFREQ_CONFIG = {
    "home": "daily",           # 首页
    "category_index": "daily",  # 分类索引页
    "article": "weekly",        # 文章页
    "static": "monthly",        # 静态页面
}

# 页面优先级配置
PRIORITY_CONFIG = {
    "home": "1.0",
    "category_index": "0.8",
    "article": "0.6",
    "static": "0.5",
}


def escape_xml(text: str) -> str:
    """转义 XML 特殊字符。"""
    if not text:
        return ""
    return saxutils.escape(str(text))


def format_lastmod_date(date_str) -> str:
    """
    将日期转换为 W3C Datetime 格式（YYYY-MM-DD）。
    
    Args:
        date_str: 日期字符串或日期对象
    
    Returns:
        W3C Datetime 格式的日期字符串
    """
    try:
        if isinstance(date_str, (datetime.date, datetime.datetime)):
            return date_str.strftime("%Y-%m-%d")
        
        dt = datetime.datetime.strptime(str(date_str), "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return datetime.date.today().strftime("%Y-%m-%d")


def get_file_lastmod(filepath: str) -> str:
    """
    获取文件的最后修改日期。
    
    Args:
        filepath: 文件路径
    
    Returns:
        最后修改日期字符串
    """
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.date.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except OSError:
        return datetime.date.today().strftime("%Y-%m-%d")


def scan_docs_pages(docs_dir: str, site_url: str) -> list[dict]:
    """
    扫描 docs 目录下的所有页面和文章。
    
    Args:
        docs_dir: docs 目录路径
        site_url: 站点 URL
    
    Returns:
        页面信息列表
    """
    pages = []
    
    # 首页
    home_md = os.path.join(docs_dir, "index.md")
    if os.path.isfile(home_md):
        pages.append({
            "loc": f"{site_url}/",
            "lastmod": get_file_lastmod(home_md),
            "changefreq": CHANGEFREQ_CONFIG["home"],
            "priority": PRIORITY_CONFIG["home"],
        })
    
    # 静态页面（非分类目录下的 .md 文件）
    for fname in os.listdir(docs_dir):
        if not fname.endswith(".md") or fname == "index.md":
            continue
        fpath = os.path.join(docs_dir, fname)
        if os.path.isfile(fpath):
            route = "/" + fname.replace(".md", "")
            pages.append({
                "loc": f"{site_url}{route}/",
                "lastmod": get_file_lastmod(fpath),
                "changefreq": CHANGEFREQ_CONFIG["static"],
                "priority": PRIORITY_CONFIG["static"],
            })
    
    # 各分类页面
    for cat_key in CATEGORIES.keys():
        cat_dir = os.path.join(docs_dir, cat_key)
        if not os.path.isdir(cat_dir):
            continue
        
        # 分类索引页
        cat_index = os.path.join(cat_dir, "index.md")
        if os.path.isfile(cat_index):
            pages.append({
                "loc": f"{site_url}/{cat_key}/",
                "lastmod": get_file_lastmod(cat_index),
                "changefreq": CHANGEFREQ_CONFIG["category_index"],
                "priority": PRIORITY_CONFIG["category_index"],
            })
        
        # 文章页
        for fname in os.listdir(cat_dir):
            if not fname.endswith(".md") or fname == "index.md":
                continue
            
            fpath = os.path.join(cat_dir, fname)
            if not os.path.isfile(fpath):
                continue
            
            meta = read_frontmatter(fpath)
            if meta and meta.get("date"):
                lastmod = format_lastmod_date(meta["date"])
            else:
                lastmod = get_file_lastmod(fpath)
            
            route = f"/{cat_key}/{fname.replace('.md', '')}"
            pages.append({
                "loc": f"{site_url}{route}/",
                "lastmod": lastmod,
                "changefreq": CHANGEFREQ_CONFIG["article"],
                "priority": PRIORITY_CONFIG["article"],
            })
    
    # 按最后修改日期降序排列
    pages.sort(key=lambda p: p.get("lastmod", ""), reverse=True)
    
    return pages


def generate_sitemap(pages: list[dict], site_url: str) -> str:
    """
    生成 Sitemap XML 内容。
    
    Args:
        pages: 页面信息列表
        site_url: 站点 URL
    
    Returns:
        Sitemap XML 字符串
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9',
        '                           http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">',
    ]
    
    for page in pages:
        loc = escape_xml(page["loc"])
        lastmod = escape_xml(page.get("lastmod", ""))
        changefreq = escape_xml(page.get("changefreq", "weekly"))
        priority = escape_xml(page.get("priority", "0.5"))
        
        lines.extend([
            "  <url>",
            f"    <loc>{loc}</loc>",
            f"    <lastmod>{lastmod}</lastmod>",
            f"    <changefreq>{changefreq}</changefreq>",
            f"    <priority>{priority}</priority>",
            "  </url>",
        ])
    
    lines.append("</urlset>")
    
    return "\n".join(lines)


def main():
    """主入口函数。"""
    parser = argparse.ArgumentParser(
        description="智慧农业资讯站 - Sitemap 生成脚本"
    )
    parser.add_argument(
        "--site-url",
        default=None,
        help=f"站点 URL（默认：{DEFAULT_SITE_URL}）",
    )
    parser.add_argument(
        "--docs-dir",
        default=None,
        help="docs 目录路径",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出文件路径（默认：docs/sitemap.xml）",
    )
    args = parser.parse_args()
    
    site_url = args.site_url or DEFAULT_SITE_URL
    # 移除末尾的斜杠
    site_url = site_url.rstrip("/")
    
    docs_dir = args.docs_dir or get_docs_dir()
    
    if not os.path.isdir(docs_dir):
        logger.error("docs 目录不存在: %s", docs_dir)
        sys.exit(1)
    
    output_path = args.output or os.path.join(docs_dir, "sitemap.xml")
    
    logger.info("站点 URL: %s", site_url)
    logger.info("扫描目录: %s", docs_dir)
    logger.info("输出文件: %s", output_path)
    
    # 扫描页面
    pages = scan_docs_pages(docs_dir, site_url)
    logger.info("共扫描到 %d 个页面", len(pages))
    
    if not pages:
        logger.warning("未找到任何页面，跳过 sitemap 生成")
        return
    
    # 生成 sitemap
    sitemap_content = generate_sitemap(pages, site_url)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    
    logger.info("Sitemap 已生成: %s", output_path)
    
    # 统计信息
    cat_counts = {}
    for page in pages:
        loc = page["loc"]
        for cat_key in CATEGORIES.keys():
            if f"/{cat_key}/" in loc:
                cat_counts[cat_key] = cat_counts.get(cat_key, 0) + 1
                break
    
    logger.info("页面分布:")
    for cat_key, count in sorted(cat_counts.items()):
        logger.info("  [%s]: %d 页", CATEGORIES.get(cat_key, cat_key), count)


if __name__ == "__main__":
    main()
