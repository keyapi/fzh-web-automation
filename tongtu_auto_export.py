#!/usr/bin/env python3
"""
通途库存清单自动导出 + 导入文件生成（多仓库版）
用法:
  uv run python tongtu_auto_export.py           # 持久化会话，依次导出所有仓库
  uv run python tongtu_auto_export.py --fresh    # 强制重新登录
"""
import subprocess, sys, time, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

TONGTU_URL = "https://erp102.tongtool.com/warehouse/goodsbalance/index.htm?warehouse=1&isFirstInto=1"
SCRIPT_DIR = Path(__file__).parent
PROFILE_DIR = SCRIPT_DIR / "chrome-profile"
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
OUTPUTS_DIR = SCRIPT_DIR / "outputs"
LOGIN_TIMEOUT_SECS = 300

# 依次导出的仓库列表
WAREHOUSES = [
    "CENTRADE",
    "FZHPoland-covers",
    "FZH-DANEEY-皮壳仓库",
    "FZH-DANEEY-退货产品仓",
    "FZH-DANEEY-成品仓",
    "FZH-DANEEY-半成品仓",
]

# 仓库名称 → 文件名安全前缀（不能有特殊字符）
def safe_prefix(name):
    return name.replace("/", "-").replace("\\", "-").replace(":", "-")


def is_already_logged_in(page):
    try:
        el = page.locator("#warehouseDisableDiv")
        return el.count() > 0 and el.is_visible()
    except:
        return False


def wait_for_login(page):
    print(f"\n[信息] 请在浏览器中登录通途...")
    print(f"[信息] 脚本将自动检测登录状态（最长等待 {LOGIN_TIMEOUT_SECS} 秒）")
    for i in range(0, LOGIN_TIMEOUT_SECS, 3):
        time.sleep(3)
        if is_already_logged_in(page):
            print("[OK] 检测到登录成功！自动继续...")
            page.wait_for_timeout(1000)
            return True
        if i % 15 == 0 and i > 0:
            print(f"  等待登录中... ({i}/{LOGIN_TIMEOUT_SECS}s)")
    return False


def ensure_toggle(page, div_id, label_text, target_class="toggle_btn_down"):
    """确保某个 toggle 按钮已选中（如仓库类型、仓库状态）"""
    try:
        a = page.locator(f"#{div_id} a").first
        a.wait_for(state="visible", timeout=3000)
        cls = a.get_attribute("class") or ""
        if target_class in cls:
            return True
        print(f"  [操作] 选中: {label_text}")
        a.click()
        page.wait_for_timeout(1500)
        return True
    except Exception as e:
        print(f"  [警告] 无法选中 {label_text}: {e}")
        return False


def select_warehouse(page, name):
    """点击指定仓库名称的切换按钮"""
    target = page.locator("#warehouseDisableDiv a", has_text=name).first
    try:
        target.wait_for(state="visible", timeout=5000)
        current_class = target.get_attribute("class") or ""
        if "toggle_btn_down" in current_class:
            print(f"  [OK] 仓库 '{name}' 已选中")
            return True
        print(f"  [操作] 切换至: {name}")
        target.click()
        page.wait_for_timeout(3000)
        return True
    except Exception as e:
        print(f"  [错误] 选仓库失败 '{name}': {e}")
        return False


def click_export(page, warehouse_name):
    """点击导出按钮，下载文件并重命名"""
    with page.expect_download(timeout=90000) as download_info:
        export_btn = page.locator('a[onclick="exportExcelPage()"]')
        export_btn.click()
        print(f"  [OK] 已点击导出，等待下载...")

    download = download_info.value
    original = download.suggested_filename
    prefix = safe_prefix(warehouse_name)
    new_name = f"{prefix}_{original}"
    target = DOWNLOADS_DIR / new_name
    download.save_as(str(target))
    print(f"  [OK] 已保存: {new_name}")
    return target


def run_generate(inventory_path, warehouse_name):
    """调用 generate_tongtu_import.py 生成导入文件"""
    generate_script = SCRIPT_DIR / "generate_tongtu_import.py"
    prefix = safe_prefix(warehouse_name)
    out_path = OUTPUTS_DIR / f"{prefix}_通途导入_头程运费_其他费用.xlsx"
    print(f"  [信息] 生成导入文件 → {out_path.name}")
    result = subprocess.run(
        [sys.executable, str(generate_script), str(inventory_path), str(out_path)],
        capture_output=True, text=True,
    )
    for line in result.stdout.strip().split("\n"):
        if "共" in line or "SKU" in line or "校验" in line or "错误" in line:
            print(f"    {line.strip()}")
    if result.returncode != 0:
        print(f"  [错误] 生成失败 (exit={result.returncode})")
        if result.stderr:
            print(f"    {result.stderr.strip()}")
        return False
    return True


def run():
    fresh = "--fresh" in sys.argv

    if fresh and PROFILE_DIR.exists():
        print("[信息] --fresh: 清除旧的登录会话...")
        shutil.rmtree(PROFILE_DIR)

    first_run = not PROFILE_DIR.exists()
    if first_run:
        print("[信息] 首次运行，将创建持久化浏览器会话")

    # 确保输出目录存在
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    OUTPUTS_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            accept_downloads=True,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()

        print("[信息] 打开库存结存页面...")
        page.goto(TONGTU_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        if is_already_logged_in(page):
            print("[OK] 检测到已登录会话，自动继续...")
        else:
            if not first_run:
                print("[信息] 登录会话已过期，请重新登录")
            if not wait_for_login(page):
                print("[错误] 登录超时，请重试")
                context.close()
                sys.exit(1)

        # 确保筛选项正确
        print("\n[信息] 确认筛选条件...")
        ensure_toggle(page, "allWarehouseTypeBtn", "全部(非FBA)")
        ensure_toggle(page, "statusBtn", "已启用")

        # 依次导出每个仓库
        total = len(WAREHOUSES)
        for idx, wh in enumerate(WAREHOUSES, 1):
            print(f"\n{'='*50}")
            print(f"[{idx}/{total}] 处理仓库: {wh}")
            print(f"{'='*50}")

            select_warehouse(page, wh)
            inv_path = click_export(page, wh)
            run_generate(inv_path, wh)

        context.close()

    print(f"\n{'='*50}")
    print(f"[完成] 全部 {total} 个仓库已处理！")
    print(f"  下载文件: {DOWNLOADS_DIR}")
    print(f"  导入文件: {OUTPUTS_DIR}")


if __name__ == "__main__":
    run()
