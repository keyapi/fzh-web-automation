# Skill 2：通途库存导入自动化 — 基本用法

> 适用：每天从通途 ERP 导出库存结存，生成可直接导入的 Excel 文件。
> 前提：已完成 Skill 1（Playwright MCP 已部署）。

---

## 首次使用（只需做一次）

### 1. 安装 uv（Python 包管理器）

按 `Win+R`，输入 `cmd`，粘贴：
```cmd
winget install --id=astral.uv -e
```

### 2. 进入项目目录，装依赖

```cmd
cd C:\Users\你的用户名\通途库存Excel
uv sync
uv run playwright install chromium
```

### 3. 首次运行——手动登录一次

```cmd
uv run python tongtu_auto_export.py
```

- 浏览器自动弹出，打开通途库存结存页面
- **手动登录**：输入用户名、密码、图形验证码，勾选"remember"
- 之后脚本全自动执行：选仓库 → 导出 → 下载 → 生成导入文件
- 登录 cookies 保存在 `chrome-profile/` 目录，下次免登录

---

## 日常使用（每天只需一行命令）

```cmd
cd C:\Users\你的用户名\通途库存Excel
uv run python tongtu_auto_export.py
```

浏览器弹出 → 自动检测已登录 → 一键完成所有操作，无需任何人工介入。

---

## 什么时候需要重新登录

以下情况需要加 `--fresh` 重新登录：
- 通途登录会话过期（通常数天到数周）
- 脚本提示"未检测到有效会话，请手动登录"

```cmd
uv run python tongtu_auto_export.py --fresh
```

---

## 如何用对话方式操控浏览器（无需写代码）

如果你部署了 Playwright MCP，以后可以直接在 Claude Desktop 对话中说：

> 用 Playwright MCP 打开通途库存结存页面，依次导出 6 个仓库

Claude 会自己打开浏览器、切换仓库、点击导出、下载文件。

**注意**：MCP 模式下下载的文件在 `.playwright-mcp/` 目录，之后需要运行：
```cmd
uv run python mcp_to_output.py --auto
```
这个脚本会自动将下载的文件整理到 `downloads/` 和 `output/` 目录。

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `tongtu_auto_export.py` | 全自动脚本（命令行执行，推荐日常使用） |
| `generate_tongtu_import.py` | 把导出的 Excel 转成导入格式 |
| `mcp_to_output.py` | MCP 模式桥接：整理 MCP 下载文件 → downloads/ + output/ |
| `chrome-profile/` | 浏览器登录会话（自动创建，不要手动删） |
| `inspect_warehouse.py` | 诊断工具（页面改版时 dump DOM 用） |
| `downloads/` | 原始库存清单 XLSX（按仓库重命名） |
| `output/` | 生成的导入文件 XLSX（按仓库重命名） |

---

## 常见问题

| 问题 | 解决 |
|------|------|
| `uv` 命令找不到 | 重新运行 `winget install --id=astral.uv -e`，或重启命令行窗口 |
| 浏览器弹出后白屏 | 通途服务器响应慢，等 30 秒 |
| 导出按钮点击没反应 | 通途页面可能改版。运行 `uv run python inspect_warehouse.py` 诊断，然后把输出的 JSON 发给技术支持 |
| 生成的文件里安全库存有 0 | 确认使用的是项目最新版脚本，已修复为留空（None） |
| MCP 模式下载的文件在哪 | 在主仓库 `.playwright-mcp/` 目录，运行 `mcp_to_output.py` 整理 |
| MCP 模式提示未登录 | Chrome cookie 注入可能有延迟，等 5 秒后刷新页面。如果仍不行，用 `uv run python tongtu_auto_export.py --export-cookies` 重新提取 cookie |
