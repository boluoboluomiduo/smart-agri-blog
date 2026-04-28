#Requires -Version 5.1
# ============================================================
# 智慧农业资讯站 - PowerShell 一键更新脚本
#
# 功能：抓取新闻 → 更新侧边栏 → 生成 RSS → 构建网站
# 用法：
#   .\run.ps1              # 完整流程：抓取 + 构建
#   .\run.ps1 -Fetch       # 仅抓取，不构建
#   .\run.ps1 -Build       # 仅构建，不抓取
#   .\run.ps1 -Feed        # 仅生成 RSS feed
#   .\run.ps1 -Sitemap     # 仅生成 Sitemap
#   .\run.ps1 -DryRun      # 预览模式
#   .\run.ps1 -Concurrent  # 启用并发抓取
#   .\run.ps1 -Workers 5   # 指定并发数为 5
# ============================================================

[CmdletBinding()]
param(
    [switch]$Fetch,          # 仅抓取，不构建
    [switch]$Build,          # 仅构建，不抓取
    [switch]$Feed,           # 仅生成 RSS feed
    [switch]$Sitemap,        # 仅生成 Sitemap
    [switch]$DryRun,         # 预览模式
    [switch]$Concurrent,     # 启用并发抓取
    [int]$Workers = 0        # 并发工作线程数（0 表示使用配置文件默认）
)

$ErrorActionPreference = "Continue"
$ScriptDir = $PSScriptRoot
$ProjectDir = Split-Path $ScriptDir -Parent
$LogFile = Join-Path $ScriptDir "run.log"

# 颜色定义
function Write-Log($Message, $Level = "Info") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "Error" { "Red" }
        "Warning" { "Yellow" }
        "Success" { "Green" }
        default { "White" }
    }
    $logEntry = "[$timestamp] $Message"
    Write-Host $logEntry -ForegroundColor $color
    Add-Content -Path $LogFile -Value $logEntry -Encoding UTF8
}

# 切换到项目目录
Set-Location $ProjectDir

Write-Log "===== 智慧农业资讯站 - 开始运行 =====" "Success"
Write-Log ""

# ── 参数解析 ──
$DoFetch = -not $Build -and -not $Feed -and -not $Sitemap
$DoBuild = -not $Fetch -and -not $Feed -and -not $Sitemap
$DoFeedOnly = $Feed
$DoSitemapOnly = $Sitemap

# ── 第1步：抓取新闻 ──
if ($DoFetch) {
    Write-Log "第1步：开始抓取新闻..."
    $fetchCmd = "python `"$ScriptDir\fetch_news.py`""
    if ($DryRun) { $fetchCmd += " --dry-run" }
    if ($Concurrent) { $fetchCmd += " --concurrent" }
    if ($Workers -gt 0) { $fetchCmd += " --workers $Workers" }
    
    try {
        Invoke-Expression $fetchCmd 2>&1 | Tee-Object -FilePath $LogFile -Append
        Write-Log "新闻抓取完成" "Success"
    } catch {
        Write-Log "新闻抓取失败: $_" "Error"
    }
    Write-Log ""

    Write-Log "第2步：更新侧边栏配置..."
    try {
        python "$ScriptDir\update_sidebar.py" 2>&1 | Tee-Object -FilePath $LogFile -Append
        Write-Log "侧边栏更新完成" "Success"
    } catch {
        Write-Log "侧边栏更新失败: $_" "Error"
    }
    Write-Log ""

    Write-Log "第3步：生成文章数据..."
    try {
        python "$ScriptDir\generate_articles_json.py" 2>&1 | Tee-Object -FilePath $LogFile -Append
        Write-Log "文章数据生成完成" "Success"
    } catch {
        Write-Log "文章数据生成失败: $_" "Error"
    }
    Write-Log ""

    Write-Log "第4步：生成 RSS Feed..."
    try {
        python "$ScriptDir\generate_feed.py" 2>&1 | Tee-Object -FilePath $LogFile -Append
        Write-Log "RSS Feed 生成完成" "Success"
    } catch {
        Write-Log "RSS Feed 生成失败: $_" "Error"
    }
    Write-Log ""
}

# ── 第5步：构建网站 ──
if ($DoBuild -and -not $DryRun) {
    Write-Log "第5步：构建 VitePress 网站..."
    
    if (-not (Test-Path "node_modules")) {
        Write-Log "安装 Node.js 依赖..."
        try {
            npm install 2>&1 | Tee-Object -FilePath $LogFile -Append
            Write-Log "依赖安装完成" "Success"
        } catch {
            Write-Log "依赖安装失败: $_" "Error"
        }
    }

    try {
        npm run build 2>&1 | Tee-Object -FilePath $LogFile -Append
        Write-Log "网站构建完成！输出目录: docs\.vitepress\dist\" "Success"
    } catch {
        Write-Log "网站构建失败: $_" "Error"
    }
    Write-Log ""
}

# ── 仅生成 RSS ──
if ($DoFeedOnly) {
    Write-Log "生成 RSS Feed..."
    try {
        python "$ScriptDir\generate_feed.py" 2>&1 | Tee-Object -FilePath $LogFile -Append
        Write-Log "RSS Feed 生成完成" "Success"
    } catch {
        Write-Log "RSS Feed 生成失败: $_" "Error"
    }
    Write-Log ""
}

# ── 仅生成 Sitemap ──
if ($DoSitemapOnly) {
    Write-Log "生成 Sitemap..."
    try {
        python "$ScriptDir\generate_sitemap.py" 2>&1 | Tee-Object -FilePath $LogFile -Append
        Write-Log "Sitemap 生成完成" "Success"
    } catch {
        Write-Log "Sitemap 生成失败: $_" "Error"
    }
    Write-Log ""
}

Write-Log "===== 全部完成！ =====" "Success"
