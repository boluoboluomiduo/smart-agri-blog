#Requires -Version 5.1
# ============================================================
# Smart Agri Blog - PowerShell Update Script
#
# Usage:
#   .\run.ps1              Full pipeline: fetch + build
#   .\run.ps1 -Fetch       Fetch only, no build
#   .\run.ps1 -Build       Build only, no fetch
#   .\run.ps1 -Feed        Generate RSS feed only
#   .\run.ps1 -Sitemap     Generate Sitemap only
#   .\run.ps1 -DryRun      Preview mode
#   .\run.ps1 -Concurrent  Enable concurrent fetching
#   .\run.ps1 -Workers 5   Set concurrent worker count
# ============================================================

[CmdletBinding()]
param(
    [switch]$Fetch,
    [switch]$Build,
    [switch]$Feed,
    [switch]$Sitemap,
    [switch]$DryRun,
    [switch]$Concurrent,
    [int]$Workers = 0
)

$ErrorActionPreference = "Continue"
$ScriptDir = $PSScriptRoot
$ProjectDir = Split-Path $ScriptDir -Parent
$LogFile = Join-Path $ScriptDir "run.log"

function Write-Log($Message, $Level = "Info") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "Error"   { "Red" }
        "Warning" { "Yellow" }
        "Success" { "Green" }
        default   { "White" }
    }
    $logEntry = "[$timestamp] $Message"
    Write-Host $logEntry -ForegroundColor $color
    Add-Content -Path $LogFile -Value $logEntry -Encoding UTF8
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python", "")
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        return @("python3", "")
    }
    return $null
}

$PythonCmd = Get-PythonCommand
if (-not $PythonCmd) {
    Write-Log "[ERROR] Python not found. Please install Python from https://www.python.org/downloads/" "Error"
    exit 1
}

$PythonExe = $PythonCmd[0]
$PythonArgs = $PythonCmd[1]

function Invoke-PythonScript($ScriptName, $ExtraArgs = @()) {
    $scriptPath = Join-Path $ScriptDir $ScriptName
    $allArgs = @($PythonArgs) + $ExtraArgs + @("`"$scriptPath`"")
    
    try {
        $output = & $PythonExe @allArgs 2>&1
        $output | ForEach-Object { Write-Host $_ }
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        return $true
    } catch {
        Write-Log "Failed to execute $ScriptName`: $_" "Error"
        return $false
    }
}

Set-Location $ProjectDir

Write-Log "===== Smart Agri Blog - Starting =====" "Success"
Write-Log "Python: $PythonExe $PythonArgs"

$DoFetch = -not ($Build -or $Feed -or $Sitemap)
$DoBuild = -not ($Fetch -or $Feed -or $Sitemap)
$DoFeedOnly = $Feed
$DoSitemapOnly = $Sitemap

if ($DoFetch) {
    Write-Log "Step 1: Fetching news..."
    
    $fetchArgs = @()
    if ($DryRun) { $fetchArgs += "--dry-run" }
    if ($Concurrent) { $fetchArgs += "--concurrent" }
    if ($Workers -gt 0) { $fetchArgs += "--workers"; $fetchArgs += $Workers.ToString() }
    
    if (Invoke-PythonScript "fetch_news.py" $fetchArgs) {
        Write-Log "News fetch complete" "Success"
    } else {
        Write-Log "News fetch failed" "Error"
    }
    Write-Log ""

    Write-Log "Step 2: Updating sidebar..."
    if (Invoke-PythonScript "update_sidebar.py") {
        Write-Log "Sidebar update complete" "Success"
    } else {
        Write-Log "Sidebar update failed" "Error"
    }
    Write-Log ""

    Write-Log "Step 3: Generating article data..."
    if (Invoke-PythonScript "generate_articles_json.py") {
        Write-Log "Article data generation complete" "Success"
    } else {
        Write-Log "Article data generation failed" "Error"
    }
    Write-Log ""

    Write-Log "Step 4: Generating RSS Feed..."
    if (Invoke-PythonScript "generate_feed.py") {
        Write-Log "RSS Feed generation complete" "Success"
    } else {
        Write-Log "RSS Feed generation failed" "Error"
    }
    Write-Log ""

    Write-Log "Step 5: Generating Sitemap..."
    if (Invoke-PythonScript "generate_sitemap.py") {
        Write-Log "Sitemap generation complete" "Success"
    } else {
        Write-Log "Sitemap generation failed" "Error"
    }
    Write-Log ""
}

if ($DoBuild -and -not $DryRun) {
    Write-Log "Step 6: Building VitePress site..."
    
    if (-not (Test-Path "node_modules")) {
        Write-Log "Installing Node.js dependencies..."
        try {
            npm install 2>&1 | ForEach-Object { Write-Host $_ }
            Write-Log "Dependencies installed" "Success"
        } catch {
            Write-Log "Dependency installation failed: $_" "Error"
        }
    }

    try {
        npm run build 2>&1 | ForEach-Object { Write-Host $_ }
        Write-Log "Site build complete! Output: docs\.vitepress\dist\" "Success"
    } catch {
        Write-Log "Site build failed: $_" "Error"
    }
    Write-Log ""
}

if ($DoFeedOnly) {
    Write-Log "Generating RSS Feed..."
    if (Invoke-PythonScript "generate_feed.py") {
        Write-Log "RSS Feed generation complete" "Success"
    } else {
        Write-Log "RSS Feed generation failed" "Error"
    }
    Write-Log ""
}

if ($DoSitemapOnly) {
    Write-Log "Generating Sitemap..."
    if (Invoke-PythonScript "generate_sitemap.py") {
        Write-Log "Sitemap generation complete" "Success"
    } else {
        Write-Log "Sitemap generation failed" "Error"
    }
    Write-Log ""
}

Write-Log "===== All done! =====" "Success"
