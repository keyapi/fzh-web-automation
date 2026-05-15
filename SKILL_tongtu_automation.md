---
name: tongtu-automation
description: >
  操控通途 ERP (erp102.tongtool.com) 的库存结存导出、仓库切换、数据转换。
  当用户提到"通途"、"Tongtu"、"tongtool"、"库存结存"、"头程运费"、
  "6个仓库"、"CENTRADE"、"togglebutton"、"exportExcelPage"等时触发。
  不要用于赛狐 (Sellfox) — 那是另一个独立系统 (见 sellfox-automation skill)。
metadata:
  platform: Tongtu ERP (ExtJS)
  python_script: tongtu_auto_export.py
  profile_dir: chrome-profile/
  warehouses: 6
  updated: 2026-05-15
---

# 通途 ERP 库存自动化

## Hard Constraints

- 通途是 **ExtJS** 框架，**永远**不要用 el-select/el-dialog 等 Element UI 选择器
- 仓库选择器是自定义 **togglebutton** (`a.toggle_btn`/`a.toggle_btn_down`)，不是 `<select>`
- 导出按钮是 `<a onclick="exportExcelPage()">`，**永远**不要用 `text=导出Excel`（有 13 个同名按钮！）
- 数据表格是 ExtJS grid，**永远**等 toggle 切换后等 8 秒再操作

## When to Use vs NOT

| Use when... | NOT when... |
|-------------|-------------|
| 通途 ERP (erp102.tongtool.com) | 赛狐 (sellfox.com) → sellfox-automation |
| 库存结存页面导出 | 其他通途页面（采购/订单等）→ 需额外探索 |
| ExtJS togglebutton 选择器 | Element UI 页面 |

## 仓库列表（6 个，按导出顺序）

```python
WAREHOUSES = [
    "CENTRADE",           # ~1,624 SKU
    "FZHPoland-covers",   # ~1,359 SKU
    "FZH-DANEEY-皮壳仓库",  # ~896 SKU
    "FZH-DANEEY-退货产品仓", # ~505 SKU
    "FZH-DANEEY-成品仓",    # ~241 SKU
    "FZH-DANEEY-半成品仓",  # ~146 SKU
]
```

## Quality Checklist（Agent 自查）

- [ ] **登录检测**：`#warehouseDisableDiv` 是否可见？（可见=已登录）
- [ ] **仓库 Bug 规避**：切换到第一个仓库时，是否"先切走再切回来"了？
- [ ] **筛选条件**："全部(非FBA)" + "已启用" 是否已勾选？（`ensure_toggle`）
- [ ] **导出按钮**：用 `a[onclick="exportExcelPage()"]` 而非 `text=导出Excel`
- [ ] **数据行**：Excel 末尾的"数量总计"/"金额总计"行是否已跳过？
- [ ] **安全库存/头程报关费**：生成导入文件时是否留空 (None) 而非填 0？

---

## Python 代码片段

### 1. 登录 + Cookie 持久化

```python
from playwright.sync_api import sync_playwright
from pathlib import Path

PROFILE_DIR = Path("chrome-profile")
URL = "https://erp102.tongtool.com/warehouse/goodsbalance/index.htm?warehouse=1&isFirstInto=1"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,          # True=后台, False=可见演示
        accept_downloads=True,
        viewport={"width": 1280, "height": 800},
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(URL, timeout=60000)
    page.wait_for_timeout(3000)

    # 登录检测: #warehouseDisableDiv 可见 = 已登录
    if page.locator("#warehouseDisableDiv").count() == 0:
        print("未登录，请在浏览器中手动登录...")
        for _ in range(100):  # 最长等 300s
            time.sleep(3)
            if page.locator("#warehouseDisableDiv").count() > 0:
                if page.locator("#warehouseDisableDiv").is_visible():
                    print("登录成功!")
                    break
```

### 2. 选择仓库（含通途 Bug 规避）

```python
def select_warehouse(page, name, all_warehouses):
    """选择仓库，自动规避通途数据表格不加载 Bug"""
    target = page.locator(
        "#warehouseDisableDiv a.toggle_btn, #warehouseDisableDiv a.toggle_btn_down",
        has_text=name,
    ).first
    target.wait_for(state="visible", timeout=5000)

    cls = target.get_attribute("class") or ""
    if "toggle_btn_down" in cls:
        # ⚠️ 通途 Bug: togglebutton 显示选中但 ExtJS grid 未渲染
        # 必须先切到其他仓库再切回来
        other = next(w for w in all_warehouses if w != name)
        print(f"  规避Bug: 先切 {other} 再切回 {name}")
        page.locator(
            "#warehouseDisableDiv a.toggle_btn, #warehouseDisableDiv a.toggle_btn_down",
            has_text=other,
        ).first.click()
        page.wait_for_timeout(3000)
    else:
        print(f"  切换至: {name}")

    target.click()
    page.wait_for_timeout(8000)  # ExtJS grid 渲染需 8s
```

### 3. 导出（核心操作）

```python
def click_export(page, warehouse_name):
    """点击导出按钮并捕获下载"""
    safer_prefix = warehouse_name.replace("/", "-").replace("\\", "-")

    # ⚠️ 必须用 onclick 属性精确匹配，页面有 13 个同名 "导出Excel" 按钮！
    with page.expect_download(timeout=60000) as dl_info:
        page.locator('a[onclick="exportExcelPage()"]').first.click()
        print(f"  已点击导出，等待下载...")

    download = dl_info.value
    filename = f"{safer_prefix}_{download.suggested_filename}"
    target = Path("downloads") / filename
    download.save_as(str(target))
    print(f"  已保存: {target}")
    return target
```

### 4. 确认筛选条件

```python
def ensure_toggle(page, div_id, label):
    """确保 toggle 按钮已选中（ExtJS togglebutton 组件）"""
    try:
        a = page.locator(f"#{div_id} a").first
        a.wait_for(state="visible", timeout=3000)
        if "toggle_btn_down" not in (a.get_attribute("class") or ""):
            print(f"  选中: {label}")
            a.click()
            page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  警告: 无法选中 {label}: {e}")

# 调用
ensure_toggle(page, "allWarehouseTypeBtn", "全部(非FBA)")
ensure_toggle(page, "statusBtn", "已启用")
```

### 5. 完整导出流程（6 仓库循环）

```python
from pathlib import Path
import subprocess, sys

DOWNLOADS_DIR = Path("downloads")
OUTPUT_DIR = Path("output")
DOWNLOADS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

for idx, wh in enumerate(WAREHOUSES, 1):
    print(f"\n[{idx}/6] {wh}")
    select_warehouse(page, wh, WAREHOUSES)
    inv_path = click_export(page, wh)

    # 生成导入文件（调 generate_tongtu_import.py）
    prefix = wh.replace("/", "-")
    out_path = OUTPUT_DIR / f"{prefix}_通途导入_头程运费_其他费用.xlsx"
    subprocess.run(
        [sys.executable, "generate_tongtu_import.py", str(inv_path), str(out_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )

# 合并多仓
import pandas as pd
all_dfs = []
for wh in WAREHOUSES:
    prefix = wh.replace("/", "-")
    files = sorted(DOWNLOADS_DIR.glob(f"{prefix}_库存结存清单*.xlsx"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        df = pd.read_excel(files[0], header=None)
        header_idx = df[df.iloc[:, 0].astype(str).str.strip() == "SKU"].index[0]
        df.columns = df.iloc[header_idx].astype(str).str.replace("\n", "").str.strip()
        df = df.iloc[header_idx + 1:]
        df = df[~df.iloc[:, 0].astype(str).str.strip().isin(["数量总计", "金额总计", "", "nan"])]
        df = df[df.iloc[:, 0].notna()]
        all_dfs.append(df)

merged = pd.concat(all_dfs, ignore_index=True)
from datetime import datetime
ts = datetime.now().strftime("%Y%m%d_%H%M")
merged_path = OUTPUT_DIR / f"通途合并库存结存清单 {ts}.xlsx"
merged.to_excel(merged_path, index=False)
print(f"合并完成: {len(merged)} 行 → {merged_path}")
```

### 6. Excel 数据转换（generate_tongtu_import.py 核心逻辑）

```python
import pandas as pd

TEMPLATE_COLS = [
    'SKU/SKU别名(必填)', '安全库存', '头程报关费（CNY）',
    '头程运费（CNY）', '其他费用（CNY）'
]

def read_inventory(path):
    df = pd.read_excel(path, header=None)
    # 找表头行（第1列为 SKU 的行）
    header_idx = df[df.iloc[:, 0].astype(str).str.strip() == 'SKU'].index[0]
    df.columns = df.iloc[header_idx].astype(str).str.replace('\n', '').str.strip()
    df = df.iloc[header_idx + 1:]
    # 跳过汇总行
    df = df[~df.iloc[:, 0].astype(str).str.strip().isin(
        ['数量总计', '金额总计', '', 'nan']
    )]
    df = df[df.iloc[:, 0].notna()]
    # 列映射: Q=头程运费, S=头程其它费
    freight_col = [c for c in df.columns if '头程运费' in c][0]
    other_col = [c for c in df.columns if '头程其它费' in c or '其他费用' in c][0]
    return df.iloc[:, 0].tolist(), df[freight_col].tolist(), df[other_col].tolist()
```

### 7. MCP 下载文件整理

```python
# MCP 下载后在 .playwright-mcp/ 目录，运行:
# uv run python mcp_to_output.py --auto
# 自动将文件按仓库重命名 → downloads/ + 生成导入文件 → output/
```

---

## 关键选择器速查

| 元素 | 选择器 | 陷阱 |
|------|--------|------|
| 仓库按钮 | `#warehouseDisableDiv a.toggle_btn:has-text("CENTRADE")` | toggle_btn_down=选中态 |
| 导出按钮 | `a[onclick="exportExcelPage()"]` | 页面有 13 个"导出Excel"！ |
| 登录检测 | `#warehouseDisableDiv` 可见 | poll 检测 |
| 筛选-类型 | `#allWarehouseTypeBtn a` → "全部(非FBA)" | ExtJS togglebutton |
| 筛选-状态 | `#statusBtn a` → "已启用" | ExtJS togglebutton |

## 踩坑速查（8 条）

| # | 现象 | 根因 | 解决 |
|---|------|------|------|
| 1 | 导出无反应，`expect_download` 超时 | 通途 Bug：toggle 显示选中但 ExtJS grid 未渲染 | **先切其他仓库再切回来** |
| 2 | SQLite 读 cookie 为空 | Chromium DPAPI 加密 | `context.cookies()` 获取解密值 |
| 3 | 注入 cookie 后 JSESSIONID 缺失 | session cookie 无 expires | passport 记住密码 cookie 触发自动登录 |
| 4 | MCP session 中 MCP 工具不可用 | MCP 只在 session 启动时加载 | **新建对话** |
| 5 | `subprocess.run()` 读 stdout 报错 | Windows GBK 编码 | `encoding="utf-8", errors="replace"` |
| 6 | MCP 下载位置和 Python 脚本不同 | MCP 自动保存到 `.playwright-mcp/` | 用 `mcp_to_output.py` 整理 |
| 7 | `text=导出Excel` strict mode violation | 13 个同名按钮 | 用 `a[onclick="exportExcelPage()"]` 精确定位 |
| 8 | git worktree 理解混乱 | 主 worktree(main) + 调试 worktree(分支) | 在 worktree 独立开发，完成 merge 回 main |

## Excel 文件结构

```
第1行: "库存结存清单"
第2行: "仓库 XXX  库存清单导出时间 YYYY"
第3行: 空
第4行: 列标题 (SKU, 货品名称/规格, ...共19列)
第5+行: 数据
末尾行: "数量总计" / "金额总计" (需跳过)
```

**列映射**：A=SKU, Q(17)=头程运费(CNY), S(19)=头程其它费(CNY)

**导入文件 5 列**：SKU/SKU别名 | 安全库存(None!) | 头程报关费(None!) | 头程运费 | 其他费用

---

## 给同事的日常使用说明

```cmd
# 一键运行（日常推荐）
uv run python tongtu_auto_export.py

# 强制重新登录
uv run python tongtu_auto_export.py --fresh

# 导出 cookie 供 MCP 使用
uv run python tongtu_auto_export.py --export-cookies

# MCP 下载后整理
uv run python mcp_to_output.py --auto
```

**常见问题**：浏览器白屏→等30s | 导出无反应→`--fresh` | 安全库存有0→用最新脚本
