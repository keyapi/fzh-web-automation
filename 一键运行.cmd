@echo off
chcp 65001 >nul
title 通途库存导入自动生成

echo ========================================
echo  通途库存导入 — 一键生成
echo ========================================
echo.

:: 检查 uv 是否安装
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [第一步] 安装 uv...
    powershell -c "winget install --id=astral.uv -e" 2>nul
    :: 备用方案
    if %errorlevel% neq 0 (
        echo 请手动安装 uv: https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b
    )
)

:: 创建虚拟环境并安装依赖
echo [第二步] 创建虚拟环境并安装依赖...
uv sync 2>nul || uv pip install -r requirements.txt 2>nul || (
    uv venv
    call .venv\Scripts\activate
    uv pip install pandas openpyxl playwright
    playwright install chromium
)

:: 运行自动化脚本
echo [第三步] 启动浏览器自动化...
uv run tongtu_auto_export.py

echo.
echo 完成！
pause
