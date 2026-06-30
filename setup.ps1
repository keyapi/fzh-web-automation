# setup.ps1 — fzh-web-automation 首次 setup 脚本
# 创建 CLAUDE.md → AGENTS.md 符号链接 (需要管理员权限或开发者模式)

$ErrorActionPreference = "Stop"

Write-Host "Setting up fzh-web-automation..." -ForegroundColor Cyan

# 创建 CLAUDE.md symlink
if (Test-Path "CLAUDE.md") {
    Remove-Item "CLAUDE.md" -Force
}
New-Item -ItemType SymbolicLink -Path "CLAUDE.md" -Target "AGENTS.md" -Force
Write-Host "CLAUDE.md → AGENTS.md symlink created" -ForegroundColor Green

Write-Host "Setup complete." -ForegroundColor Cyan
