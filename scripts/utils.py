#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧农业资讯站 - 公共工具模块

包含各脚本共享的工具函数、常量配置等。
"""

import json
import logging
import os
import re
import time
from datetime import date, datetime
from typing import Optional

import requests
import urllib3
import yaml


# ============================================================
# 全局常量
# ============================================================

CATEGORIES = {
    "policies": "政策法规",
    "news": "行业资讯",
    "cases": "地方案例",
    "standards": "技术标准",
}

CATEGORY_LABELS = CATEGORIES

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "docs"))

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# HTTP 请求默认配置
DEFAULT_REQUEST_TIMEOUT = 15
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2.0
DEFAULT_RETRY_BACKOFF = 2.0  # 指数退避倍数


# ============================================================
# 日志配置
# ============================================================


def setup_logger(
    name: str = None,
    level: int = logging.INFO,
    log_file: str = None,
    format_str: str = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
) -> logging.Logger:
    """
    配置并返回日志记录器。

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        format_str: 日志格式
        datefmt: 日期格式

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(format_str, datefmt)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ============================================================
# HTTP 请求（带重试和 SSL 验证）
# ============================================================


def fetch_page(
    url: str,
    headers: dict = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
    verify_ssl: bool = True,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_RETRY_DELAY,
    backoff_factor: float = DEFAULT_RETRY_BACKOFF,
    logger: logging.Logger = None,
) -> Optional[str]:
    """
    请求指定 URL 并返回页面文本，内置指数退避重试机制。

    Args:
        url: 目标 URL
        headers: 请求头（默认使用内置浏览器 UA）
        timeout: 请求超时（秒）
        verify_ssl: 是否验证 SSL 证书
        max_retries: 最大重试次数
        initial_delay: 初始重试延迟（秒）
        backoff_factor: 指数退避倍数
        logger: 日志记录器（可选）

    Returns:
        页面文本，请求失败时返回 None
    """
    if headers is None:
        headers = DEFAULT_HEADERS

    if logger is None:
        logger = logging.getLogger(__name__)

    delay = initial_delay

    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                logger.info("第 %d 次重试，等待 %.1f 秒后请求: %s", attempt, delay, url)
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.info("正在请求: %s", url)

            resp = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=verify_ssl,
                allow_redirects=True,
            )
            resp.raise_for_status()

            # 自动检测编码
            if resp.encoding and resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding

            return resp.text

        except requests.exceptions.SSLError as exc:
            logger.error("SSL 证书验证失败 [%s]: %s", url, exc)
            if attempt == max_retries:
                return None
        except requests.exceptions.ConnectionError as exc:
            logger.warning("连接失败 [%s]: %s", url, exc)
            if attempt == max_retries:
                return None
        except requests.exceptions.Timeout as exc:
            logger.warning("请求超时 [%s]: %s", url, exc)
            if attempt == max_retries:
                return None
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP 错误 [%s]: %s", url, exc)
            if 400 <= resp.status_code < 500:
                return None
            if attempt == max_retries:
                return None
        except requests.RequestException as exc:
            logger.error("请求失败 [%s]: %s", url, exc)
            if attempt == max_retries:
                return None

    return None


def fetch_page_no_verify(
    url: str,
    headers: dict = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_RETRY_DELAY,
    backoff_factor: float = DEFAULT_RETRY_BACKOFF,
    logger: logging.Logger = None,
) -> Optional[str]:
    """
    请求指定 URL（跳过 SSL 验证），用于证书有问题的网站。

    Args:
        url: 目标 URL
        headers: 请求头
        timeout: 请求超时（秒）
        max_retries: 最大重试次数
        initial_delay: 初始重试延迟（秒）
        backoff_factor: 指数退避倍数
        logger: 日志记录器

    Returns:
        页面文本，请求失败时返回 None
    """
    return fetch_page(
        url=url,
        headers=headers,
        timeout=timeout,
        verify_ssl=False,
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=backoff_factor,
        logger=logger,
    )


def disable_ssl_warnings():
    """禁用 urllib3 的 SSL 警告（仅在使用 verify_ssl=False 时调用）。"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# 配置加载
# ============================================================


def load_config(config_path: str) -> dict:
    """
    读取并返回 YAML 配置文件内容。

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典

    Raises:
        ValueError: 配置文件为空或格式错误
    """
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg:
        raise ValueError(f"配置文件为空或格式错误: {config_path}")
    return cfg


# ============================================================
# Frontmatter 解析
# ============================================================


def read_frontmatter(filepath: str) -> Optional[dict]:
    """
    从 Markdown 文件中解析 YAML frontmatter。

    Args:
        filepath: Markdown 文件路径

    Returns:
        元数据字典，解析失败时返回 None
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None

    try:
        meta = yaml.safe_load(match.group(1))
        if isinstance(meta, dict):
            # 将 YAML 自动解析的 date/datetime 对象转为字符串
            for key, value in meta.items():
                if isinstance(value, (date, datetime)):
                    if isinstance(value, datetime):
                        meta[key] = value.strftime("%Y-%m-%d")
                    else:
                        meta[key] = value.isoformat()
            return meta
    except yaml.YAMLError:
        pass
    return None


# ============================================================
# 日期处理
# ============================================================


def extract_date_from_text(text: str) -> str:
    """
    从文本中提取日期字符串（YYYY-MM-DD 格式）。

    Args:
        text: 包含日期的文本

    Returns:
        提取的日期字符串，未找到则返回当天日期
    """
    patterns = [
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        r"(\d{4})/(\d{1,2})/(\d{1,2})",
        r"(\d{4})年(\d{1,2})月(\d{1,2})日?",
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            y, m, d = match.group(1), match.group(2), match.group(3)
            try:
                dt = date(int(y), int(m), int(d))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return date.today().strftime("%Y-%m-%d")


def format_rfc2822_date(date_str) -> str:
    """
    将日期转换为 RFC 2822 格式（用于 RSS）。

    Args:
        date_str: 日期字符串或日期对象

    Returns:
        RFC 2822 格式的日期字符串
    """
    try:
        if isinstance(date_str, date) and not isinstance(date_str, datetime):
            dt = datetime(date_str.year, date_str.month, date_str.day)
        elif isinstance(date_str, datetime):
            dt = date_str
        else:
            dt = datetime.strptime(str(date_str), "%Y-%m-%d")
        # 使用英文月份和星期缩写，避免中文 locale 影响
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return f"{days[dt.weekday()]}, {dt.day:02d} {months[dt.month - 1]} {dt.year} 08:00:00 +0000"
    except (ValueError, TypeError):
        now = datetime.now()
        return f"{days[now.weekday()]}, {now.day:02d} {months[now.month - 1]} {now.year} 08:00:00 +0000"


def format_iso8601_date(date_str) -> str:
    """
    将日期转换为 ISO 8601 格式（用于 Atom）。

    Args:
        date_str: 日期字符串或日期对象

    Returns:
        ISO 8601 格式的日期字符串
    """
    try:
        if isinstance(date_str, date) and not isinstance(date_str, datetime):
            dt = datetime(date_str.year, date_str.month, date_str.day)
        elif isinstance(date_str, datetime):
            dt = date_str
        else:
            dt = datetime.strptime(str(date_str), "%Y-%m-%d")
        return dt.isoformat() + "Z"
    except (ValueError, TypeError):
        return datetime.now().isoformat() + "Z"


# ============================================================
# 文本清理
# ============================================================


def clean_markdown_content(content: str) -> str:
    """
    清理 Markdown 内容，移除 frontmatter 和格式标记。

    Args:
        content: 原始 Markdown 内容

    Returns:
        清理后的纯文本内容
    """
    # 移除 frontmatter
    match = re.match(r"^---\s*\n.*?\n---\n", content, re.DOTALL)
    if match:
        content = content[match.end():]

    # 移除 Markdown 标题
    content = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)
    # 移除链接语法，保留文本
    content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)
    # 移除图片
    content = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", content)
    # 移除 blockquote 标记
    content = re.sub(r"^>\s*", "", content, flags=re.MULTILINE)
    # 移除 Markdown 代码块
    content = re.sub(r"```[\s\S]*?```", "", content)
    # 移除 HTML 标签
    content = re.sub(r"<[^>]+>", "", content)
    # 清理多余空行
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content.strip()


# ============================================================
# 文件扫描
# ============================================================


def scan_category_articles(
    docs_dir: str,
    category: str,
    exclude_files: list = None,
) -> list[dict]:
    """
    扫描指定分类目录下的所有 Markdown 文章文件。

    Args:
        docs_dir: docs 目录路径
        category: 分类目录名
        exclude_files: 要排除的文件名列表

    Returns:
        文章元数据列表，按日期降序排列
    """
    if exclude_files is None:
        exclude_files = ["index.md"]

    cat_dir = os.path.join(docs_dir, category)
    if not os.path.isdir(cat_dir):
        return []

    articles = []
    for fname in os.listdir(cat_dir):
        if not fname.endswith(".md") or fname in exclude_files:
            continue

        fpath = os.path.join(cat_dir, fname)
        meta = read_frontmatter(fpath)
        if not meta:
            continue

        articles.append({
            "filepath": fpath,
            "filename": fname,
            "meta": meta,
        })

    # 按日期降序排列
    articles.sort(
        key=lambda a: a["meta"].get("date", ""),
        reverse=True,
    )
    return articles


# ============================================================
# 路径处理
# ============================================================


def get_docs_dir(relative_path: str = "../docs") -> str:
    """
    获取 docs 目录的绝对路径。

    Args:
        relative_path: 相对于脚本目录的路径

    Returns:
        docs 目录的绝对路径
    """
    return os.path.normpath(os.path.join(SCRIPT_DIR, relative_path))


def get_category_dir(docs_dir: str, category: str) -> str:
    """
    获取分类目录的绝对路径。

    Args:
        docs_dir: docs 目录路径
        category: 分类目录名

    Returns:
        分类目录的绝对路径
    """
    return os.path.join(docs_dir, category)


def extract_description(filepath: str, max_len: int = 150, meta: dict = None) -> str:
    """从 Markdown 文件中提取摘要（优先使用 frontmatter summary）。

    Args:
        filepath: Markdown 文件路径
        max_len: 摘要最大长度
        meta: 已解析的 frontmatter（可选，避免重复解析）
    """
    if meta is None:
        meta = read_frontmatter(filepath)

    # 优先使用 frontmatter 中的 summary
    if meta and meta.get("summary"):
        desc = meta["summary"]
        if len(desc) > max_len:
            desc = desc[:max_len].rsplit("。", 1)[0] + "..."
        return desc

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return ""

    # 移除 frontmatter
    match = re.match(r"^---\s*\n.*?\n---\n", content, re.DOTALL)
    if match:
        content = content[match.end():]

    # 移除 Markdown 标题、链接语法、图片等
    content = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)
    content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)
    content = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", content)
    content = re.sub(r"^>\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"```[\s\S]*?```", "", content)
    content = re.sub(r"<[^>]+>", "", content)

    # 清理多余空行
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = content.strip()

    # 取前 max_len 个字符
    if len(content) > max_len:
        content = content[:max_len].rsplit("。", 1)[0] + "..."

    return content


def filepath_to_route(filepath: str, docs_dir: str) -> str:
    """
    将文件绝对路径转换为 VitePress 路由。

    Args:
        filepath: 文件绝对路径
        docs_dir: docs 目录路径

    Returns:
        VitePress 路由（如 /news/2024-01-01-title）
    """
    rel_path = os.path.relpath(filepath, docs_dir)
    # 将 Windows 路径分隔符转为正斜杠
    rel_path = rel_path.replace("\\", "/")
    # 移除 .md 后缀
    if rel_path.endswith(".md"):
        rel_path = rel_path[:-3]
    # 确保以 / 开头
    if not rel_path.startswith("/"):
        rel_path = "/" + rel_path
    return rel_path
