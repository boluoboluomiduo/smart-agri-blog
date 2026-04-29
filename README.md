# 智慧农业资讯站

自动化采集 + VitePress 静态博客，定时从权威渠道抓取智慧农业相关资讯并发布。

## 项目结构

```
smart-agri-blog/
├── docs/                          # VitePress 文档目录
│   ├── .vitepress/
│   │   ├── config.mts             # 站点配置（自动加载 sidebar.json）
│   │   ├── sidebar.json           # 自动生成的侧边栏
│   │   └── theme/                 # 自定义主题（绿色农业风格）
│   ├── index.md                   # 首页
│   ├── policies/                  # 政策法规
│   ├── news/                      # 行业资讯
│   ├── cases/                     # 地方案例
│   └── standards/                 # 技术标准
├── scripts/
│   ├── config.yaml                # 采集源配置
│   ├── fetch_news.py              # 新闻采集脚本
│   ├── update_sidebar.py          # 侧边栏生成脚本
│   ├── generate_feed.py           # RSS Feed 生成脚本
│   ├── run.sh                     # Linux/Mac 一键脚本
│   ├── run.bat                    # Windows 批处理脚本
│   └── run.ps1                    # Windows PowerShell 脚本
└── package.json
```

## 快速开始

### 1. 安装依赖

```bash
# Node.js 依赖
npm install

# Python 依赖
pip install -r scripts/requirements.txt
```

### 2. 采集新闻

```bash
# 正常采集（包含正文内容抓取）
python3 scripts/fetch_news.py

# 预览模式（不写入文件）
python3 scripts/fetch_news.py --dry-run

# 仅采集列表，不抓取正文（速度更快）
python3 scripts/fetch_news.py --no-content

# 强制更新已有文章（重新抓取正文）
python3 scripts/fetch_news.py --force

# 更新侧边栏
python3 scripts/update_sidebar.py
```

### 3. 本地预览

```bash
npm run dev
```

### 4. 构建部署

```bash
npm run build
# 产物在 docs/.vitepress/dist/
```

### 5. 一键执行（采集 + 构建）

```bash
# Linux / macOS
bash scripts/run.sh

# Windows CMD
scripts\run.bat

# Windows PowerShell
.\scripts\run.ps1
```

#### Windows 脚本参数

```powershell
# 完整流程（抓取 + 构建）
.\run.ps1

# 仅抓取，不构建
.\run.ps1 -Fetch

# 仅构建，不抓取
.\run.ps1 -Build

# 仅生成 RSS feed
.\run.ps1 -Feed

# 预览模式
.\run.ps1 -DryRun

# 组合使用
.\run.ps1 -Fetch -DryRun
```

## RSS 订阅

网站支持多种 RSS 订阅格式，方便用户通过 RSS 阅读器订阅更新。

### 订阅地址

| 格式 | 地址 | 说明 |
|------|------|------|
| RSS 2.0 | `/feed.xml` | 通用订阅格式 |
| Atom | `/feed-atom.xml` | Atom 标准格式 |
| JSON Feed | `/feed.json` | JSON 格式（现代阅读器）|

### 分类订阅

| 分类 | RSS 2.0 | Atom |
|------|---------|------|
| 政策法规 | `/policies/feed.xml` | `/policies/feed-atom.xml` |
| 行业资讯 | `/news/feed.xml` | `/news/feed-atom.xml` |
| 地方案例 | `/cases/feed.xml` | `/cases/feed-atom.xml` |
| 技术标准 | `/standards/feed.xml` | `/standards/feed-atom.xml` |

### 使用示例

```bash
# 单独生成 RSS feed
python3 scripts/generate_feed.py

# 仅生成特定分类的 feed
python3 scripts/generate_feed.py --category news

# 限制每类文章数量
python3 scripts/generate_feed.py --limit 20
```

### 在 RSS 阅读器中使用

1. 复制上述订阅地址
2. 粘贴到 RSS 阅读器的添加订阅框中
3. 自动获取最新更新

## 定时任务配置

### Linux Crontab（推荐）

```bash
# 编辑 crontab
crontab -e

# 每天早上 8 点自动采集并构建
0 8 * * * cd /path/to/smart-agri-blog && bash scripts/run.sh >> scripts/cron.log 2>&1

# 每 6 小时采集一次（仅采集，不构建）
0 */6 * * * cd /path/to/smart-agri-blog && bash scripts/run.sh --fetch >> scripts/cron.log 2>&1
```

### GitHub Actions（自动部署到 GitHub Pages）

在仓库中创建 `.github/workflows/deploy.yml`：

```yaml
name: 采集并部署

on:
  schedule:
    - cron: '0 0 * * *'   # 每天 UTC 0:00（北京时间 8:00）
  workflow_dispatch:        # 支持手动触发

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 安装依赖
        run: |
          npm install
          pip install -r scripts/requirements.txt

      - name: 采集新闻
        run: |
          python3 scripts/fetch_news.py
          python3 scripts/update_sidebar.py
          python3 scripts/generate_feed.py

      - name: 提交新内容
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/
          git diff --staged --quiet || git commit -m "auto: 更新资讯 $(date +%Y-%m-%d)"
          git push

      - name: 构建网站
        run: npm run build

      - name: 部署到 GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: docs/.vitepress/dist
```

## 添加/修改采集源

编辑 `scripts/config.yaml`，按以下格式添加新源：

```yaml
- name: "源名称"
  url: "https://example.com/news/"
  type: "html"
  category: "news"          # policies / news / cases / standards
  selectors:
    list: "ul.newsList li"  # 列表项选择器
    title: "a"              # 标题选择器
    date: "span.date"       # 日期选择器
```

### 内容抓取设置

配置文件中可调整以下全局设置：

```yaml
# 是否自动抓取文章正文
fetch_content: true

# 请求间隔（秒），避免被封
request_delay: 1.0

# 摘要最大长度
summary_max_length: 200
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 预览模式，不写入文件 |
| `--force` | 强制更新已有文章 |
| `--no-content` | 仅采集列表，不抓取正文 |
| `--config PATH` | 指定配置文件路径 |

## 部署选项

| 平台 | 方式 | 费用 |
|------|------|------|
| GitHub Pages | GitHub Actions 自动部署 | 免费 |
| Cloudflare Pages | 连接 Git 仓库自动构建 | 免费 |
| Vercel | 连接 Git 仓库自动构建 | 免费 |
| 自有服务器 | Nginx 托管 dist 目录 | 服务器费用 |
