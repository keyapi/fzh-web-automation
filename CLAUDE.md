# CLAUDE.md — 跨境电商 ERP 自动化项目

## 通用守则 (Andrej Karpathy)

> 源自 [Andrej Karpathy 对 LLM 编码陷阱的观察](https://x.com/karpathy/status/2015883857489522876)，由 [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) 整理。
> **权衡取舍**：这些准则偏向谨慎而非速度。对于琐碎任务，自行判断。

### 守则 1：编码前思考
**不假设。不隐藏困惑。呈现权衡。**
- 明确陈述你的假设。如果不确定，询问。
- 如果存在多种解释，呈现它们——不要默默选择。
- 如果有不清楚的地方，停下来。指出困惑之处。提问。

### 守则 2：简洁优先
**用最少代码解决问题。不做投机性工作。**
- 不添加未被要求的功能；不为一次性代码创建抽象。
- 不为不可能发生的场景做错误处理。
- 扪心自问："资深工程师会觉得这过于复杂吗？"如果是，就简化。

### 守则 3：精准修改
**只碰必须碰的。只清理自己造成的混乱。**
- 不"改进"相邻的代码、注释或格式；不重构没坏的东西。
- 匹配已有风格，即使你更倾向于不同的写法。
- 删除因你改动而不再使用的导入/变量/函数；不删除已存在的死代码。
- 检验标准：每一行被改动的代码都能直接追溯到用户的请求。

### 守则 4：目标驱动执行
**定义成功标准。循环验证直到达成。**
- "添加校验" → "先写非法输入测试用例，再让它们通过"
- "修 bug" → "先写一个能复现的测试，再让它通过"
- 多步骤任务陈述简要计划，每步标注验证点。

---

## 公司背景 (FZH)

**FZH** 是跨境电商公司，在北美和欧洲销售**家居纺织品**（填充物为 PP棉/海绵的靠枕、沙发等）。
销售平台：Amazon（北美+欧洲）、Wayfair、Home24、Shopify 等。

### 供应链架构

```
绍兴工厂 (中国)
  ├─ 生产皮壳、内胆、半成品（如缝制海绵进皮壳）
  ├─ 部分成品直接生产（填充+压缩+包装）→ FBA / 直接发货
  │
  └─ → 海外分公司仓库：
       ├── USNJ (美东, NJ州) → 填充/压缩/包装/仓储/发货(2C+个别2B)
       ├── USTX (美中, TX州) → 同上
       └── POLAND (波兰)     → 同上
            │
            └─ → Amazon FBA / 第三方海外仓
```

海外分公司负责：填充、抽真空压缩、包装、仓储、发货（主要是 2C，个别 2B）。

### 赛狐仓库映射

| 公司仓库 | 赛狐仓库名 | 说明 |
|----------|-----------|------|
| USNJ 美东仓 | CENTRADE | 已启用 |
| USTX 美中仓 | DANEEY | 已启用 |
| POLAND 波兰仓 | POLAND | 已启用 |
| 绍兴工厂(本地) | — | 未启用（赛狐本地仓限制多） |

> 赛狐有两种仓库类型：**本地仓**（中国仓，更多限制，未启用）和**海外仓**（我们用的 3 个分公司仓）。
> 赛狐本身主要服务小卖家（中国直发），我们的架构不同，需要"套进"赛狐体系使用。

### 财务核算需求

可能经常需要调整库存成本（类似 ERPNext 的库存调账）：
- 原材料价格变化
- 头程价格变化
- 之前维护的数据不对

**赛狐限制**：海外仓不能直接通过库存调账修改库存数量和采购单价。
需要通过 **其他入库 / 其他出库** 的方式实现成本调整。

---

## 通途项目背景

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
├── SKILL_tongtu_automation.md     # Skill: 通途专项自动化
├── sellfox_auto_export.py          # 赛狐库存导出（浏览器+API）
├── sellfox_import_update.py        # 赛狐商品导入更新（闭环验证）
├── sellfox_import_other_outbound.py # 赛狐其他出库一键导入
├── sellfox_import_warehouse_restock.py # 赛狐海外仓备货单一键导入
├── sellfox_restock_allocate_ship.py   # 备货单分配库存+发货
├── sellfox_restock_receive.py         # 备货单批量SKU收货
├── commodity_import_template.py    # 赛狐下载商品导入模板
└── sellfox-profile/                # 赛狐持久化登录 (gitignore)
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
- **现象 1**：`subprocess.run()` 读 stdout 报 `UnicodeDecodeError: 'gbk'`
- **解决 1**：`subprocess.run(..., encoding="utf-8", errors="replace")`
- **现象 2**：Python print 中文/Unicode 直接崩溃（`UnicodeEncodeError: 'gbk' codec can't encode character`）
- **根因**：Windows 下 Python stdout 默认 GBK 编码，不能处理 ✓ 等 Unicode 字符
- **解决 2**：每个脚本开头加 `sys.stdout.reconfigure(encoding='utf-8')`，所有 8 个 py 文件均已内置

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

### 坑 9：赛狐页面 20+ 隐藏 dialog（关键！）
- **现象**：`document.querySelector('.el-dialog__wrapper')` 拿到第一个（是隐藏的空壳）
- **原因**：赛狐所有弹窗预渲染在 DOM 中，只有 1 个 visible
- **解决**：**永远**用 `.filter(d => d.getBoundingClientRect().width > 0)` 过滤

### 坑 10：Element UI checkbox 不能用 evaluate click
- **现象**：`cb.click()` 在 evaluate 中不改变 Vue 组件状态
- **解决**：必须用 Playwright `page.locator().click()` 真实点击

### 坑 11：赛狐导入 Excel 的 sheet 名陷阱
- **现象**：`pd.to_excel()` 生成的文件导入卡在"正在导入"
- **根因**：赛狐模板 sheet 名必须是 `商品`（默认 `Sheet1` 不认）
- **解决**：`ExcelWriter(sheet_name='商品')` + 不复用模板文件

### 坑 12：el-dropdown-menu__item 对 Playwright 不可见
- **现象**：Playwright click 超时 (element not visible)
- **解决**：使用 `page.evaluate("item.click()")` 绕过可见性检查

### 坑 13：无 MCP 探索直接猜 URL 浪费大量精力（教训！）
- **现象**：找"其他入库"入口时，在 Python Playwright 脚本中穷举了 20+ 个猜测 URL，
  反复试错耗时数十分钟，结果入口其实在侧边栏展开菜单中（一个 `<a>` 标签点击即可）
- **根因**：Sellfox 的 SPA 侧边栏菜单只在点击"仓库"导航后动态展开，
  菜单项是 `<a>` 标签直接点击触发 Vue Router 导航，URL 无法直接访问
- **正确做法**：先用 MCP Playwright 浏览器浏览页面→截图→evaluate 搜 DOM→点菜单找 URL，
  确认后只用 Python 写脚本。不要凭猜测凑 URL
- **教训级别**：🔴 严重 —— 10 分钟 MCP 探索可省 2+ 小时 Python 试错

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

当前探索：库存明细页已完成 DOM 摸查+导出弹窗+API逆向+Python脚本。商品导入页已完成下载模板+上传导入全流程。

### 赛狐 Excel 导入（关键教训）
- **必须 sheet_name='商品'**：模板文件有 3 个 sheet (`['商品','hidden1','hidden2']`)，`pd.to_excel()` 默认 `Sheet1` 会被赛狐拒绝
- **禁止 pd.read_excel(模板)**：读模板会带 hidden sheet，`to_excel` 后丢失这些 sheet → 导入卡死
- **正确做法**：只取表头列名 → `pd.DataFrame()` 构造数据 → `ExcelWriter(sheet_name='商品')` 写入
- **文件上传**：Python Playwright 用 `expect_file_chooser` + `set_files()`，或直接用 `set_input_files`
- **上传后弹窗**：`POST /excel/import.json` (multipart/form-data) 返回 200+taskID，但前端等 WebSocket 通知

---

## Skill 管理规则（2026 最佳实践）

### 核心原则
1. **每个平台/模块一个 skill**，职责单一，不堆砌
2. **SKILL.md 是入口索引**（<300 行），不做百科
3. **references/ 放详情**（页面结构、选择器、代码），按需加载
4. **description 是触发命中的关键**——必须包含用户真正会说的自然语言
5. **所有 skill 文件纳入 git**，可回滚、可协作

### 目录规范
```
.claude/skills/<kebab-case-name>/          # 小写中划线
├── SKILL.md                               # 入口：YAML frontmatter + 正文
├── references/                            # 渐进加载的参考文件（一层深度）
│   ├── page-detail.md                     # 页面 DOM + 选择器 + 操作流程
│   ├── code-snippets.md                   # Python 代码片段
│   └── ...                                # 每个页面/模块一个文件
└── scripts/                               # (可选) 独立脚本
```

### YAML Frontmatter 模板

```yaml
---
name: platform-automation
description: >
  一句话描述 skill 用途。包含所有用户可能使用的触发词。
  "当用户提到 XXX、YYY、ZZZ 等时触发。"
  这行是 Claude 自动检测是否激活 skill 的唯一依据，务必覆盖完整！
compatibility: >
  依赖说明：需要什么环境、工具、配置文件。
metadata:
  platform: 平台名 (技术栈)
  python_script: 主脚本文件名
  profile_dir: 登录配置目录
  updated: 2026-05-19
---
```

**description 编写规则**：
- 包含用户真正会说出口的词：产品名、动词、功能名
- 中英文都要覆盖（如 "通途"+"Tongtu"+"库存结存"+"export"）
- 用自然语言短语而非关键词堆砌
- 明确 NOT 情况：什么情况下**不要**触发

### 编写原则

| 原则 | 说明 |
|------|------|
| **SKILL.md < 300 行** | 只保留触发条件、约束、操作流程索引、Quality Checklist |
| **references/ 放细节** | 每个页面/主题一个文件，结构：URL→页面结构→选择器→流程→踩坑 |
| **中文 + 英文选择器** | 面向中文用户描述，代码级内容保持原样 |
| **"给同事"版块** | 每个 SKILL.md 开头放"一句话触发"表格，非技术同事只看这个 |
| **去重** | SKILL.md 不重复 CLAUDE.md 已有内容，用引用代替 |

### 触发词覆盖规则
description 中必须覆盖以下类型的触发词：

| 类型 | 示例 |
|------|------|
| 平台名中英文 | 通途/Tongtu/tongtool, 赛狐/Sellfox/sellfox.com |
| 核心动词 | 导出/导入/搜索/切换/合并/下载/上传 |
| 关键页面名 | 库存明细/库存结存/商品列表/仓库导出 |
| 特征元素 | togglebutton/el-select/el-dialog/图标导出 |
| 用户习惯说法 | 6个仓库/CENTRADE/头程运费/隐藏0数据 |

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
2. 读取结果（下载文件/API查询/弹窗文本）
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

### 给非技术同事的用法指南

技能迁移完成后，同事只需在 Claude Code 中自然语言说出需求：

| 你想做什么 | 就说这句话 |
|-----------|-----------|
| 通途导出全部仓库 | "**通途导出库存**" |
| 通途导指定仓库 | "**通途导出 CENTRADE 仓库**" |
| 通途重新登录 | "**通途重新登录**" |
| 赛狐导出库存 | "**赛狐导出库存**" |
| 赛狐搜索商品 | "**赛狐搜索 SKU KS0001**" |
| 赛狐导入更新商品 | "**赛狐导入更新商品**" |
| 查看所有 skill | "**/skill**" |

> 首次运行两个平台都需要手动登录一次（浏览器弹窗），之后免登录。

---

## WebFetch 失败修复（2026-05-20）

**问题**：Claude Code WebFetch 报错 `Unable to verify if domain is safe to fetch`

**原因**：Claude Code 在获取网页前会访问 `claude.ai` 做域名安全预检，企业网络/GFW 会拦截这个预检请求。

**解决**：在用户级配置文件 `%USERPROFILE%\.claude\settings.json` 中加入：
```json
{
  "skipWebFetchPreflight": true
}
```
> 注意：这是用户级配置（不在项目 `.claude/` 下），需要重启 Claude Desktop 生效。
> 备选方案：用 `curl` 绕过（`Bash(curl:*)` 许可即可）

---

## Hooks 钩子学习记录（2026-05-20）

### 结论：当前项目不需要也不使用 Hooks

#### 知识来源
1. 官方 Blog: [How Claude Code works in large codebases](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start) — 阐释 Harness 架构（CLAUDE.md → Hooks → Skills → Plugins → MCP）
2. 社区教程/案例（CSDN、dev.to、GitHub Issues）

#### Hooks 核心知识

| 生命周期事件 | 作用 | 我们适用？ |
|-------------|------|-----------|
| `SessionStart` | 注入动态上下文（git 分支等） | ❌ GUI/Desktop 不支持 (Bug #16763) |
| `PreToolUse` | 拦截危险命令（exit 2 阻止） | ❌ 无强拦截需求 |
| `PostToolUse` | 自动格式化、lint | ❌ 不做 Web 开发 |
| `UserPromptSubmit` | 每次提示前预处理 | ❌ 频率太高，过度设计 |
| `Stop` | 会话结束反思总结 | ❌ 不需要 |

#### 实测结论

1. **Claude Desktop 3P 安装版不支持 SessionStart hooks**（官方已知 Bug [#16763](https://github.com/anthropics/claude-code/issues/16763)）——只对 CLI 启动的 session 有效，GUI pane 不触发
2. **Plugin 中的 SessionStart hook 也有问题**（官方 Bug [#16538](https://github.com/anthropics/claude-code/issues/16538)）——`additionalContext` 不会被传递给 Claude

#### 设计原则

- Hooks 适合**企业团队场景**（强制代码规范、审查流程）和**确定性拦截**（PreToolUse 拦截 `rm -rf` / `git push --force`）
- 个人项目如果只是"想让 Claude 知道些信息"，用 CLAUDE.md + SKILL.md 就够，不需要 Hook
- `git status` 这类即时查询，让 Claude 现场跑一下就行（1 秒完成），不需要 Hook 预注入
- **过度设计比不做更糟糕**——别为了用一个技术而去用它
