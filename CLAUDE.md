# CLAUDE.md — 通途库存自动化项目

## 业务背景

**通途 (Tongtu)** 是跨境电商 ERP 系统（erp102.tongtool.com），管理亚马逊/eBay/速卖通等平台订单、采购、仓储、财务。

本项目目标：从通途**库存结存**页面自动导出 6 个仓库的库存清单，提取 SKU / 头程运费 / 其他费用，生成可重新导入通途的标准 5 列 Excel（SKU、安全库存、头程报关费、头程运费、其他费用）。

导入目标仓：`FZH-DANEEY-皮壳仓库`。安全库存和头程报关费**必须留空 (None)**，填 0 会覆盖通途现有数据。

**用户**：跨境电商运营，非 IT 背景。账号：`zhangkeyong@vilavidress.com`。

## 仓库列表（按导出顺序）

| # | 仓库名 | SKU 数 (最近) |
|---|--------|--------------|
| 1 | CENTRADE | ~1,624 |
| 2 | FZHPoland-covers | ~1,359 |
| 3 | FZH-DANEEY-皮壳仓库 | ~896 |
| 4 | FZH-DANEEY-退货产品仓 | ~505 |
| 5 | FZH-DANEEY-成品仓 | ~241 |
| 6 | FZH-DANEEY-半成品仓 | ~146 |

## 文件结构

```
通途库存Excel/
├── tongtu_auto_export.py      # 主脚本：浏览器自动化导出 + 生成导入 + 合并
├── generate_tongtu_import.py  # 数据转换：库存清单 → 5列导入模板
├── merge_inventory.py         # 独立合并脚本：多仓原始清单 → 单文件
├── inspect_warehouse.py       # 诊断工具：dump 通途页面 DOM 元素
├── mcp_to_output.py           # MCP 桥接：整理 MCP 下载文件
├── pyproject.toml             # uv 项目配置 (pandas, openpyxl, playwright)
├── 一键运行.cmd               # Windows 双击运行
├── chrome-profile/            # 持久化浏览器会话 (gitignore)
├── downloads/                 # 原始库存清单 (gitignore)
├── output/                    # 导入文件 + 合并文件 (gitignore)
├── CLAUDE.md                  # 本文件
├── PROJECT.md                 # 详细项目文档
├── README_给同事.md           # 给同事的入口文档
├── README_自动化.txt          # 快速入门
├── SKILL_quick_start.md       # Skill: 通用环境安装
├── SKILL_web_automation.md    # Skill: 浏览器自动化通用模式
├── SKILL_deploy_playwright_mcp.md  # Skill: MCP 部署详解
└── SKILL_tongtu_automation.md     # Skill: 通途专项自动化
```

## 运行方式

### 日常使用（推荐）
```bash
uv run python tongtu_auto_export.py
```
自动完成：检测登录 → 6 仓库依次导出 → 生成导入文件 → 合并多仓清单。

### 强制重新登录
```bash
uv run python tongtu_auto_export.py --fresh
```

### 导出 cookies 供 MCP 使用
```bash
uv run python tongtu_auto_export.py --export-cookies
```

### MCP 对话模式（Claude Desktop Code 模式）
说：**"用 Playwright MCP 打开通途库存结存页面，依次导出 6 个仓库"**

MCP 下载文件在 `.playwright-mcp/`，之后运行 `uv run python mcp_to_output.py --auto` 整理。

## 关键技术决策

### 1. uv 环境隔离（非 pip）
uv 比 pip 快 10x，自动管理 venv。同事可能有不同 Python 项目的冲突依赖，uv 隔离开。`pyproject.toml` 声明依赖，`uv sync` 一键安装。

### 2. Playwright persistent_context（非 CDP attach）
**最终方案**：`chromium.launch_persistent_context(user_data_dir="chrome-profile/")`
- Playwright 自己管理 Chromium 实例
- cookies/localStorage 持久化到磁盘
- 首次手动登录，后续免登录
- **放弃的方案**：`chrome.exe --remote-debugging-port=9222` → CDP 端点不可达

### 3. Cookie 注入桥接（MCP ↔ Python）
MCP Playwright 使用独立浏览器实例，无法共享 chrome-profile。解决方案：
- Python 脚本 `--export-cookies` 提取解密 cookie → JSON
- MCP 会话 `browser_run_code` + `addCookies()` 注入
- passport 记住密码 cookie (username/password hash) 触发自动登录

### 4. 两种模式共存
| 模式 | 启动方式 | 适用 |
|------|---------|------|
| Python 脚本 | `uv run python tongtu_auto_export.py` | 日常定时，免登录 |
| MCP 对话 | Claude Desktop 对话 | 探索新页面，一次性操作 |

## 踩坑记录（按严重程度排序）

### 坑 1：通途数据表格不加载（最关键！）
- **现象**：导出按钮点击后无反应，`expect_download` 超时 90s
- **根因**：通途页面 Bug——togglebutton 显示仓库"已选中"，但 ExtJS 数据表格未实际渲染。`exportExcelPage()` → `exportGoodsBalanceExcel()` → `Cannot read properties of undefined (reading 'table')` → 静默失败
- **排查过程**：
  1. 改用 `page.evaluate("exportExcelPage()")` 直接调 JS → 报错暴露真因
  2. MCP 实测点击有效 → 排除 selector 问题
  3. 用户观察：先切走再切回，数据就加载了
- **修复**：`select_warehouse()` 中如果已选中，先切到其他仓库等 3s，再切回来等 8s

### 坑 2：Cookie 加密
- **现象**：SQLite 直接读 `chrome-profile/Default/Network/Cookies` → cookie 值为空
- **原因**：Chromium 用 Windows DPAPI 加密 cookie value
- **解决**：Playwright `launch_persistent_context` + `context.cookies()` 获取解密值

### 坑 3：Session cookie 无法持久化
- **现象**：注入所有 cookie 后，`JSESSIONID` 仍然缺失
- **原理**：JSESSIONID 无 expires（session cookie），浏览器关闭即清除
- **解决**：passport 记住密码 cookie (username + password hash) 触发自动登录，重新签发 JSESSIONID

### 坑 4：MCP 热加载限制
- **现象**：session 中激活 MCP 后工具不可用
- **解决**：必须**新建对话**。MCP 只在 session 启动时加载

### 坑 5：中文路径编码（Windows）
- **现象**：`subprocess.run()` 读 stdout 报 `UnicodeDecodeError: 'gbk'`
- **解决**：`subprocess.run(..., encoding="utf-8", errors="replace")`

### 坑 6：下载路径差异
- **Python 脚本**：`page.expect_download()` 精确控制保存位置 (`downloads/`)
- **MCP 模式**：文件自动保存到 `.playwright-mcp/`（仓库根目录），需 `mcp_to_output.py` 整理

### 坑 7：13 个同名"导出Excel"按钮
- 通途页面有 FBA、FBF、Shein、Temu 等 13 个平台各自的导出按钮
- 必须用 `a[onclick="exportExcelPage()"]` 精确定位库存清单的导出按钮

### 坑 8：git worktree 理解
- 主仓库 (`C:\Users\zhang\通途库存Excel`) 在 `main` 分支
- 调试 worktree (`.claude/worktrees/`) 在独立分支
- 两个独立工作区，互不干扰，完成后 merge 回 main

## 通途页面 DOM 知识

### 仓库选择器（非标准 `<select>`）
- **类型**：ExtJS `xtype="togglebutton"` 自定义组件
- **容器**：`div#warehouseDisableDiv`
- **元素**：`<a class="toggle_btn">` (未选中) / `class="toggle_btn_down">` (选中)
- **定位**：`page.locator("#warehouseDisableDiv a.toggle_btn", has_text="CENTRADE")`

### 登录检测
- 特征元素：`#warehouseDisableDiv` 可见 = 已登录
- 轮询方式：`page.locator("#warehouseDisableDiv").is_visible()`

### 导出按钮
- 精确选择器：`a[onclick="exportExcelPage()"]`（不要用 `text=导出Excel`）

### 筛选按钮
- 仓库类型：`#allWarehouseTypeBtn` → "全部(非FBA)"
- 仓库状态：`#statusBtn` → "已启用"

### Excel 文件结构（库存结存清单）
- 第 1 行：标题 "库存结存清单"
- 第 2 行：仓库信息 + 导出时间
- 第 3 行：空
- 第 4 行：列标题（以 SKU 开头，共 19 列）
- 第 5+ 行：数据
- 末尾行：数量总计 / 金额总计（需跳过）

### Excel 列映射
- A: SKU → 导入模板 SKU/SKU别名
- Q(17): 头程运费(CNY) → 导入模板头程运费
- S(19): 头程其它费(CNY) → 导入模板其他费用

## 给新 Agent/同事的速查

**运行导出**：`uv run python tongtu_auto_export.py`

**运行合并**：`uv run python merge_inventory.py`

**环境检测**：`uv --version && node --version`

**常见问题**：
- 浏览器弹出白屏 → 通途服务器慢，等 30s
- 导出按钮无反应 → 可能是登录过期，加 `--fresh`
- 中文乱码 → Windows GBK 编码问题，不影响结果
- 安全库存有 0 → 确认使用最新脚本（留空 None 非 0）

**隐私注意**：
- `chrome-profile/` 含明文 cookie，**绝不能提交 git**
- `mcp_cookies.json` 含密码 hash，**绝不能提交 git**
- `downloads/` 和 `output/` 含业务数据，**绝不能提交 git**
- 以上目录已在 `.gitignore` 中排除
