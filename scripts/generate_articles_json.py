#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧农业资讯站 - 文章数据生成脚本

生成 articles.json，包含所有文章的完整元数据，供前端组件使用。

用法:
    python generate_articles_json.py
"""

import json
import os
import re
import sys
import argparse

from utils import CATEGORIES, read_frontmatter, extract_description, setup_logger, filepath_to_route, get_docs_dir

logger = setup_logger(__name__)


def scan_all_articles(docs_dir: str) -> dict:
    """
    扫描所有分类下的文章。
    返回 {category: [articles]} 格式的字典。
    """
    all_articles = {}
    
    for cat_key in CATEGORIES.keys():
        cat_dir = os.path.join(docs_dir, cat_key)
        if not os.path.isdir(cat_dir):
            continue
        
        articles = []
        for fname in os.listdir(cat_dir):
            if not fname.endswith(".md") or fname == "index.md":
                continue
            
            fpath = os.path.join(cat_dir, fname)
            meta = read_frontmatter(fpath)
            if not meta:
                continue
            
            route = filepath_to_route(fpath, docs_dir)
            description = extract_description(fpath)
            
            articles.append({
                "title": meta.get("title", fname),
                "link": route,
                "date": meta.get("date", ""),
                "source": meta.get("source", ""),
                "description": description,
            })
        
        articles.sort(key=lambda a: a.get("date", ""), reverse=True)
        all_articles[cat_key] = articles
    
    return all_articles


def main():
    parser = argparse.ArgumentParser(description="生成文章数据 JSON")
    parser.add_argument("--docs-dir", default=None, help="docs 目录路径")
    parser.add_argument("--output", default=None, help="输出文件路径")
    args = parser.parse_args()
    
    docs_dir = args.docs_dir or get_docs_dir()
    output_path = args.output or os.path.join(docs_dir, ".vitepress", "articles.json")
    
    logger.info("扫描目录: %s", docs_dir)
    logger.info("输出文件: %s", output_path)
    
    all_articles = scan_all_articles(docs_dir)
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    
    total = sum(len(articles) for articles in all_articles.values())
    logger.info("文章数据已生成: %s", output_path)
    logger.info("共 %d 个分类，%d 篇文章", len(all_articles), total)
    
    for cat_key, articles in all_articles.items():
        logger.info("  [%s]: %d 篇", CATEGORIES.get(cat_key, cat_key), len(articles))


if __name__ == "__main__":
    main()
