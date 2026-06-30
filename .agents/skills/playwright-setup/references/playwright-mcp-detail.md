---
okf: v0.1
type: Reference
title: Playwright MCP 部署详解
description: 从 SKILL_deploy_playwright_mcp.md 迁移的详细部署指南
tags: [playwright, mcp, deployment, troubleshooting]
timestamp: 2026-06-30
---

# 部署 Playwright MCP（详细版）

> 这是 playwright-setup skill 第四/五步的详细补充。

## 前置条件

- Windows 10/11 或 Mac
- 已安装 Claude Desktop 或 Codex CLI
- 项目文件夹已拷贝到本机

## 配置文件路径

### Windows（Microsoft Store 版）

1. `Win+R` → 输入 `%APPDATA%\..\Local\Packages` → 回车
2. 找到 `Claude_` 开头的文件夹（如 `Claude_pzs8sxrjxfjjc`）
3. 进入 `LocalCache\Roaming\Claude-3p\`
4. 找到 `claude_desktop_config.json`

### Mac

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## 配置文件内容

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

**关键规则**：
- 如果文件已有其他字段（如 `preferences`），保留它们，只加 `mcpServers` 部分
- JSON 最后一项后面**不能有逗号**
- 保存后用 https://jsonlint.com 验证格式

## 验证部署

进入 Settings → Developer，确认看到：
```
playwright    ✓    npx @playwright/mcp@latest
```

## 详细排查

| 问题 | 解决 |
|------|------|
| "No servers added" | 检查 JSON 格式、确认彻底 Quit（系统托盘）、确认路径在 Claude-3p 下 |
| `npx` 找不到 | 重装 Node.js LTS，勾选 "Add to PATH" |
| 启动报错 | JSON 格式有误，用 jsonlint.com 验证 |
| 浏览器白屏 | 首次需下载 Chromium，等 1-2 分钟 |
| MCP 工具不可用 | 新建对话（非热加载） |
| 通途登录页无法自动登录 | 先用 `uv run python tongtu_auto_export.py --export-cookies` 导出 cookie |
| cookie 注入后仍跳转登录页 | JSESSIONID 不可持久化，依赖记住密码 cookie 触发自动登录，注入后等 3-5 秒 |
