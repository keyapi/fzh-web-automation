# 通途库存自动化 — 给同事的启动包

> 把这个文件夹拷贝到你的电脑，打开 Claude Desktop（Code 模式），然后对 Claude 说：
> **"帮我设置自动化环境"** 即可开始。

## 你需要什么

- Claude Desktop 已安装（第三方/deployment 模式）
- 一台能上网的电脑（Windows 10+ 或 Mac）
- 不需要会编程

## 三种用法

### 1. 通途库存导出

对 Claude 说：

> 帮我导出通途库存结存的所有 6 个仓库，并生成导入文件

Claude 会自动打开浏览器、切换仓库、下载文件、生成导入 Excel。

### 2. 通途其他页面

对 Claude 说：

> 帮我打开通途的 XX 页面，自动做 YY 操作

### 3. 赛狐操作

对 Claude 说：

> 赛狐导出库存 / 赛狐搜索 SKU KS0001

## 首次使用步骤

1. 把这个文件夹拷贝到你的电脑
2. 打开 Claude Desktop，切换到 **Code 模式**
3. 用 Claude Desktop 打开这个文件夹
4. 对 Claude 说：**"帮我设置自动化环境"**

Claude 会自动安装 Node.js + uv + Playwright MCP，并验证一切正常。

## 如果需要帮助

对 Claude 说：

> 我遇到了 XX 问题，帮我排查

Claude 会读取 skill 文件中的踩坑记录来帮你。

## 项目详情

- [README.md](README.md) — 项目简介（人读）
- [AGENTS.md](AGENTS.md) — Agent 指令源 + 行为规则
- [.agents/skills/](.agents/skills/) — 自动化技能（Agent 自动加载）
