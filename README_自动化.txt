============================
通途库存导出全自动化
============================

环境管理用 uv，比 pip 快一个数量级：
  https://docs.astral.sh/uv/getting-started/installation/

------ 首次使用 ------

  1. 安装 uv（选一种方式）：
     - winget install --id=astral.uv -e
     - 或 https://docs.astral.sh/uv/getting-started/installation/

  2. 进入这个目录，创建虚拟环境 + 装依赖（一行搞定）：
     uv sync

  3. 安装 Playwright 浏览器：
     uv run playwright install chromium

  4. 运行（首次需手动登录通途，后续免登录）：
     uv run python tongtu_auto_export.py

------ 日常使用 ------

  双击 一键运行.cmd
  或者：
  uv run python tongtu_auto_export.py

  首次运行：浏览器弹出 → 手动登录（输入用户名、密码、验证码）
                    → 脚本自动选仓库、导出、生成导入文件
                    → 登录会话保存到 chrome-profile/ 目录

  后续运行：浏览器弹出 → 自动检测到已登录 → 全程零人工！

  如需重新登录（会话过期等原因）：
  uv run python tongtu_auto_export.py --fresh

------ MCP 对话模式 ------

  如果部署了 Playwright MCP（见 SKILL_deploy_playwright_mcp.md），
  也可以在 Claude Desktop 对话中直接操控浏览器导出。

  MCP 下载的文件保存在 .playwright-mcp/ 目录，
  用桥接脚本整理并生成导入文件：
  uv run python mcp_to_output.py --auto

------ 调试 ------

  导出按钮定位变化时，用诊断脚本 dump 页面元素：
  uv run python inspect_warehouse.py
