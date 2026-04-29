# Skill 1：在新 Windows 电脑上部署 Playwright MCP

> 适用：给新电脑安装 Claude Desktop + Playwright MCP，让 Claude 能操控浏览器。
> 难度：无需 IT 背景，复制粘贴命令即可。

---

## 前置条件

- Windows 10 或 11
- 已安装 Claude Desktop（Microsoft Store 版）
- 本项目文件夹已拷贝到本机（例如 `C:\Users\xxx\通途库存Excel\`）

---

## 第一步：安装 Node.js

Playwright MCP 需要 Node.js 运行。

1. 打开浏览器访问 https://nodejs.org
2. 下载 **LTS 版本**（左边绿色按钮），例如 `node-v22.x.x-x64.msi`
3. 双击安装，一路点 Next，全部默认设置即可
4. 验证：按 `Win+R`，输入 `cmd`，回车，在黑色窗口里输入：
   ```
   node --version
   ```
   看到 `v22.x.x` 即成功。

---

## 第二步：修改 Claude Desktop 配置

> ⚠️ **关键**：Microsoft Store 版的配置路径是特殊路径，不要弄错。

1. 按 `Win+R`，输入以下路径，回车：
   ```
   %APPDATA%\..\Local\Packages
   ```
2. 找到名字以 `Claude_` 开头的文件夹（例如 `Claude_pzs8sxrjxfjjc`），双击进入
3. 依次进入 `LocalCache` → `Roaming` → `Claude-3p`
4. 右键点击 `claude_desktop_config.json`，选"打开方式" → "记事本"

5. 把文件内容改成这样（如果已有其他内容，只加 `mcpServers` 那一段）：
   ```json
   {
     "deploymentMode": "3p",
     "preferences": {
       "coworkWebSearchEnabled": true
     },
     "mcpServers": {
       "playwright": {
         "command": "npx",
         "args": ["@playwright/mcp@latest"]
       }
     }
   }
   ```
   
   > 如果文件里已经有 `coworkScheduledTasksEnabled`、`ccdScheduledTasksEnabled`、`sidebarMode` 等字段，保留它们不动，只加 `mcpServers` 部分即可。

6. 保存文件（Ctrl+S），关闭记事本。

---

## 第三步：彻底重启 Claude Desktop

> ⚠️ **最容易踩的坑**：只关窗口不够！

1. 关闭 Claude Desktop 窗口
2. 看 Windows 任务栏右下角（系统托盘），找到 Claude 图标
3. **右键图标 → Quit**（彻底退出）
4. 重新打开 Claude Desktop
5. 进入 **Settings → Developer**，确认看到：
   ```
   Local MCP servers
   playwright    ✓    npx @playwright/mcp@latest
   ```

---

## 第四步：验证

在 Claude Desktop 对话中输入：

> 用 Playwright 打开 https://www.baidu.com，截图给我看

如果能打开浏览器并截图返回，说明部署成功。

---

## 常见问题

| 问题 | 解决 |
|------|------|
| Settings → Developer 显示 "No servers added" | 配置未生效。检查：① JSON 格式是否正确（不能有多余逗号）② 是否彻底 Quit 了系统托盘 ③ 路径是否在 `Claude-3p` 文件夹下 |
| `npx` 命令找不到 | Node.js 没装或没加到 PATH。重新安装 Node.js LTS 版，安装时勾选 "Add to PATH" |
| Claude Desktop 启动报错 | JSON 格式有误。用 https://jsonlint.com 验证你的配置文件 |
| 浏览器能打开但白屏 | 首次使用需要下载 Chromium，稍等 1-2 分钟再试 |
| Claude Code 中 MCP 工具不可用 | 如果 MCP 在当前 session 开始后才激活，Claude Code 可能无法热加载。需要**新建对话**（新 session）才能使用 MCP 工具 |
| 通途登录页无法自动登录 | 需先用项目脚本 `uv run python tongtu_auto_export.py --export-cookies` 导出 cookie，再在 MCP session 中用 `browser_run_code` + `addCookies()` 注入 |
| 通途页面 cookie 注入后仍跳转登录页 | session cookie (JSESSIONID) 无法持久化，但记住密码 cookie 可触发自动登录。注入后等待 3-5 秒，再导航到 `erp102.tongtool.com/.../goodsbalance/...` |
