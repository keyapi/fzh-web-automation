# 通途库存自动化 — 启动包

> 给同事的：把这个文件夹拷贝到你的电脑，打开 Claude Desktop（Code 模式），然后对 Claude 说：
> **"帮我设置自动化环境"** 即可开始。

---

## 你需要什么

- Claude Desktop 已安装（第三方/deployment 模式）
- 一台能上网的电脑（Windows 10+ 或 Mac）
- 不需要会编程

---

## 三种用法

### 1. 通途库存导出（和我一样的需求）

对 Claude 说：

> 帮我导出通途库存结存的所有 6 个仓库，并生成导入文件

Claude 会自动打开浏览器、切换仓库、下载文件、生成导入 Excel。

### 2. 通途其他页面自动化

对 Claude 说：

> 帮我打开通途的 XX 页面，自动做 YY 操作

### 3. 其他网站的自动化

对 Claude 说：

> 帮我自动化 https://xxx.com 的 XX 操作

---

## 文件夹说明

| 文件 | 给谁看的 | 用途 |
|------|---------|------|
| `SKILL_quick_start.md` | Claude | 环境安装步骤（uv + Node.js + MCP） |
| `SKILL_web_automation.md` | Claude | 浏览器自动化通用模式（选择器、登录、下载） |
| `SKILL_deploy_playwright_mcp.md` | Claude | MCP 部署的详细踩坑指南 |
| `SKILL_tongtu_automation.md` | Claude | 通途专项自动化说明 |
| `tongtu_auto_export.py` | Claude | 通途全自动导出脚本（Python） |
| `mcp_to_output.py` | Claude | MCP 下载文件整理脚本 |
| `generate_tongtu_import.py` | Claude | SKU 数据转换脚本 |
| `一键运行.cmd` | 人 | Windows 一键运行 |

---

## 首次使用步骤

1. 把这个文件夹拷贝到你的电脑（比如桌面或文档目录）
2. 打开 Claude Desktop
3. 切换到 **Code 模式**（左下角或设置里）
4. 用 Claude Desktop 打开这个文件夹
5. 对 Claude 说：**"帮我设置自动化环境"**

Claude 会根据你的操作系统（Windows/Mac）自动：
- 安装 Node.js（如果没装）
- 安装 uv（Python 包管理器）
- 配置 Playwright MCP
- 验证一切正常

环境就绪后，你就可以用对话操控浏览器了。

---

## 如果需要帮助

对 Claude 说：

> 我遇到了 XX 问题，帮我排查

Claude 会读取 skill 文件中的踩坑记录来帮你。
