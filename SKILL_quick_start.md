# Skill: 自动化环境一键启动

> **给 Claude 看的**：当用户说"帮我设置自动化环境"、"安装自动化工具"、"Setup"等，按此文档操作。
> **适用人群**：零编程背景的 Windows/Mac 用户。
> **适用范围**：任意网站浏览器自动化（不限于通途）。

---

## 你的任务

帮助用户在本机安装最少的必要工具，让 Claude Desktop（Code 模式）能通过 Playwright MCP 操控浏览器。

**核心原则**：
- 只装必需的工具，不装 IDE、不装一堆库
- 用 uv 隔离 Python 环境（不同项目互不干扰）
- 所有操作通过对话完成，用户只需复制粘贴命令

---

## 第一步：检测当前环境

先确认用户的操作系统和已安装的工具：

1. 问用户是什么操作系统（Windows / Mac）
2. 检查 Node.js：让用户运行 `node --version`
3. 检查 uv：让用户运行 `uv --version`

根据结果决定后续步骤。

---

## 第二步：安装 Node.js（如未安装）

Playwright MCP 需要 Node.js 运行。

### Windows
```
winget install OpenJS.NodeJS.LTS
```
如果没有 winget，让用户访问 https://nodejs.org 下载 LTS 版本安装。

### Mac
```
brew install node
```
如果没有 brew，让用户访问 https://nodejs.org 下载 LTS 版本安装。

验证：`node --version`（应显示 v22.x 或 v20.x）

---

## 第三步：安装 uv（Python 包管理器）

uv 比 pip 快 10-100 倍，自动管理虚拟环境，项目间互不干扰。

### Windows
```cmd
winget install --id=astral.uv -e
```
装完后**关闭并重新打开**命令行窗口（或重启 Claude Desktop）。

### Mac
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
然后运行 `source ~/.zshrc` 或重启终端。

验证：`uv --version`

---

## 第四步：配置 Playwright MCP

> ⚠️ 这一步是**最容易踩坑**的地方。请严格按顺序操作。

### 4.1 找到 Claude Desktop 配置文件

- **Windows（Microsoft Store 版）**：
  1. `Win+R` → 输入 `%APPDATA%\..\Local\Packages` → 回车
  2. 找到 `Claude_` 开头的文件夹（如 `Claude_pzs8sxrjxfjjc`）
  3. 进入 `LocalCache\Roaming\Claude-3p\`
  4. 找到 `claude_desktop_config.json`

- **Mac**：
  ```
  ~/Library/Application Support/Claude/claude_desktop_config.json
  ```

### 4.2 修改配置文件

用记事本（Windows）或文本编辑（Mac）打开，确保包含以下内容：

```json
{
  "deploymentMode": "3p",
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

**关键规则**：
- 如果文件已有其他字段（如 `preferences`、`coworkWebSearchEnabled` 等），**保留它们**，只加 `mcpServers` 部分
- JSON 最后一项后面**不能有逗号**
- 保存后用 https://jsonlint.com 验证格式

### 4.3 彻底重启 Claude Desktop

> ⚠️ **最常见的失败原因**：只关窗口不够！

1. 关闭所有 Claude Desktop 窗口
2. **Windows**：右下角系统托盘 → 右键 Claude 图标 → **Quit**
3. **Mac**：菜单栏 Claude → **Quit Claude**
4. 重新打开 Claude Desktop
5. 进入 Settings → Developer，确认看到 `playwright ✓`

---

## 第五步：验证

在 Claude Desktop 对话中输入：

> 用 Playwright 打开 https://www.baidu.com，截图给我看

如果能看到截图，说明环境就绪。

---

## 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| Settings 显示 "No servers added" | 配置未生效 | 确认彻底 Quit（系统托盘！），重启 |
| `npx` 命令找不到 | Node.js 未安装或 PATH 问题 | 重装 Node.js LTS，确认安装时勾选 "Add to PATH" |
| MCP 工具在对话中不可用 | MCP 在当前 session 启动后才激活 | **新建对话**（新 session），MCP 只在 session 开始时加载 |
| `uv` 命令找不到 | 安装后未刷新 PATH | 关掉命令行窗口重新打开 |
| 浏览器白屏 | 首次需下载 Chromium | 等 1-2 分钟再试 |
| winget 找不到 | Windows 版本太旧 | 从 https://nodejs.org 和 https://github.com/astral-sh/uv 手动下载安装包 |

---

## 给 Claude 的提醒

- **禁止**让用户手动编辑注册表、环境变量等高级设置
- **禁止**让用户安装 Visual Studio Build Tools、Anaconda 等重型工具
- 如果某个安装步骤失败 3 次，换个方法而不是重复同样的命令
- Mac 用户可能没有管理员密码（公司电脑），优先用不需要 sudo 的方案
- 用户是零基础，用类比解释技术概念（"虚拟环境就像一个独立的工作间"）
