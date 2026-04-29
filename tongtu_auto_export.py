#!/usr/bin/env python3
"""
通途库存清单自动导出
"""
import os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

TONGTU_URL = "https://erp102.tongtool.com/warehouse/goodsbalance/index.htm?warehouse=1&isFirstInto=1"
SCRIPT_DIR = Path(__file__).parent


def run():
    mode = "launch" if "--launch" in sys.argv else "cdp"

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

        print("\n" + "=" * 50)
        print("【操作】1.登录 2.选仓库 3.切回终端按回车")
        print("=" * 50)
        input("按回车继续...")

        with page.expect_download(timeout=90000) as download_info:
            export_btn = page.locator('a[onclick="exportExcelPage()"]')
            export_btn.click()
            print("[OK] 已点击导出，等待下载...")

        download = download_info.value
        target = SCRIPT_DIR / download.suggested_filename
        download.save_as(str(target))
        print(f"[OK] 下载完成: {target.name}")
        browser.close()

        print("\n[信息] 生成导入文件...")
        os.system(f'uv run python "{SCRIPT_DIR / "generate_tongtu_import.py"}" "{target}"')
        print("\n[完成] 全部流程结束！")


if __name__ == "__main__":
    run()
