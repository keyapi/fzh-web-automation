#!/usr/bin/env python3
"""
通途库存清单自动导出 + 导入文件生成
用法:
  uv run python tongtu_auto_export.py           # 持久化会话（首次手动登录，后续免登录）
  uv run python tongtu_auto_export.py --fresh    # 强制重新登录（清除已保存的会话）
"""
import os, sys, time, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

TONGTU_URL = "https://erp102.tongtool.com/warehouse/goodsbalance/index.htm?warehouse=1&isFirstInto=1"
TARGET_WAREHOUSE = "FZH-DANEEY-皮壳仓库"
SCRIPT_DIR = Path(__file__).parent
PROFILE_DIR = SCRIPT_DIR / "chrome-profile"
LOGIN_TIMEOUT_SECS = 300


def is_already_logged_in(page):
    """快速检测是否已有有效登录会话"""
    try:
        el = page.locator("#warehouseDisableDiv")
        return el.count() > 0 and el.is_visible()
    except:
        return False


def wait_for_login(page):
    """轮询等待用户完成登录"""
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


def select_warehouse(page, name):
    """点击指定仓库名称的切换按钮"""
    target = page.locator("#warehouseDisableDiv a", has_text=name).first
    try:
        target.wait_for(state="visible", timeout=5000)
        current_class = target.get_attribute("class") or ""
        if "toggle_btn_down" in current_class:
            print(f"[OK] 仓库 '{name}' 已选中，无需切换")
            return True
        print(f"[操作] 切换仓库至 '{name}'...")
        target.click()
        page.wait_for_timeout(3000)
        return True
    except Exception as e:
        print(f"[错误] 选仓库失败: {e}")
        return False


def click_export(page):
    """点击导出Excel按钮并等待下载"""
    with page.expect_download(timeout=90000) as download_info:
        export_btn = page.locator('a[onclick="exportExcelPage()"]')
        export_btn.click()
        print("[OK] 已点击导出，等待下载...")

    download = download_info.value
    target = SCRIPT_DIR / download.suggested_filename
    download.save_as(str(target))
    print(f"[OK] 下载完成: {target.name}")
    return target


def run_generate(inventory_path):
    """调用 generate_tongtu_import.py 生成导入文件"""
    generate_script = SCRIPT_DIR / "generate_tongtu_import.py"
    print("\n[信息] 生成导入文件...")
    exit_code = os.system(f'"{sys.executable}" "{generate_script}" "{inventory_path}"')
    if exit_code != 0:
        print(f"[错误] 生成失败 (exit={exit_code})")
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

        select_warehouse(page, TARGET_WAREHOUSE)
        inventory_path = click_export(page)
        context.close()

        run_generate(inventory_path)
        print("\n[完成] 全部流程结束！")


if __name__ == "__main__":
    run()
