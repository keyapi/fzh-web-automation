---
name: playwright-setup
description: >
  为新机器安装自动化环境：Node.js + uv + Playwright MCP + Chrome。
  当用户提到"设置自动化环境"、"安装自动化工具"、"Setup"、"环境安装"、
  "装 Playwright"、"配置 MCP"、"MCP 部署"、"首次使用"、"帮我装环境"等时触发。
  不要用于具体的通途或赛狐操作 — 那些用 tongtu-automation / sellfox-automation skill。
compatibility: >
  需要 Claude Desktop 或 Codex CLI。Windows/Mac 均可。
  依赖 Node.js LTS, uv, Playwright MCP (@playwright/mcp@latest)。
metadata:
  module: playwright-setup
  updated: 2026-06-30
---

# 自动化环境一键启动

## 一句话触发（给同事）

在 Claude Code 中说：

| 你想做什么 | 就说 |
|-----------|------|
| 新电脑装环境 | "**帮我设置自动化环境**" |
| 检查环境 | "**检查我的自动化环境**" |
| MCP 不工作 | "**Playwright MCP 连不上**" |

## Hard Constraints

- **只装必需工具**：Node.js + uv + Playwright MCP。不装 IDE、不装重型工具
- **用 uv 隔离**：不同项目互不干扰
- **操作通过对话完成**：用户只需复制粘贴命令
- **禁止**让用户手动编辑注册表、环境变量
- **禁止**让用户安装 Visual Studio Build Tools、Anaconda

## 安装流程

### 第一步：检测环境

1. 确认操作系统（Windows / Mac）
2. `node --version` — 检测 Node.js
3. `uv --version` — 检测 uv

### 第二步：安装 Node.js（如未安装）

```bash
# Windows
winget install OpenJS.NodeJS.LTS

# Mac
brew install node
```

验证：`node --version`（v22.x 或 v20.x）

### 第三步：安装 uv（如未安装）

```bash
# Windows
winget install --id=astral.uv -e
# 装完后重启命令行窗口

# Mac
curl -LsSf https://astral.sh/uv/install.sh | sh
```

验证：`uv --version`

### 第四步：安装 Playwright MCP

```bash
npm install -g @playwright/mcp
npx playwright install chromium
```

### 第五步：配置 Claude Desktop

**Windows（Microsoft Store 版）配置文件路径**：
```
%APPDATA%\..\Local\Packages\Claude_xxx\LocalCache\Roaming\Claude-3p\claude_desktop_config.json
```

在配置文件中加入：
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

> 如果文件已有其他字段，保留它们，只加 `mcpServers` 部分。

**彻底重启 Claude Desktop**：系统托盘 → 右键 Claude 图标 → Quit → 重新打开。

### 第六步：验证

在 Claude Desktop 对话中输入：*"用 Playwright 打开 https://www.baidu.com，截图给我看"*

## 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| "No servers added" | 配置未生效 | 确认彻底 Quit（系统托盘！），重启 |
| `npx` 找不到 | Node.js 未安装/未加 PATH | 重装 Node.js LTS，勾选 "Add to PATH" |
| MCP 工具不可用 | 当前 session 热加载限制 | **新建对话** |
| `uv` 找不到 | 安装后未刷新 PATH | 重启命令行窗口 |
| 浏览器白屏 | 首次下载 Chromium | 等 1-2 分钟再试 |
| winget 找不到 | Windows 太旧 | 从官网手动下载安装包 |

## 参考

- [MCP 部署详解](references/playwright-mcp-detail.md)
