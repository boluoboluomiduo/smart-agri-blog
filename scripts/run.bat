@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "LOG_FILE=%SCRIPT_DIR%run.log"

set "PYTHON_CMD="
set "PYTHON_ARGS="
where py >nul 2>&1 && (set "PYTHON_CMD=py" & set "PYTHON_ARGS=-3")
if not defined PYTHON_CMD where python >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD where python3 >nul 2>&1 && set "PYTHON_CMD=python3"
if not defined PYTHON_CMD (
    echo [ERROR] Python not found
    exit /b 1
)

for /f "delims=" %%v in ('%PYTHON_CMD% %PYTHON_ARGS% --version 2^>^&1') do set "PY_VER=%%v"

set "DO_FETCH=1"
set "DO_BUILD=1"
set "DO_FEED=1"
set "DRY_RUN="

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

for /f "tokens=1-4 delims=/ " %%a in ('date /t') do set "DATE=%%a-%%b-%%c"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "TIME=%%a:%%b"
set "TIMESTAMP=%DATE% %TIME%"

echo ===========================================================
echo [%TIMESTAMP%] Smart Agri Blog - Starting
echo [INFO] Python: %PY_VER%
echo ===========================================================
echo.

if "%DO_FETCH%"=="1" (
    echo [%TIMESTAMP%] Step 1: Fetching news...
    %PYTHON_CMD% %PYTHON_ARGS% "%SCRIPT_DIR%fetch_news.py" %DRY_RUN%
    if errorlevel 1 (
        echo [ERROR] News fetch failed
    ) else (
        echo [%TIMESTAMP%] News fetch complete
    )
    echo.

    echo [%TIMESTAMP%] Step 2: Updating sidebar...
    %PYTHON_CMD% %PYTHON_ARGS% "%SCRIPT_DIR%update_sidebar.py"
    if errorlevel 1 (
        echo [ERROR] Sidebar update failed
    ) else (
        echo [%TIMESTAMP%] Sidebar update complete
    )
    echo.

    echo [%TIMESTAMP%] Step 3: Generating article data...
    %PYTHON_CMD% %PYTHON_ARGS% "%SCRIPT_DIR%generate_articles_json.py"
    if errorlevel 1 (
        echo [ERROR] Article data generation failed
    ) else (
        echo [%TIMESTAMP%] Article data generation complete
    )
    echo.

    echo [%TIMESTAMP%] Step 4: Generating RSS Feed...
    %PYTHON_CMD% %PYTHON_ARGS% "%SCRIPT_DIR%generate_feed.py"
    if errorlevel 1 (
        echo [ERROR] RSS Feed generation failed
    ) else (
        echo [%TIMESTAMP%] RSS Feed generation complete
    )
    echo.

    echo [%TIMESTAMP%] Step 5: Generating Sitemap...
    %PYTHON_CMD% %PYTHON_ARGS% "%SCRIPT_DIR%generate_sitemap.py"
    if errorlevel 1 (
        echo [ERROR] Sitemap generation failed
    ) else (
        echo [%TIMESTAMP%] Sitemap generation complete
    )
    echo.
)

if "%DO_BUILD%"=="1" if not defined DRY_RUN (
    echo [%TIMESTAMP%] Step 6: Building VitePress site...

    if not exist "node_modules" (
        echo [%TIMESTAMP%] Installing Node.js dependencies...
        call npm install
    )

    call npm run build
    if errorlevel 1 (
        echo [ERROR] Site build failed
    ) else (
        echo [%TIMESTAMP%] Site build complete! Output: docs\.vitepress\dist\
    )
    echo.
)

if "%DO_FEED%"=="1" if "%DO_FETCH%"=="0" (
    echo [%TIMESTAMP%] Generating RSS Feed...
    %PYTHON_CMD% %PYTHON_ARGS% "%SCRIPT_DIR%generate_feed.py"
    if errorlevel 1 (
        echo [ERROR] RSS Feed generation failed
    ) else (
        echo [%TIMESTAMP%] RSS Feed generation complete
    )
    echo.
)

echo ===========================================================
echo [%TIMESTAMP%] All done!
echo ===========================================================
endlocal
