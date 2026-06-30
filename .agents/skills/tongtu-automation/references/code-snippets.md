# 通途 — Python Playwright 代码片段

> 可直接复制使用。每个片段对应 SKILL.md 中的一个操作步骤。

---

## 1. 登录 + Cookie 持久化

```python
from playwright.sync_api import sync_playwright
from pathlib import Path

PROFILE_DIR = Path("chrome-profile")
URL = "https://erp102.tongtool.com/warehouse/goodsbalance/index.htm?warehouse=1&isFirstInto=1"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        accept_downloads=True,
        viewport={"width": 1280, "height": 800},
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(URL, timeout=60000)
    page.wait_for_timeout(3000)

    # 登录检测
    if page.locator("#warehouseDisableDiv").is_visible():
        print("已登录")
    else:
        print("请手动登录...")
        for _ in range(100):
            time.sleep(3)
            if page.locator("#warehouseDisableDiv").is_visible():
                print("登录成功!")
                break
```

## 2. 选择仓库

```python
def select_warehouse(page, name, all_warehouses):
    """选择仓库，自动规避通途 Bug"""
    target = page.locator(
        "#warehouseDisableDiv a.toggle_btn, #warehouseDisableDiv a.toggle_btn_down",
        has_text=name,
    ).first
    target.wait_for(state="visible", timeout=5000)

    cls = target.get_attribute("class") or ""
    if "toggle_btn_down" in cls:
        # 通途 Bug 规避: 先切到其他仓库再切回来
        other = next(w for w in all_warehouses if w != name)
        page.locator(
            "#warehouseDisableDiv a.toggle_btn, #warehouseDisableDiv a.toggle_btn_down",
            has_text=other,
        ).first.click()
        page.wait_for_timeout(3000)

    target.click()
    page.wait_for_timeout(8000)  # ExtJS grid 渲染
```

## 3. 确认筛选条件

```python
def ensure_toggle(page, div_id, label):
    """确保 ExtJS togglebutton 已选中"""
    a = page.locator(f"#{div_id} a").first
    a.wait_for(state="visible", timeout=3000)
    if "toggle_btn_down" not in (a.get_attribute("class") or ""):
        print(f"  选中: {label}")
        a.click()
        page.wait_for_timeout(1500)

# 使用
ensure_toggle(page, "allWarehouseTypeBtn", "全部(非FBA)")
ensure_toggle(page, "statusBtn", "已启用")
```

## 4. 导出（核心）

```python
def click_export(page, warehouse_name):
    """导出当前仓库库存清单"""
    safer_prefix = warehouse_name.replace("/", "-").replace("\\", "-")

    with page.expect_download(timeout=60000) as dl_info:
        # ⚠️ 必须用 onclick 属性！页面有 13 个同名按钮
        page.locator('a[onclick="exportExcelPage()"]').first.click()

    download = dl_info.value
    filename = f"{safer_prefix}_{download.suggested_filename}"
    target = Path("downloads") / filename
    download.save_as(str(target))
    print(f"  已保存: {target}")
    return target
```

## 5. 完整导出流程（6 仓库循环）

```python
from pathlib import Path
import subprocess, sys

DOWNLOADS_DIR = Path("downloads")
OUTPUT_DIR = Path("output")
DOWNLOADS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

WAREHOUSES = [
    "CENTRADE", "FZHPoland-covers", "FZH-DANEEY-皮壳仓库",
    "FZH-DANEEY-退货产品仓", "FZH-DANEEY-成品仓", "FZH-DANEEY-半成品仓",
]

for idx, wh in enumerate(WAREHOUSES, 1):
    print(f"\n[{idx}/6] {wh}")
    select_warehouse(page, wh, WAREHOUSES)
    inv_path = click_export(page, wh)

    # 生成导入文件
    prefix = wh.replace("/", "-")
    out_path = OUTPUT_DIR / f"{prefix}_通途导入_头程运费_其他费用.xlsx"
    subprocess.run(
        [sys.executable, "generate_tongtu_import.py", str(inv_path), str(out_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )

# 参考 tongtu_auto_export.py 中的 merge_all_inventory() 函数合并结果
```

## 6. Cookie 导出（MCP 注入用）

```python
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="chrome-profile/", headless=True
    )
    all_cookies = context.cookies()
    context.close()

tongtu_cookies = [c for c in all_cookies if "tongtool" in c.get("domain", "")]
with open("mcp_cookies.json", "w") as f:
    json.dump(tongtu_cookies, f, indent=2)
print(f"已导出 {len(tongtu_cookies)} 个 cookie")
```

## 7. Excel 数据转换（generate_tongtu_import.py 核心）

```python
import pandas as pd

TEMPLATE_COLS = [
    'SKU/SKU别名(必填)', '安全库存', '头程报关费（CNY）',
    '头程运费（CNY）', '其他费用（CNY）'
]

def read_inventory(path):
    df = pd.read_excel(path, header=None)
    # 找表头行
    header_idx = df[df.iloc[:, 0].astype(str).str.strip() == 'SKU'].index[0]
    df.columns = df.iloc[header_idx].astype(str).str.replace('\n', '').str.strip()
    df = df.iloc[header_idx + 1:]
    # 跳过汇总行
    df = df[~df.iloc[:, 0].astype(str).str.strip().isin(
        ['数量总计', '金额总计', '', 'nan']
    )]
    df = df[df.iloc[:, 0].notna()]
    # 列映射: 头程运费 / 头程其它费
    freight_col = [c for c in df.columns if '头程运费' in c][0]
    other_col = [c for c in df.columns if '头程其它费' in c or '其他费用' in c][0]
    return df.iloc[:, 0].tolist(), df[freight_col].tolist(), df[other_col].tolist()
```
