@echo off
chcp 65001 >nul
REM ============================================================
REM 智慧农业资讯站 - Windows 一键更新脚本
REM
REM 功能：抓取新闻 → 更新侧边栏 → 生成 RSS → 构建网站
REM 用法：
REM   run.bat              # 完整流程：抓取 + 构建
REM   run.bat --fetch     # 仅抓取，不构建
REM   run.bat --build     # 仅构建，不抓取
REM   run.bat --feed      # 仅生成 RSS feed
REM   run.bat --dry-run   # 预览模式
REM ============================================================

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "LOG_FILE=%SCRIPT_DIR%run.log"

REM 尝试多种方式找到 Python（优先使用 py -3）
set "PYTHON_CMD="
where py >nul 2>&1 && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD where python3 >nul 2>&1 && set "PYTHON_CMD=python3"
if not defined PYTHON_CMD (
    echo [错误] 未找到 Python，请确保已安装 Python
    echo 下载地址: https://www.python.org/downloads/
    exit /b 1
)

REM 验证 Python 版本
for /f "delims=" %%v in ('"%PYTHON_CMD%" --version 2^>^&1') do set "PY_VER=%%v"

set "DO_FETCH=1"
set "DO_BUILD=1"
set "DO_FEED=1"
set "DRY_RUN="

REM 参数解析
:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--fetch" set "DO_BUILD=0"
if /i "%~1"=="--build" set "DO_FETCH=0"
if /i "%~1"=="--feed" set "DO_FETCH=0" & set "DO_BUILD=0" & set "DO_FEED=1"
if /i "%~1"=="--dry-run" set "DRY_RUN=--dry-run"
shift
goto :parse_args

:args_done
cd /d "%PROJECT_DIR%"

REM 获取当前时间戳
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do set "DATE=%%a-%%b-%%c"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "TIME=%%a:%%b"
set "TIMESTAMP=%DATE% %TIME%"

echo ===========================================================
echo [%TIMESTAMP%] 智慧农业资讯站 - 开始运行
echo [信息] Python: %PY_VER%
echo ===========================================================
echo.

REM ── 第1步：抓取新闻 ──
if "%DO_FETCH%"=="1" (
    echo [%TIMESTAMP%] 第1步：开始抓取新闻...
    "%PYTHON_CMD%" "%SCRIPT_DIR%fetch_news.py" %DRY_RUN%
    if errorlevel 1 (
        echo [错误] 新闻抓取失败，请检查日志
    ) else (
        echo [%TIMESTAMP%] 新闻抓取完成
    )
    echo.

    echo [%TIMESTAMP%] 第2步：更新侧边栏配置...
    "%PYTHON_CMD%" "%SCRIPT_DIR%update_sidebar.py"
    if errorlevel 1 (
        echo [错误] 侧边栏更新失败
    ) else (
        echo [%TIMESTAMP%] 侧边栏更新完成
    )
    echo.

    echo [%TIMESTAMP%] 第3步：生成文章数据...
    "%PYTHON_CMD%" "%SCRIPT_DIR%generate_articles_json.py"
    if errorlevel 1 (
        echo [错误] 文章数据生成失败
    ) else (
        echo [%TIMESTAMP%] 文章数据生成完成
    )
    echo.

    echo [%TIMESTAMP%] 第4步：生成 RSS Feed...
    "%PYTHON_CMD%" "%SCRIPT_DIR%generate_feed.py"
    if errorlevel 1 (
        echo [错误] RSS Feed 生成失败
    ) else (
        echo [%TIMESTAMP%] RSS Feed 生成完成
    )
    echo.

    echo [%TIMESTAMP%] 第5步：生成 Sitemap...
    "%PYTHON_CMD%" "%SCRIPT_DIR%generate_sitemap.py"
    if errorlevel 1 (
        echo [错误] Sitemap 生成失败
    ) else (
        echo [%TIMESTAMP%] Sitemap 生成完成
    )
    echo.
)

REM ── 第6步：构建网站 ──
if "%DO_BUILD%"=="1" if not defined DRY_RUN (
    echo [%TIMESTAMP%] 第6步：构建 VitePress 网站...

    if not exist "node_modules" (
        echo [%TIMESTAMP%] 安装 Node.js 依赖...
        call npm install
    )

    call npm run build
    if errorlevel 1 (
        echo [错误] 网站构建失败
    ) else (
        echo [%TIMESTAMP%] 网站构建完成！输出目录: docs\.vitepress\dist\
    )
    echo.
)

REM ── 仅生成 RSS ──
if "%DO_FEED%"=="1" if "%DO_FETCH%"=="0" (
    echo [%TIMESTAMP%] 生成 RSS Feed...
    "%PYTHON_CMD%" "%SCRIPT_DIR%generate_feed.py"
    if errorlevel 1 (
        echo [错误] RSS Feed 生成失败
    ) else (
        echo [%TIMESTAMP%] RSS Feed 生成完成
    )
    echo.
)

echo ===========================================================
echo [%TIMESTAMP%] 全部完成！
echo ===========================================================
endlocal
