#!/usr/bin/env python3
"""
通途库存清单自动导出 + 导入文件生成
用法:
  uv run python tongtu_auto_export.py           # 自动启动Chromium
  uv run python tongtu_auto_export.py --cdp      # 连接已有Chrome (免登录)
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

TONGTU_URL = "https://erp102.tongtool.com/warehouse/goodsbalance/index.htm?warehouse=1&isFirstInto=1"
TARGET_WAREHOUSE = "FZH-DANEEY-皮壳仓库"
SCRIPT_DIR = Path(__file__).parent

# 登录最长等待时间
LOGIN_TIMEOUT_SECS = 300


def wait_for_login(page):
    """轮询等待用户完成登录（检测仓库选择器是否出现）"""
    print(f"\n[信息] 请在浏览器中登录通途...")
    print(f"[信息] 脚本将自动检测登录状态（最长等待 {LOGIN_TIMEOUT_SECS} 秒）")
    for i in range(0, LOGIN_TIMEOUT_SECS, 3):
        time.sleep(3)
        try:
            # 登录成功后仓库选择器会出现
            el = page.locator("#warehouseDisableDiv")
            if el.count() > 0 and el.is_visible():
                print("[OK] 检测到登录成功！自动继续...")
                page.wait_for_timeout(1000)
                return True
        except:
            pass
        if i % 15 == 0 and i > 0:
            print(f"  等待登录中... ({i}/{LOGIN_TIMEOUT_SECS}s)")
    return False


def select_warehouse(page, name):
    """点击指定仓库名称的切换按钮"""
    # 仓库按钮在 div#coll 里，是 <a class="toggle_btn"> 或 <a class="toggle_btn_down">
    target = page.locator("#warehouseDisableDiv a", has_text=name).first
    try:
        target.wait_for(state="visible", timeout=5000)
        current_class = target.get_attribute("class") or ""
        if "toggle_btn_down" in current_class:
            print(f"[OK] 仓库 '{name}' 已选中，无需切换")
            return True
        print(f"[操作] 切换仓库至 '{name}'...")
        target.click()
        page.wait_for_timeout(3000)  # 等待页面刷新数据
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
    mode = "cdp" if "--cdp" in sys.argv else "launch"

    with sync_playwright() as p:
        if mode == "cdp":
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
        else:
            print("[信息] 启动 Playwright Chromium...")
            browser = p.chromium.launch(headless=False)
            ctx = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 800})
            page = ctx.new_page()

        print("[信息] 打开库存结存页面...")
        page.goto(TONGTU_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        if not wait_for_login(page):
            print("[错误] 登录超时，请重试")
            browser.close()
            sys.exit(1)

        select_warehouse(page, TARGET_WAREHOUSE)
        inventory_path = click_export(page)
        browser.close()

        run_generate(inventory_path)
        print("\n[完成] 全部流程结束！")


if __name__ == "__main__":
    run()
