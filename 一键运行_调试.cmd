@echo off
chcp 65001 >nul
title 通途库存导入自动生成

echo ========================================
echo  通途库存导入 — 一键生成（调试版）
echo ========================================
echo.

:: 显示当前路径
echo [信息] 当前路径: %cd%
echo.

:: 检查 uv 是否安装
echo [检查] 检测 uv...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [失败] uv 未安装！
    echo.
    echo 请手动安装 uv：
    echo 打开 PowerShell，粘贴运行以下命令：
    echo   powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 ^| iex"
    echo.
    pause
    exit /b 1
)
echo [OK] uv 已安装
echo.

:: 安装依赖
echo [第二步] 安装依赖...
uv sync
if %errorlevel% neq 0 (
    echo [失败] uv sync 失败，尝试备用方案...
    uv venv
    call .venv\Scripts\activate
    uv pip install pandas openpyxl playwright requests requests-toolbelt
)
echo.

:: 安装 Chromium
echo [第三步] 安装 Chromium 浏览器...
uv run playwright install chromium
if %errorlevel% neq 0 (
    echo [警告] Chromium 安装可能失败，尝试继续...
)
echo.

:: 运行
echo [第四步] 启动浏览器自动化...
echo ========================================
echo.
uv run python tongtu_auto_export.py
set EXITCODE=%errorlevel%
echo.
echo ========================================
if %EXITCODE% equ 0 (
    echo [完成] 运行成功！
) else (
    echo [失败] 运行出错，退出码: %EXITCODE%
    echo 请截图上面的错误信息发给我
)
echo ========================================
pause
