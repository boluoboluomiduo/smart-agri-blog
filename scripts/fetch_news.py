#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧农业新闻聚合 - 新闻抓取脚本 (增强版)

从配置的多个农业新闻源抓取文章标题、链接、日期和正文内容，
生成 Markdown 文件并更新各分类的索引页面。

增强功能:
- 支持抓取文章详情页正文内容
- 多种内容提取策略，自动回退
- 基于内容哈希的去重机制
- 增量更新检测
- 自动生成文章摘要

用法:
    python fetch_news.py              # 正常运行，抓取并写入文件
    python fetch_news.py --dry-run    # 预览模式，不写入文件
    python fetch_news.py --force      # 强制更新已有文章
    python fetch_news.py --no-content # 仅抓取列表，不获取正文
"""

import os
import re
import sys
import json
import time
import hashlib
import argparse
import datetime
import logging
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml
from bs4 import BeautifulSoup

from utils import (
    CATEGORY_LABELS,
    load_config,
    extract_date_from_text,
    read_frontmatter,
    setup_logger,
    fetch_page as fetch_page_with_retry,
    disable_ssl_warnings,
)

# ============================================================
# 日志配置
# ============================================================

logger = setup_logger(__name__)

# 请求间隔（秒），避免频繁请求被封
REQUEST_DELAY = 1.0

# 回退通用选择器 —— 当配置的选择器未匹配到内容时使用
FALLBACK_LIST_SELECTORS = [
    "ul li",
    "div.list li",
    "div.newsList li",
    "div.article-list li",
    "ol li",
]

# 正文提取候选选择器（按优先级排序）
CONTENT_SELECTORS = [
    # 通用内容容器
    "article",
    "article.content",
    "article.con",
    ".article-content",
    ".article-con",
    ".article-text",
    ".article-body",
    ".article",
    ".content",
    ".con",
    # 新闻专用
    ".news-content",
    ".news-con",
    ".news_text",
    ".newsDetail",
    ".detail_content",
    # 政府网站
    ".TRS_Editor",
    "#TRS_Editor",
    ".article-content-wrap",
    ".articleView",
    # 博客/论坛
    ".post-content",
    ".post-body",
    ".entry-content",
    ".content-body",
    # 兜底
    "main",
    ".main",
    "#main",
]

# 要移除的无关元素选择器
REMOVE_SELECTORS = [
    "script", "style", "iframe", "nav", "header", "footer",
    ".nav", ".navbar", ".menu", ".sidebar", ".advertisement",
    ".ad", ".ads", ".related", ".share", ".comment", ".author",
    "[class*='copyright']", "[class*='footer']", "[class*='header']",
    "[class*='nav']", "[class*='menu']", "[class*='share']",
    "[class*='social']", "[class*='related']", "[class*='recommend']",
    "form", "button", ".fixed", ".back-top",
]

# 数据文件路径（用于存储已抓取内容哈希）
HASH_FILE = ".article_hashes.json"


def slugify(text: str, max_len: int = 50) -> str:
    """
    将标题转为适合文件名的 slug。
    自动去除标题中自带的日期，避免文件名出现重复日期。
    """
    text = text.strip()
    # 去除标题中自带的日期（如 "2026-03-27"、"2026年03月27日"）
    text = re.sub(r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?", "", text).strip()
    text = re.sub(r"[^\w一-鿿]+", "-", text)
    text = text.strip("-")
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text


def compute_content_hash(title: str, content: str) -> str:
    """计算内容的 MD5 哈希值，用于去重。"""
    combined = f"{title}|{content[:1000]}"  # 用标题+正文前1000字符
    return hashlib.md5(combined.encode("utf-8")).hexdigest()


def load_hash_store(script_dir: str) -> dict:
    """加载已抓取文章的哈希存储。"""
    hash_path = os.path.join(script_dir, HASH_FILE)
    if os.path.exists(hash_path):
        try:
            with open(hash_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_hash_store(script_dir: str, store: dict) -> None:
    """保存文章哈希存储。"""
    hash_path = os.path.join(script_dir, HASH_FILE)
    try:
        with open(hash_path, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except IOError as exc:
        logger.warning("无法保存哈希存储: %s", exc)


def clean_html_text(html_content: str) -> str:
    """清理 HTML 标签，提取纯文本。"""
    soup = BeautifulSoup(html_content, "html.parser")
    # 移除无关元素
    for sel in REMOVE_SELECTORS:
        for elem in soup.select(sel):
            elem.decompose()
    # 获取文本
    text = soup.get_text(separator="\n", strip=True)
    # 清理多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_summary(content: str, max_len: int = 200) -> str:
    """从正文中提取摘要。"""
    # 清理文本
    text = clean_html_text(content)
    if not text:
        return ""
    # 取前 max_len 个字符
    summary = text[:max_len]
    # 在句号或换行处截断
    match = re.search(r'[。！？\n][^。！？\n]*$', summary)
    if match:
        summary = summary[:match.start() + 1]
    if len(text) > max_len:
        summary += "..."
    return summary


def html_to_markdown(html_content: str) -> str:
    """将 HTML 内容转换为 Markdown 格式。"""
    soup = BeautifulSoup(html_content, "html.parser")

    # 移除无关元素
    for sel in REMOVE_SELECTORS:
        for elem in soup.select(sel):
            elem.decompose()

    lines = []

    for elem in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6",
                                "ul", "ol", "li", "blockquote", "pre", "code"]):
        tag_name = elem.name

        if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag_name[1])
            text = elem.get_text(strip=True)
            if text:
                lines.append(f"{'#' * level} {text}")
                lines.append("")

        elif tag_name == "p":
            text = elem.get_text(strip=True)
            if text:
                lines.append(text)
                lines.append("")

        elif tag_name == "blockquote":
            text = elem.get_text(strip=True)
            if text:
                for line in text.split("\n"):
                    lines.append(f"> {line}")
                lines.append("")

        elif tag_name == "pre":
            code = elem.get_text(strip=True)
            if code:
                lines.append(f"```\n{code}\n```")
                lines.append("")

        elif tag_name == "code":
            text = elem.get_text(strip=True)
            if text and elem.parent.name != "pre":
                lines.append(f"`{text}`")

        elif tag_name == "ul":
            for li in elem.find_all("li", recursive=False):
                text = li.get_text(strip=True)
                if text:
                    lines.append(f"- {text}")
            lines.append("")

        elif tag_name == "ol":
            for i, li in enumerate(elem.find_all("li", recursive=False), 1):
                text = li.get_text(strip=True)
                if text:
                    lines.append(f"{i}. {text}")
            lines.append("")

    # 清理多余空行
    result = "\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def make_frontmatter(title: str, date: str, source: str,
                     category: str, link: str, tags: list,
                     summary: str = "", content_hash: str = "") -> str:
    """生成 Markdown 文件的 YAML frontmatter。"""
    tag_str = "\n".join(f"  - {t}" for t in tags)
    lines = [
        "---",
        f"title: \"{title}\"",
        f"date: {date}",
        f"source: \"{source}\"",
        f"category: {category}",
        f"link: \"{link}\"",
    ]
    if summary:
        # 多行摘要需要使用 | 或 >
        lines.append(f"summary: |")
        for s_line in summary.split("\n"):
            lines.append(f"  {s_line}")
    if content_hash:
        lines.append(f"contentHash: \"{content_hash}\"")
    lines.append(f"tags:")
    lines.append(tag_str)
    lines.append("---")
    return "\n".join(lines) + "\n"


# ============================================================
# 页面抓取与解析
# ============================================================


def fetch_page(url: str, delay: float = REQUEST_DELAY, verify_ssl: bool = True) -> str | None:
    """
    请求指定 URL 并返回页面 HTML 文本（带重试机制）。

    Args:
        url: 目标 URL
        delay: 请求间隔（秒），0 表示不延迟
        verify_ssl: 是否验证 SSL 证书

    Returns:
        页面 HTML 文本，请求失败时返回 None
    """
    html = fetch_page_with_retry(url, verify_ssl=verify_ssl, logger=logger)
    if html and delay > 0:
        time.sleep(delay)
    return html


def fetch_article_content(url: str, delay: float = REQUEST_DELAY, verify_ssl: bool = True) -> str | None:
    """
    获取文章详情页的正文内容。
    使用多种策略提取内容。
    """
    html = fetch_page(url, delay=delay, verify_ssl=verify_ssl)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    for selector in CONTENT_SELECTORS:
        content_elem = soup.select_one(selector)
        if content_elem:
            text = content_elem.get_text(strip=True)
            if len(text) > 100:
                logger.info("使用选择器 '%s' 提取到正文 (%d 字符)", selector, len(text))
                return str(content_elem)

    logger.info("使用兜底策略提取正文")
    body = soup.find("body")
    if body:
        return str(body)

    return None


def parse_articles(html: str, source_cfg: dict) -> list[dict]:
    """
    解析 HTML 页面，根据配置的 CSS 选择器提取文章列表。
    """
    soup = BeautifulSoup(html, "html.parser")
    selectors = source_cfg.get("selectors", {})
    base_url = source_cfg["url"]

    list_selector = selectors.get("list", "")
    title_selector = selectors.get("title", "a")
    date_selector = selectors.get("date", "span")

    # 先尝试配置的选择器，再尝试回退选择器
    items = []
    if list_selector:
        items = soup.select(list_selector)
    if not items:
        logger.info("配置选择器未匹配，尝试回退选择器...")
        for fallback in FALLBACK_LIST_SELECTORS:
            items = soup.select(fallback)
            if items:
                logger.info("回退选择器 '%s' 匹配到 %d 项", fallback, len(items))
                break

    if not items:
        logger.warning("未能从 %s 解析到任何列表项", base_url)
        return []

    articles = []
    max_articles = source_cfg.get("_max", 5)

    for item in items:
        if len(articles) >= max_articles:
            break

        # 提取标题和链接
        a_tag = item.select_one(title_selector) if title_selector else item.find("a")
        if not a_tag:
            a_tag = item.find("a")
        if not a_tag:
            continue

        title = a_tag.get_text(strip=True)
        href = a_tag.get("href", "")

        # 过滤无效条目
        if not title or len(title) < 6:
            continue
        if not href or href == "#" or href.startswith("javascript:"):
            continue
        # 过滤导航菜单
        nav_keywords = [
            "首页", "通知公告", "政策解读", "机构职能", "市场回声",
            "联系我们", "网站地图", "更多>>", "查看更多", "下载",
            "关于我们", "版权声明", "友情链接",
        ]
        if title in nav_keywords or len(title) <= 4:
            continue
        # 过滤不含路径的链接
        parsed = urlparse(urljoin(base_url, href))
        if parsed.path in ('/', '') and not parsed.query:
            continue

        # 将相对链接转为绝对链接
        link = urljoin(base_url, href)

        # 提取日期
        date_el = item.select_one(date_selector) if date_selector else None
        if date_el:
            date_text = date_el.get_text(strip=True)
        else:
            date_text = item.get_text()
        article_date = extract_date_from_text(date_text)

        articles.append({
            "title": title,
            "link": link,
            "date": article_date,
        })

    logger.info("从 %s 解析到 %d 篇文章", source_cfg["name"], len(articles))
    return articles


# ============================================================
# 文件写入
# ============================================================


def write_article_md(article: dict, source_name: str, category: str,
                     output_dir: str, dry_run: bool = False,
                     force_update: bool = False,
                     fetch_content: bool = True,
                     verify_ssl: bool = True) -> str | None:
    """
    将单篇文章写入 Markdown 文件。
    返回写入的文件路径，若跳过则返回 None。
    """
    cat_dir = os.path.join(output_dir, category)
    os.makedirs(cat_dir, exist_ok=True)

    slug = slugify(article["title"])
    if not slug:
        slug = "untitled"
    filename = f"{article['date']}-{slug}.md"
    filepath = os.path.join(cat_dir, filename)

    # 加载哈希存储
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hash_store = load_hash_store(script_dir)
    file_key = f"{category}/{filename}"

    # 检查内容变化
    content_changed = True
    raw_content = None
    summary = ""
    content_hash = ""

    if os.path.exists(filepath) and not force_update:
        existing = read_frontmatter(filepath)
        if existing:
            # 检查标题是否相同
            if existing.get("title") == article["title"]:
                logger.info("文件已存在，内容未变，跳过: %s", filename)
                return None

    # 获取正文内容
    if fetch_content:
        logger.info("正在抓取文章内容: %s", article["title"])
        raw_content = fetch_article_content(article["link"], verify_ssl=verify_ssl)
        if raw_content:
            # 转换为 Markdown
            content_md = html_to_markdown(raw_content)
            if content_md:
                article["content"] = content_md
            # 提取摘要
            summary = extract_summary(raw_content)
            # 计算哈希
            content_hash = compute_content_hash(article["title"], raw_content)

            # 检查哈希是否变化
            if file_key in hash_store and hash_store[file_key] == content_hash:
                logger.info("文章内容未变化，跳过: %s", filename)
                return None
    else:
        raw_content = None

    tags = ["智慧农业", CATEGORY_LABELS.get(category, category)]

    frontmatter = make_frontmatter(
        title=article["title"],
        date=article["date"],
        source=source_name,
        category=category,
        link=article["link"],
        tags=tags,
        summary=summary,
        content_hash=content_hash,
    )

    # 构建正文
    body_lines = [f"\n# {article['title']}\n"]
    body_lines.append(f"> 来源: [{source_name}]({article['link']})  ")
    body_lines.append(f"> 日期: {article['date']}")
    if summary:
        body_lines.append(f"> 摘要: {summary}")
    if summary:
        body_lines.append(f"> 摘要: {summary}")
    body_lines.append("")

    # 添加正文内容
    if article.get("content"):
        body_lines.append(article["content"])
        body_lines.append("")

    body_lines.append(f"\n[阅读原文]({article['link']})\n")

    content = frontmatter + "\n".join(body_lines)

    if dry_run:
        logger.info("[预览] 将写入: %s", filepath)
        return filepath

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # 更新哈希存储
    if content_hash:
        hash_store[file_key] = content_hash
        save_hash_store(script_dir, hash_store)

    logger.info("已写入: %s", filepath)
    return filepath


# ============================================================
# 主流程
# ============================================================


def process_source(source_cfg: dict, output_dir: str,
                  max_articles: int, dry_run: bool,
                  force_update: bool, fetch_content: bool,
                  global_verify_ssl: bool = True) -> int:
    """
    处理单个新闻源：抓取页面 → 解析文章 → 抓取正文 → 写入文件。
    返回成功写入的文章数。
    """
    name = source_cfg["name"]
    url = source_cfg["url"]
    category = source_cfg.get("category", "news")

    verify_ssl = source_cfg.get("verify_ssl", global_verify_ssl)

    logger.info("=" * 50)
    logger.info("处理来源: %s (%s) [SSL: %s]", name, url, "开启" if verify_ssl else "关闭")

    html = fetch_page(url, delay=0, verify_ssl=verify_ssl)
    if not html:
        logger.warning("无法获取页面内容，跳过: %s", name)
        return 0

    source_cfg["_max"] = max_articles
    source_cfg["_verify_ssl"] = verify_ssl
    articles = parse_articles(html, source_cfg)
    if not articles:
        logger.warning("未解析到文章，跳过: %s", name)
        return 0

    written = 0
    for article in articles:
        try:
            result = write_article_md(
                article=article,
                source_name=name,
                category=category,
                output_dir=output_dir,
                dry_run=dry_run,
                force_update=force_update,
                fetch_content=fetch_content,
                verify_ssl=verify_ssl,
            )
            if result:
                written += 1
        except Exception as exc:
            logger.error("处理文章 '%s' 时出错: %s", article.get("title", "?"), exc)
            continue

    return written


def process_sources_concurrent(sources: list, output_dir: str,
                               max_articles: int, dry_run: bool,
                               force_update: bool, fetch_content: bool,
                               global_verify_ssl: bool,
                               max_workers: int = 3) -> int:
    """
    并发处理多个新闻源。
    返回列表页抓取阶段成功获取的文章总数。
    """
    results = {}

    def fetch_list_page(source_cfg):
        """仅抓取列表页并解析文章（线程安全）。"""
        name = source_cfg["name"]
        url = source_cfg["url"]
        category = source_cfg.get("category", "news")
        verify_ssl = source_cfg.get("verify_ssl", global_verify_ssl)

        logger.info("[%s] 正在抓取列表页...", name)
        html = fetch_page(url, delay=0, verify_ssl=verify_ssl)
        if not html:
            logger.warning("[%s] 无法获取页面内容", name)
            return None

        source_cfg["_max"] = max_articles
        source_cfg["_verify_ssl"] = verify_ssl
        articles = parse_articles(html, source_cfg)
        if not articles:
            logger.warning("[%s] 未解析到文章", name)
            return None

        return {
            "name": name,
            "category": category,
            "verify_ssl": verify_ssl,
            "articles": articles,
        }

    # 阶段一：并发抓取所有来源的列表页
    logger.info("=" * 50)
    logger.info("开始并发抓取 %d 个来源的列表页（并发数：%d）", len(sources), max_workers)

    list_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_source = {
            executor.submit(fetch_list_page, source): source
            for source in sources
        }
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                result = future.result()
                if result:
                    list_results.append(result)
                    logger.info("[%s] 列表页抓取成功，解析到 %d 篇文章",
                              result["name"], len(result["articles"]))
            except Exception as exc:
                logger.error("[%s] 列表页抓取出错: %s", source.get("name", "?"), exc)

    if not list_results:
        logger.warning("所有来源列表页抓取均失败")
        return 0

    # 阶段二：串行处理文章写入（避免文件写入竞争）
    logger.info("=" * 50)
    logger.info("开始处理文章写入（共 %d 篇文章）",
              sum(len(r["articles"]) for r in list_results))

    total_written = 0
    for result in list_results:
        name = result["name"]
        category = result["category"]
        verify_ssl = result["verify_ssl"]
        articles = result["articles"]

        logger.info("-" * 30)
        logger.info("[%s] 处理 %d 篇文章...", name, len(articles))

        for article in articles:
            try:
                written_path = write_article_md(
                    article=article,
                    source_name=name,
                    category=category,
                    output_dir=output_dir,
                    dry_run=dry_run,
                    force_update=force_update,
                    fetch_content=fetch_content,
                    verify_ssl=verify_ssl,
                )
                if written_path:
                    total_written += 1
            except Exception as exc:
                logger.error("[%s] 处理文章 '%s' 时出错: %s",
                           name, article.get("title", "?"), exc)
                continue

    return total_written


def main():
    """主入口函数：解析参数、加载配置、依次处理各新闻源。"""
    parser = argparse.ArgumentParser(
        description="智慧农业新闻聚合 - 抓取脚本 (增强版)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式，不实际写入文件",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制更新已有文章",
    )
    parser.add_argument(
        "--no-content",
        action="store_true",
        help="仅抓取列表，不获取正文内容",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="配置文件路径（默认为脚本同目录下的 config.yaml）",
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        default=None,
        help="启用并发抓取（覆盖配置文件设置）",
    )
    parser.add_argument(
        "--no-concurrent",
        action="store_true",
        help="禁用并发抓取（覆盖配置文件设置）",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="并发工作线程数（覆盖配置文件设置）",
    )
    args = parser.parse_args()

    # 确定配置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = args.config or os.path.join(script_dir, "config.yaml")

    if not os.path.isfile(config_path):
        logger.error("配置文件不存在: %s", config_path)
        sys.exit(1)

    cfg = load_config(config_path)

    # 解析输出目录
    output_dir = cfg.get("output_dir", "../docs")
    if not os.path.isabs(output_dir):
        output_dir = os.path.normpath(os.path.join(script_dir, output_dir))

    # 从配置读取请求延迟（修复硬编码问题）
    REQUEST_DELAY = cfg.get("request_delay", 1.0)

    max_articles = cfg.get("max_articles_per_source", 5)
    sources = cfg.get("sources", [])

    if not sources:
        logger.error("配置中未定义任何新闻源")
        sys.exit(1)

    if args.dry_run:
        logger.info("*** 预览模式 - 不会写入任何文件 ***")

    fetch_content = not args.no_content

    # 读取全局 SSL 验证配置（默认开启）
    global_verify_ssl = cfg.get("verify_ssl", True)
    if not global_verify_ssl:
        disable_ssl_warnings()
        logger.info("全局 SSL 验证已关闭")

    logger.info("输出目录: %s", output_dir)
    logger.info("新闻源数量: %d", len(sources))
    logger.info("每源最大文章数: %d", max_articles)
    logger.info("请求延迟: %.1f 秒", REQUEST_DELAY)
    logger.info("抓取正文内容: %s", "是" if fetch_content else "否")
    logger.info("强制更新已有文章: %s", "是" if args.force else "否")
    logger.info("SSL 验证: %s", "开启" if global_verify_ssl else "关闭")

    # 确定并发模式（命令行 > 配置文件 > 默认）
    if args.concurrent:
        enable_concurrent = True
    elif args.no_concurrent:
        enable_concurrent = False
    else:
        enable_concurrent = cfg.get("enable_concurrent", False)

    # 确定并发数（命令行 > 配置文件 > 默认）
    max_workers = args.workers or cfg.get("max_workers", 3)

    logger.info("并发抓取: %s", "开启" if enable_concurrent else "关闭")
    if enable_concurrent:
        logger.info("并发工作线程数: %d", max_workers)

    os.makedirs(output_dir, exist_ok=True)

    total_written = 0
    categories_touched = set()

    if enable_concurrent:
        # 并发模式
        total_written = process_sources_concurrent(
            sources, output_dir, max_articles,
            args.dry_run, args.force, fetch_content,
            global_verify_ssl, max_workers,
        )
        # 统计涉及到的分类
        for source in sources:
            categories_touched.add(source.get("category", "news"))
    else:
        # 串行模式
        for source in sources:
            try:
                count = process_source(
                    source, output_dir, max_articles,
                    args.dry_run, args.force, fetch_content,
                    global_verify_ssl,
                )
                total_written += count
                categories_touched.add(source.get("category", "news"))
            except Exception as exc:
                logger.error("处理来源 '%s' 时出错: %s", source.get("name", "?"), exc)
                continue

    # 分类索引页由 index.md 中的 CategoryPage 组件通过 sidebar.json 渲染，
    # 不再需要 update_category_index 生成纯 Markdown 列表。
    logger.info("=" * 50)
    logger.info("分类索引已由 CategoryPage 组件渲染，跳过索引页更新")

    logger.info("=" * 50)
    logger.info("完成！共写入 %d 篇新文章", total_written)


if __name__ == "__main__":
    main()
