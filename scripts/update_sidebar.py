#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧农业新闻聚合 - 侧边栏生成脚本

扫描 docs/ 下各分类目录中的 Markdown 文件，读取 frontmatter 元数据，
生成 sidebar.json 供 VitePress 配置导入使用。

用法:
    python update_sidebar.py                  # 使用默认路径
    python update_sidebar.py --docs-dir PATH  # 指定 docs 目录
"""

import json
import os
import sys
import argparse

from utils import CATEGORIES, read_frontmatter, extract_description, setup_logger, filepath_to_route

logger = setup_logger(__name__)


def scan_category(docs_dir: str, category: str) -> list[dict]:
    """
    扫描指定分类目录下所有 .md 文件（排除 index.md），
    读取 frontmatter 并返回文章元数据列表。
    """
    cat_dir = os.path.join(docs_dir, category)
    if not os.path.isdir(cat_dir):
        logger.info("目录不存在，跳过: %s", cat_dir)
        return []

    articles = []
    for fname in os.listdir(cat_dir):
        if not fname.endswith(".md") or fname == "index.md":
            continue

        fpath = os.path.join(cat_dir, fname)
        meta = read_frontmatter(fpath)
        if not meta:
            logger.warning("跳过无效文件: %s", fpath)
            continue

        route = filepath_to_route(fpath, docs_dir)
        description = extract_description(fpath)

        articles.append({
            "text": meta.get("title", fname),
            "link": route,
            "date": meta.get("date", ""),
            "source": meta.get("source", ""),
            "description": description,
        })

    articles.sort(key=lambda a: a.get("date", ""), reverse=True)
    return articles


def build_sidebar(docs_dir: str, max_articles: int = 500) -> list[dict]:
    """
    构建完整的侧边栏结构。
    返回 VitePress 侧边栏格式的列表。
    """
    sidebar = []

    for cat_key, cat_label in CATEGORIES.items():
        articles = scan_category(docs_dir, cat_key)

        group = {
            "text": cat_label,
            "collapsed": False,
            "items": [],
        }

        for article in articles[:max_articles]:
            group["items"].append({
                "text": article["text"],
                "link": article["link"],
                "date": article["date"],
                "source": article["source"],
                "description": article.get("description", ""),
            })

        sidebar.append(group)
        logger.info("分类 [%s]: %d 篇文章", cat_label, len(articles))

    return sidebar


def main():
    """主入口函数：解析参数、扫描文件、生成 sidebar.json。"""
    parser = argparse.ArgumentParser(
        description="智慧农业新闻聚合 - 侧边栏生成脚本"
    )
    parser.add_argument(
        "--docs-dir",
        default=None,
        help="docs 目录路径（默认为脚本上级目录的 docs/）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出 JSON 文件路径（默认为 docs/.vitepress/sidebar.json）",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=50,
        help="每个分类最大文章数（默认 50）",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = args.docs_dir or os.path.normpath(
        os.path.join(script_dir, "..", "docs")
    )

    if not os.path.isdir(docs_dir):
        logger.error("docs 目录不存在: %s", docs_dir)
        sys.exit(1)

    output_path = args.output or os.path.join(
        docs_dir, ".vitepress", "sidebar.json"
    )

    logger.info("扫描目录: %s", docs_dir)
    logger.info("输出文件: %s", output_path)
    logger.info("每个分类最大文章数: %d", args.max_articles)

    sidebar = build_sidebar(docs_dir, args.max_articles)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sidebar, f, ensure_ascii=False, indent=2)

    logger.info("侧边栏配置已生成: %s", output_path)

    total = sum(len(group["items"]) for group in sidebar)
    logger.info("共 %d 个分类，%d 个侧边栏条目", len(sidebar), total)


if __name__ == "__main__":
    main()
