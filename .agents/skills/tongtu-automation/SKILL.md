---
name: tongtu-automation
description: >
  操控通途 ERP (erp102.tongtool.com) 的库存结存导出、仓库切换、数据转换。
  当用户提到"通途"、"Tongtu"、"tongtool"、"库存结存"、"头程运费"、
  "6个仓库"、"CENTRADE"、"exportExcelPage"、"togglebutton"、
  "导出库存"、"仓库导出"、"chrome-profile"等时触发。
  不要用于赛狐 (Sellfox) — 那是另一个独立系统 (见 sellfox-automation skill)。
compatibility: >
  需要 Python Playwright (sync_api) 及 openpyxl/pandas。
  持久化会话依赖 `chrome-profile/` 目录（gitignored）。
metadata:
  platform: Tongtu ERP (ExtJS)
  python_script: tongtu_auto_export.py
  profile_dir: chrome-profile/
  warehouses: 6
  updated: 2026-05-19
---

# 通途 ERP 库存自动化

## 一句话触发（给同事）

在 Claude Code 中说下面的话即可自动执行：

| 你想做什么 | 就说 |
|-----------|------|
| 导出全部 6 个仓库库存 | "**通途导出库存**" |
| 导出指定仓库 | "**通途导出 CENTRADE 仓库**" |
| 强制重新登录 | "**通途重新登录**" |
| 导出 cookie 供 MCP 用 | "**通途导出 cookie**" |
| 合并已导出的清单 | "**通途合并库存**" |
| 查看当前仓库有哪些 | "**通途有哪些仓库**" |

> 首次运行需要手动登录一次（浏览器会弹出），之后免登录。

## Hard Constraints

- 通途是 **ExtJS** 框架，**永远**不要用 el-select/el-dialog 等 Element UI 选择器
- 仓库选择器是自定义 **togglebutton**：未选中 `a.toggle_btn` / 已选中 `a.toggle_btn_down`
- 导出按钮必须用 `a[onclick="exportExcelPage()"]` 精确定位（页面有 13 个同名"导出Excel"按钮！）
- **永远**不要在 `expect_download` 的 with 块外调用 `download.save_as()` — 会超时
- SPA 页面，切换仓库后**至少等 8 秒**再操作（ExtJS grid 渲染慢）

## When to Use vs NOT

| ✅ 用这个 skill | ❌ 不用这个 skill |
|----------------|-----------------|
| 通途 EP (erp102.tongtool.com) | 赛狐 (sellfox.com) → `/skill sellfox-automation` |
| 库存结存页面导出 / 数据转换 | 通途其他页面（采购/订单等）→ 需额外探索 |
| ExtJS togglebutton 选择器 | Element UI / Vue 页面 |

## 快速运行

```bash
# 日常导出（6 仓库依次导出 + 生成导入文件 + 合并）
uv run python tongtu_auto_export.py

# 强制重新登录（登录过期时用）
uv run python tongtu_auto_export.py --fresh

# 导出 cookie 给 MCP 注入
uv run python tongtu_auto_export.py --export-cookies

# MCP 下载后整理文件
uv run python mcp_to_output.py --auto
```

## 核心操作流程

### 1. 启动浏览器 + 登录检测

```python
from playwright.sync_api import sync_playwright
context = p.chromium.launch_persistent_context(
    user_data_dir="chrome-profile/",
    headless=False, accept_downloads=True,
)
page = context.pages[0]
page.goto(TONGTU_URL, wait_until="networkidle", timeout=60000)

# 登录检测: #warehouseDisableDiv 可见 = 已登录
if page.locator("#warehouseDisableDiv").count() > 0:
    print("已登录")
```

### 2. 选择仓库（含通途 Bug 规避）

```python
target = page.locator(
    "#warehouseDisableDiv a.toggle_btn, #warehouseDisableDiv a.toggle_btn_down",
    has_text=warehouse_name,
).first
# ⚠️ 通途 Bug: 显示已选中但数据未渲染 → 先切走再切回来
page.locator("...", has_text=other_warehouse).first.click()
page.wait_for_timeout(3000)
target.click()
page.wait_for_timeout(8000)  # ExtJS grid 渲染
```

### 3. 导出（核心）

```python
# 必须用 onclick 属性精确匹配！13 个同名按钮
with page.expect_download(timeout=60000) as dl_info:
    page.locator('a[onclick="exportExcelPage()"]').first.click()
download = dl_info.value
download.save_as(f"downloads/{warehouse}_{download.suggested_filename}")
```

### 4. 确认筛选条件

```python
# 仓库类型: "全部(非FBA)" — ExtJS togglebutton
page.locator("#allWarehouseTypeBtn a").first.click()
page.wait_for_timeout(1500)
# 仓库状态: "已启用"
page.locator("#statusBtn a").first.click()
page.wait_for_timeout(1500)
```

## 关键选择器速查

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 仓库按钮 | `#warehouseDisableDiv a.toggle_btn` | 未选中态 |
| 仓库按钮(选中) | `#warehouseDisableDiv a.toggle_btn_down` | 已选中态 |
| 导出按钮 | `a[onclick="exportExcelPage()"]` | 页面唯一，13 个同名按钮中精确匹配 |
| 登录检测 | `#warehouseDisableDiv` 可见 | poll 检测 |
| 仓库类型筛选 | `#allWarehouseTypeBtn a` | "全部(非FBA)" |
| 仓库状态筛选 | `#statusBtn a` | "已启用" |

## 仓库列表（6 个）

按导出顺序：CENTRADE → FZHPoland-covers → FZH-DANEEY-皮壳仓库 → FZH-DANEEY-退货产品仓 → FZH-DANEEY-成品仓 → FZH-DANEEY-半成品仓

> 详细数据（SKU 数、Excel 结构、踩坑）见 `CLAUDE.md` 踩坑记录 + 仓库表格。

## Excel 文件结构

| 行 | 内容 |
|----|------|
| 1 | "库存结存清单" |
| 2 | "仓库 XXX 库存清单导出时间 YYYY" |
| 3 | 空行 |
| 4 | 列标题（SKU, 货品名称/规格, ... 共 19 列） |
| 5+ | 数据行 |
| 末尾 | "数量总计" / "金额总计"（**必须跳过**） |

**列映射**: A=SKU → 导入模板 SKU/SKU别名, Q(17)=头程运费(CNY) → 导入模板头程运费, S(19)=头程其它费(CNY) → 导入模板其他费用

**导入文件 5 列**: SKU/SKU别名 | 安全库存(**留空None!**) | 头程报关费(**留空None!**) | 头程运费 | 其他费用

## Quality Checklist（给 Agent 自查）

- [ ] **登录检测**：`#warehouseDisableDiv` 是否可见？（可见=已登录）
- [ ] **仓库 Bug 规避**：切换仓库时是否"先切走再切回来"了？
- [ ] **筛选条件**："全部(非FBA)" + "已启用" 是否已勾选？
- [ ] **导出按钮**：用 `a[onclick="exportExcelPage()"]` 而非 `text=导出Excel`
- [ ] **数据行**：Excel 末尾的"数量总计"/"金额总计"行是否已跳过？
- [ ] **安全库存/头程报关费**：生成导入文件时是否留空 (None) 而非填 0？

## 参考

- [仓库导出详情](references/warehouse-export.md) — DOM 结构 + 完整操作流程
- [Python 代码片段](references/code-snippets.md) — 各步骤代码可直接复制
- [Excel 格式细节](references/excel-format.md) — 列映射 + 导入模板陷阱
- [主脚本](../tongtu_auto_export.py) — 完整自动化脚本
- [数据转换脚本](../generate_tongtu_import.py) — 库存清单 → 5 列导入模板
