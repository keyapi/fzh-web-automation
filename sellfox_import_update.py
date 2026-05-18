#!/usr/bin/env python3
"""
赛狐商品导入更新 — 最稳方案（全浏览器点击 + 已知成功文件）

用法:
  uv run python sellfox_import_update.py

策略:
  - 先用用户手动验证过的成功文件测试导入流程
  - 全量浏览器点击（不跳过任何步骤）
  - 验证弹窗"导入完成"文字
"""

import time, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

SCRIPT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = SCRIPT_DIR / "sellfox-profile"
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"

LOGIN_URL = "https://www.sellfox.com/amzup-web-main/login.html"
PAGE_URL  = "https://www.sellfox.com/amzup-web-main/web/commodity/index.html"

# 用户已验证成功上传的文件
WORKING_FILE = DOWNLOADS_DIR / "working_import.xlsx"

# ── 登录 ────────────────────────────────────────────────────

def is_logged_in(page):
    try:
        return ("login" not in page.url
                and page.locator("text=克勇").first.is_visible())
    except:
        return False

def wait_for_login(page):
    print("  请在浏览器中手动登录...")
    for _ in range(150):
        time.sleep(2)
        try:
            if page.locator("text=克勇").first.is_visible():
                return True
        except:
            pass
        if "login" not in page.url and "sellfox" in page.url:
            return True
    return False

# ── 导入流程 ────────────────────────────────────────────────

def do_import(page, file_path):
    """
    最稳方案: 全浏览器点击
    1. 打开导入下拉 → 选"导入更新商品"
    2. 弹窗中勾选"规格信息"
    3. 点击"添加文件" → 文件选择器 → 选文件
    4. 点击"导入" → 等待完成
    """
    # 1. 打开导入下拉
    print("  1. 展开导入下拉菜单...")
    page.evaluate(
        "(() => { [...document.querySelectorAll('button')]"
        ".find(b => b.textContent.trim() === '导入')?.click(); })()"
    )
    page.wait_for_timeout(800)

    # 2. 选"导入更新商品"
    print("  2. 选择 导入更新商品...")
    page.evaluate(
        "(() => { [...document.querySelectorAll('.el-dropdown-menu__item')]"
        ".find(i => i.textContent.trim() === '导入更新商品')?.click(); })()"
    )
    page.wait_for_timeout(3000)

    # 3. 滚动弹窗 + 勾选规格信息
    print("  3. 勾选 规格信息...")
    page.evaluate(
        "(() => { const b = document.querySelector('.el-dialog__body');"
        " if (b) b.scrollTop = b.scrollHeight; })()"
    )
    page.wait_for_timeout(500)
    page.locator(
        '.el-checkbox:has(.el-checkbox__label:text-is("规格信息"))'
    ).click()
    page.wait_for_timeout(500)

    # 4. 上传文件
    print(f"  4. 上传文件: {file_path.name}...")
    with page.expect_file_chooser() as fc:
        page.locator(
            '.el-button--primary:has-text("添加文件")'
        ).click()
    fc.value.set_files(str(file_path.resolve()))
    page.wait_for_timeout(800)

    # 5. 点导入
    print("  5. 点击导入...")
    page.get_by_role("button", name="导入", exact=True).click()

    # 6. 等待完成
    print("  6. 等待处理...")
    for sec in range(120):
        text = page.evaluate(
            "(() => { const d = [...document.querySelectorAll('.el-dialog__wrapper')]"
            ".find(x => x.getBoundingClientRect().width > 0);"
            " return d?.textContent?.trim()?.substring(0, 200) || ''; })()"
        )
        if "导入完成" in text:
            print(f"     [OK] {text.strip()}")
            return True
        if "失败" in text and "成功" not in text:
            print(f"     [FAIL] {text.strip()}")
            return False
        if sec % 15 == 0 and sec > 0:
            print(f"     等待中... ({sec}s)")
        time.sleep(1)

    print("     [WARN] 超时 120s")
    return False


def close_dialog(page):
    page.evaluate(
        "(() => { const d = [...document.querySelectorAll('.el-dialog__wrapper')]"
        ".find(x => x.getBoundingClientRect().width > 0);"
        " d?.querySelector('.el-dialog__headerbtn')?.click(); })()"
    )


def main():
    DOWNLOADS_DIR.mkdir(exist_ok=True)

    if not WORKING_FILE.exists():
        print(f"错误: 找不到 {WORKING_FILE}")
        print("请先确保已知成功文件存在")
        sys.exit(1)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            accept_downloads=True,
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # 登录
        print("[Start] 打开商品列表页...")
        page.goto(PAGE_URL, timeout=60000)
        page.wait_for_timeout(5000)

        if is_logged_in(page):
            print("       已登录")
        else:
            page.goto(LOGIN_URL, timeout=30000)
            if not wait_for_login(page):
                ctx.close(); return
            page.goto(PAGE_URL, timeout=60000)
            page.wait_for_timeout(8000)

        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # 导入
        print("[Import] 开始导入流程...")
        ok = do_import(page, WORKING_FILE)
        close_dialog(page)

        if ok:
            print("\n[Done] 导入成功！")
        else:
            print("\n[Done] 导入可能未完成，请手动检查")

        ctx.close()


if __name__ == "__main__":
    main()
