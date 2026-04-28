#!/bin/bash
# ============================================================
# 智慧农业资讯站 - 一键更新脚本
#
# 功能：抓取新闻 → 更新侧边栏 → 生成 RSS → 构建网站
# 用法：
#   bash scripts/run.sh            # 完整流程：抓取 + 构建
#   bash scripts/run.sh --fetch    # 仅抓取，不构建
#   bash scripts/run.sh --build    # 仅构建，不抓取
#   bash scripts/run.sh --feed     # 仅生成 RSS feed
#   bash scripts/run.sh --sitemap  # 仅生成 Sitemap
#   bash scripts/run.sh --dry-run  # 预览模式
#   bash scripts/run.sh --concurrent  # 启用并发抓取
#   bash scripts/run.sh --workers 5   # 指定并发数为 5
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$SCRIPT_DIR/run.log"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"; }
err() { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"; }

# 参数解析
DO_FETCH=true
DO_BUILD=true
DO_FEED=true
DO_SITEMAP=false
DRY_RUN=""
CONCURRENT=""
WORKERS=""

for arg in "$@"; do
  case $arg in
    --fetch)       DO_BUILD=false; DO_FEED=false; DO_SITEMAP=false ;;
    --build)       DO_FETCH=false; DO_FEED=false; DO_SITEMAP=false ;;
    --feed)        DO_FETCH=false; DO_BUILD=false; DO_FEED=true; DO_SITEMAP=false ;;
    --sitemap)     DO_FETCH=false; DO_BUILD=false; DO_FEED=false; DO_SITEMAP=true ;;
    --dry-run)     DRY_RUN="--dry-run" ;;
    --concurrent)  CONCURRENT="--concurrent" ;;
    --workers)     WORKERS="--workers $2"; shift ;;
  esac
done

cd "$PROJECT_DIR"

# ── 第1步：抓取新闻 ──
if [ "$DO_FETCH" = true ]; then
  log "第1步：开始抓取新闻..."
  python3 "$SCRIPT_DIR/fetch_news.py" $DRY_RUN $CONCURRENT $WORKERS 2>&1 | tee -a "$LOG_FILE"

  log "第2步：更新侧边栏配置..."
  python3 "$SCRIPT_DIR/update_sidebar.py" 2>&1 | tee -a "$LOG_FILE"

  log "第3步：生成文章数据..."
  python3 "$SCRIPT_DIR/generate_articles_json.py" 2>&1 | tee -a "$LOG_FILE"

  log "第4步：生成 RSS Feed..."
  python3 "$SCRIPT_DIR/generate_feed.py" 2>&1 | tee -a "$LOG_FILE"

  log "第5步：生成 Sitemap..."
  python3 "$SCRIPT_DIR/generate_sitemap.py" 2>&1 | tee -a "$LOG_FILE"
fi

# ── 第6步：构建网站 ──
if [ "$DO_BUILD" = true ] && [ -z "$DRY_RUN" ]; then
  log "第6步：构建 VitePress 网站..."

  # 检查 node_modules
  if [ ! -d "node_modules" ]; then
    log "安装 Node.js 依赖..."
    npm install
  fi

  npm run build 2>&1 | tee -a "$LOG_FILE"
  log "网站构建完成！输出目录: docs/.vitepress/dist/"
fi

# ── 仅生成 Sitemap ──
if [ "$DO_SITEMAP" = true ]; then
  log "生成 Sitemap..."
  python3 "$SCRIPT_DIR/generate_sitemap.py" 2>&1 | tee -a "$LOG_FILE"
  log "Sitemap 生成完成！"
fi

log "全部完成！"
