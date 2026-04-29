#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧农业资讯站 - RSS Feed 生成脚本

扫描 docs 目录下的文章，生成符合标准的 RSS 2.0 和 Atom feed 文件。

生成的文件：
- feed.xml          # RSS 2.0 全站订阅源
- feed-atom.xml     # Atom 格式订阅源
- policies/feed.xml # 政策法规分类订阅源
- news/feed.xml     # 行业资讯分类订阅源
- cases/feed.xml   # 地方案例分类订阅源
- standards/feed.xml # 技术标准分类订阅源

用法:
    python generate_feed.py              # 生成所有 feed
    python generate_feed.py --category news  # 仅生成行业资讯 feed
    python generate_feed.py --limit 20  # 限制每类最多 20 篇
"""

import os
import json
import sys
import argparse
import datetime
from xml.sax import saxutils

from utils import (
    CATEGORIES,
    read_frontmatter,
    extract_description,
    format_rfc2822_date,
    format_iso8601_date,
    clean_markdown_content,
    setup_logger,
)

# ============================================================
# 日志配置
# ============================================================

logger = setup_logger(__name__)

# Feed 配置
FEED_CONFIG = {
    "title": "智慧农业资讯站",
    "description": "汇聚智慧农业政策法规、行业资讯、地方案例与技术标准，助力农业现代化发展",
    "link": "https://smart-agri-blog.github.io/smart-agri-blog",
    "language": "zh-CN",
    "author": "智慧农业资讯站",
    "generator": "Smart Agri Blog Feed Generator",
}


# ============================================================
# 工具函数
# ============================================================


def escape_xml(text: str) -> str:
    """转义 XML 特殊字符。"""
    if not text:
        return ""
    return saxutils.escape(str(text))


def read_article_content(filepath: str) -> str:
    """读取文章内容（去除 frontmatter）。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return ""

    return clean_markdown_content(content)


def scan_articles(docs_dir: str, category: str = None, limit: int = 50) -> list[dict]:
    """
    扫描 docs 目录下的文章。
    返回按日期降序排列的文章列表。
    """
    articles = []

    categories_to_scan = [category] if category else CATEGORIES.keys()

    for cat in categories_to_scan:
        cat_dir = os.path.join(docs_dir, cat)
        if not os.path.isdir(cat_dir):
            continue

        for fname in os.listdir(cat_dir):
            if not fname.endswith(".md") or fname == "index.md":
                continue

            fpath = os.path.join(cat_dir, fname)
            meta = read_frontmatter(fpath)
            if not meta:
                continue

            articles.append({
                "title": meta.get("title", "无标题"),
                "date": meta.get("date", ""),
                "link": meta.get("link", ""),
                "source": meta.get("source", ""),
                "category": cat,
                "category_label": CATEGORIES.get(cat, cat),
                "filepath": fpath,
                "meta": meta,
            })

    # 按日期降序排列
    articles.sort(key=lambda a: a.get("date", ""), reverse=True)

    # 限制数量
    return articles[:limit]


# ============================================================
# RSS 2.0 生成
# ============================================================


def generate_rss2(articles: list[dict], config: dict, 
                  feed_title: str = None, feed_description: str = None,
                  feed_link: str = None, category: str = None) -> str:
    """生成 RSS 2.0 格式的 feed。"""
    title = escape_xml(feed_title or config["title"])
    description = escape_xml(feed_description or config["description"])
    link = feed_link or config["link"]

    if category:
        title = f"{title} - {CATEGORIES.get(category, category)}"
        link = f"{link}/{category}/"

    build_date = format_rfc2822_date(datetime.date.today().strftime("%Y-%m-%d"))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        f"    <title>{title}</title>",
        f"    <description>{description}</description>",
        f"    <link>{link}</link>",
        f"    <language>{config['language']}</language>",
        f"    <webMaster>{config['author']} ({config['title']})</webMaster>",
        f"    <generator>{config['generator']}</generator>",
        f"    <lastBuildDate>{build_date}</lastBuildDate>",
    ]

    # 添加 Atom 自链接
    atom_link = f"{link}feed.xml" if not category else f"{link}{category}/feed.xml"
    lines.append(f'    <atom:link href="{atom_link}" rel="self" type="application/rss+xml"/>')

    for article in articles:
        article_title = escape_xml(article["title"])
        article_link = escape_xml(article["link"])
        article_date = format_rfc2822_date(article["date"])
        article_source = escape_xml(article.get("source", ""))
        article_desc = escape_xml(extract_description(article["filepath"], 300, article["meta"]))

        lines.extend([
            "    <item>",
            f"      <title>{article_title}</title>",
            f"      <link>{article_link}</link>",
            f"      <guid isPermaLink=\"false\">{article_link}</guid>",
            f"      <pubDate>{article_date}</pubDate>",
            f"      <author>{article_source}</author>",
            f"      <description>{article_desc}</description>",
            f"      <category>{article.get('category_label', '')}</category>",
            "    </item>",
        ])

    lines.extend([
        "  </channel>",
        "</rss>",
    ])

    return "\n".join(lines)


# ============================================================
# Atom 生成
# ============================================================


def generate_atom(articles: list[dict], config: dict,
                  feed_title: str = None, feed_link: str = None,
                  category: str = None) -> str:
    """生成 Atom 格式的 feed。"""
    title = escape_xml(feed_title or config["title"])
    link = feed_link or config["link"]
    updated = format_iso8601_date(datetime.date.today().strftime("%Y-%m-%d"))

    if category:
        title = f"{title} - {CATEGORIES.get(category, category)}"
        link = f"{link}/{category}/"

    feed_id = f"{link}feed-atom.xml" if not category else f"{link}{category}/feed-atom.xml"

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{title}</title>",
        f"  <subtitle>{escape_xml(config['description'])}</subtitle>",
        f"  <id>{escape_xml(feed_id)}</id>",
        f"  <updated>{updated}</updated>",
        f"  <author><name>{config['author']}</name></author>",
        f"  <link href=\"{link}\" rel=\"alternate\" type=\"text/html\"/>",
        f"  <link href=\"{link}feed-atom.xml\" rel=\"self\" type=\"application/atom+xml\"/>",
    ]

    for article in articles:
        article_id = escape_xml(article["link"])
        article_title = escape_xml(article["title"])
        article_updated = format_iso8601_date(article["date"])
        article_author = escape_xml(article.get("source", ""))
        article_summary = escape_xml(extract_description(article["filepath"], 300, article["meta"]))

        lines.extend([
            "  <entry>",
            f"    <title>{article_title}</title>",
            f"    <id>{article_id}</id>",
            f"    <updated>{article_updated}</updated>",
            f"    <author><name>{article_author}</name></author>",
            f"    <link href=\"{article_id}\" rel=\"alternate\"/>",
            f"    <summary>{article_summary}</summary>",
            f"    <category term=\"{article.get('category_label', '')}\"/>",
            "  </entry>",
        ])

    lines.append("</feed>")
    return "\n".join(lines)


# ============================================================
# JSON Feed 生成（可选）
# ============================================================


def generate_json_feed(articles: list[dict], config: dict,
                       category: str = None) -> str:
    """生成 JSON Feed 格式。"""
    title = config["title"]
    link = config["link"]

    if category:
        title = f"{title} - {CATEGORIES.get(category, category)}"
        link = f"{link}/{category}/"

    items = []
    for article in articles:
        date_val = article["date"]
        if isinstance(date_val, (datetime.date, datetime.datetime)):
            date_str = date_val.strftime("%Y-%m-%d")
        else:
            date_str = str(date_val)
        items.append({
            "id": article["link"],
            "title": article["title"],
            "url": article["link"],
            "date_published": date_str + "T08:00:00Z",
            "author": {"name": article.get("source", "")},
            "summary": extract_description(article["filepath"], 300, article["meta"]),
            "category": [{"name": article.get("category_label", "")}],
        })

    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": title,
        "home_page_url": link,
        "feed_url": f"{link}feed.json",
        "description": config["description"],
        "language": config["language"],
        "items": items,
    }

    return json.dumps(feed, ensure_ascii=False, indent=2)


# ============================================================
# 主流程
# ============================================================


def generate_feeds(docs_dir: str, output_dir: str,
                   limit: int, category: str = None) -> None:
    """生成所有 feed 文件。"""
    logger.info("扫描文章目录: %s", docs_dir)

    # 扫描文章
    articles = scan_articles(docs_dir, category, limit)
    logger.info("共扫描到 %d 篇文章", len(articles))

    if not articles:
        logger.warning("未找到任何文章，跳过 feed 生成")
        return

    # 生成分类 feed
    if category:
        categories_to_generate = [category]
    else:
        categories_to_generate = list(CATEGORIES.keys())

    for cat in categories_to_generate:
        cat_articles = [a for a in articles if a["category"] == cat]
        if not cat_articles:
            continue

        cat_dir = os.path.join(output_dir, cat)
        os.makedirs(cat_dir, exist_ok=True)

        # RSS 2.0
        rss_content = generate_rss2(cat_articles, FEED_CONFIG, category=cat)
        rss_path = os.path.join(cat_dir, "feed.xml")
        with open(rss_path, "w", encoding="utf-8") as f:
            f.write(rss_content)
        logger.info("已生成: %s", rss_path)

        # Atom
        atom_content = generate_atom(cat_articles, FEED_CONFIG, category=cat)
        atom_path = os.path.join(cat_dir, "feed-atom.xml")
        with open(atom_path, "w", encoding="utf-8") as f:
            f.write(atom_content)
        logger.info("已生成: %s", atom_path)

    # 生成全站 feed（仅当生成所有分类时）
    if not category:
        # RSS 2.0 全站
        rss_content = generate_rss2(articles, FEED_CONFIG)
        rss_path = os.path.join(output_dir, "feed.xml")
        with open(rss_path, "w", encoding="utf-8") as f:
            f.write(rss_content)
        logger.info("已生成: %s", rss_path)

        # Atom 全站
        atom_content = generate_atom(articles, FEED_CONFIG)
        atom_path = os.path.join(output_dir, "feed-atom.xml")
        with open(atom_path, "w", encoding="utf-8") as f:
            f.write(atom_content)
        logger.info("已生成: %s", atom_path)

        # JSON Feed 全站
        json_content = generate_json_feed(articles, FEED_CONFIG)
        json_path = os.path.join(output_dir, "feed.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        logger.info("已生成: %s", json_path)

    logger.info("Feed 生成完成！")


def main():
    """主入口函数。"""
    parser = argparse.ArgumentParser(
        description="智慧农业资讯站 - RSS Feed 生成脚本"
    )
    parser.add_argument(
        "--docs-dir",
        default=None,
        help="docs 目录路径（默认为脚本上级目录的 docs/）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出目录（默认同 docs-dir）",
    )
    parser.add_argument(
        "--category",
        choices=list(CATEGORIES.keys()),
        help="仅生成指定分类的 feed",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="每类最多包含文章数（默认 50）",
    )
    args = parser.parse_args()

    # 确定目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = args.docs_dir or os.path.normpath(os.path.join(script_dir, "..", "docs"))
    output_dir = args.output or docs_dir

    if not os.path.isdir(docs_dir):
        logger.error("docs 目录不存在: %s", docs_dir)
        sys.exit(1)

    generate_feeds(docs_dir, output_dir, args.limit, args.category)


if __name__ == "__main__":
    main()
