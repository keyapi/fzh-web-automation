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

---

## 赛狐 (Sellfox) 平台

### 背景
公司正从通途逐步切换到赛狐 ERP。赛狐是店小秘生态的亚马逊 ERP 系统。

### 平台对比

| 维度 | 通途 | 赛狐 |
|------|------|------|
| URL | erp102.tongtool.com | www.sellfox.com |
| UI 框架 | ExtJS | **Element UI (Vue.js)** |
| 登录 | passport 统一 | 独立登录 + 拼图滑块 |
| 仓库选择器 | 自定义 togglebutton | el-select 标准下拉 |
| 导出方式 | 直接 `<a onclick>` | 图标按钮 → 弹窗选字段 → 确定 |
| 选择器策略 | onclick 属性 | class/placeholder 属性 |

### 关键选择器模式
- **下拉框**: `input[placeholder="全部仓库"]` — el-select 组件
- **按钮**: 可能是纯图标（如 `.icon_sf_download`），页面搜不到文字
- **弹窗**: `el-dialog` 组件，标题在 `.el-dialog__title`
- **表格**: `el-table` 或 `vxe-table`
- **复选框**: `el-checkbox`

### Skill 文件
详见 `.claude/skills/sellfox-automation/SKILL.md` 及 `references/` 子文件。

当前探索：库存明细页已完成初步 DOM 摸查，导出弹窗结构已掌握，实际下载行为待验证。

---

## Skill 管理规则

### 目录结构
遵循 [agentskills.io](https://agentskills.io) 规范：
```
.claude/skills/<skill-name>/
├── SKILL.md              # 入口：YAML frontmatter + Markdown 正文
└── references/           # 按需加载的参考资料（保持一层深度）
```

### 命名规则
- 小写 kebab-case：`sellfox-automation`、`warehouse-detailed`
- 一个 skill 一个职责，多页面用 references/ 拆分

### 编写原则
1. **SKILL.md 是索引**（<500 行），不堆砌细节
2. **references/ 放详情**，每页一个 reference 文件
3. **每个 reference 记录**：URL、页面结构、选择器、操作流程、已知未知、踩坑
4. **渐进披露**：metadata 常驻（~100 tokens）→ SKILL.md 按需加载 → references 更深按需
5. **每次 MCP 探索后立即更新** reference 文件，不积累记忆负担
6. **中文描述 + 英文选择器**：面向中文用户但代码级内容保持原样

### 新页面探索流程（铁律）
**任何新页面或新功能，必须按此顺序**：
1. **MCP 先探路**：用 Playwright MCP 手动操作，摸清 DOM 结构、选择器、交互流程
2. **Python 代码实现**：把 MCP 验证过的选择器翻译成 Python Playwright 代码
3. **文件记录**：立即创建/更新 `references/` 下的页面文件 + 更新 `SKILL.md` 引用
4. **git 提交**：提交时总结关键发现

**禁止**：不经过 MCP 探索就直接写 Python 代码 → 必然反复踩坑

### 闭环测试（铁律）
**任何自动化脚本写完后，必须自己跑一遍闭环验证**：
1. 执行操作（导出/导入/搜索）
2. 读取结果（下载文件/API查询）
3. 验证数据是否正确更新
4. **不验证 = 代码不可靠**
5. 验证失败要追根因，不"差不多得了"

### 探索后更新规则（最重要！）
- **每次 MCP 探索或代码测试有新发现，必须立即更新对应的 `references/*.md`**
- 不积累记忆负担——更新完文档再提交
- **不仅更新"已知未知"，要同步更新所有相关章节**（选择器表、踩坑记录、仓库列表、行为描述等）
- 如果只更新了部分而漏了其他相关章节 → 违规。自查原则："改了数据，所有引用该数据的章节都得更新"

### 运行规则（铁律）
- **永远用 `uv run python`**，不用 `python` 或 `pip install`
- **永远用 `uv add <包名>` 加依赖**，自动写入 `pyproject.toml`
- **worktree venv 需装 Chromium**：`uv run playwright install chromium`
- **主仓库 venv**（`.venv/`）有完整环境，也优先用 `uv run`

### Git 提交规则
- **每次代码修改后立即提交**，不攒一堆
- **中文提交信息**，格式：`动词: 具体描述`
- **及时合并到 main**，避免分支长期分离
- **保持工作区干净**：提交前检查 `git status`，不留临时文件

### 探索工作流（新页面通用流程）
1. `browser_navigate` 到目标 URL
2. 检测登录状态（URL 是否被重定向）
3. `browser_snapshot` → 太大用 `browser_evaluate` 精准提取
4. 搜索关键元素：过滤框 (input placeholder)、按钮 (icon class)、表格
5. 点击关键元素观察行为（弹窗、下载、页面跳转）
6. **立即记录到 references/**，不等全部探索完
7. 标记"已知未知"：哪些已验证、哪些待验证
