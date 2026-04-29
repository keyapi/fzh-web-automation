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
     或手动：uv venv && uv pip install pandas openpyxl playwright
            && playwright install chromium

  3. 关掉所有 Chrome 窗口，重新用调试端口启动：
     chrome.exe --remote-debugging-port=9222

  4. 在打开的 Chrome 中登录通途

  5. 运行（加了 uv run 会自动激活虚拟环境）：
     uv run tongtu_auto_export.py

------ 日常使用 ------

  双击 一键运行.cmd
  或者：
  1. chrome.exe --remote-debugging-port=9222
  2. uv run tongtu_auto_export.py

------ 调试选择器 ------

  如果导出按钮点不到，用 Playwright 的录制功能：
  uv run playwright codegen https://你的通途地址
  手动点一遍导出流程，codegen 会自动生成 Python 代码，
  把里面定位到按钮的那行复制替换到 tongtu_auto_export.py 里。
