#!/usr/bin/env python3
"""
sellfox_import_other_outbound.py
赛狐 其他出库 一键导入 — 自动上传一个或多个出库文件

用法:
  uv run python sellfox_import_other_outbound.py                     # 导入 outbound/ 下所有文件
  uv run python sellfox_import_other_outbound.py file1.xlsx file2.xlsx  # 导入指定文件
  uv run python sellfox_import_other_outbound.py --fresh               # 强制重新登录

流程: 导航→添加单据→导入出库单→添加文件→上传→导入→关闭→刷新→下一个

注意: 导入后需手动去赛狐页面逐个"确认出库"（赛狐无批量确认功能）
"""
import sys
import time
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

SCRIPT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = SCRIPT_DIR / "sellfox-profile"
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
DEFAULT_IMPORT_DIR = SCRIPT_DIR / "outbound"

PAGE_URL = "https://www.sellfox.com/amzup-web-main/web/warehouse/otherOut/index.html"
LOGIN_URL = "https://www.sellfox.com/amzup-web-main/login.html"
LOGIN_TIMEOUT = 300


def wait_for_login(page):
    """等待用户手动登录。"""
    print(f"\n请在浏览器中登录赛狐（最长等待 {LOGIN_TIMEOUT}s）...")
    for i in range(0, LOGIN_TIMEOUT, 2):
        time.sleep(2)
        url = page.url
        if "login" not in url and url != "about:blank" and "sellfox" in url:
            print(f"✓ 检测到登录成功！")
            page.wait_for_timeout(1000)
            return True
        try:
            if page.locator('text=克勇').first.is_visible():
                print("✓ 检测到登录成功！(用户菜单可见)")
                return True
        except:
            pass
    return False


def is_logged_in(page):
    """检测是否已登录。"""
    url = page.url
    if "login" in url:
        return False
    try:
        return page.locator(".icon_sf_download").first.is_visible() or "login" not in url
    except:
        return "login" not in url


def import_one_file(page, filepath: Path) -> bool:
    """导入一个出库文件。返回是否成功。"""
    print(f"\n{'='*50}")
    print(f"导入: {filepath.name}")
    print(f"{'='*50}")

    # 先刷新页面确保干净状态
    print("  刷新页面...")
    page.goto(PAGE_URL, timeout=30000)
    page.wait_for_timeout(3000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # Step 1: 点击"添加单据"
    print("  点击 添加单据...")
    add_btn = page.locator('button', has_text="添加单据").first
    add_btn.wait_for(state="visible", timeout=10000)
    add_btn.click()
    page.wait_for_timeout(600)

    # Step 2: 点击"导入出库单"
    print("  点击 导入出库单...")
    import_item = page.locator('.el-dropdown-menu__item', has_text="导入出库单").first
    import_item.wait_for(state="attached", timeout=5000)
    # el-dropdown items may be hidden until hover — try evaluate fallback
    try:
        import_item.click(timeout=3000)
    except:
        page.evaluate("""
            document.querySelectorAll('.el-dropdown-menu__item').forEach(item => {
                if (item.textContent.includes('导入出库单')) item.click();
            });
        """)
    page.wait_for_timeout(800)

    # Step 3: 等待导入弹窗出现
    print("  等待导入弹窗...")
    page.wait_for_timeout(500)

    # Step 4: 点击"添加文件"打开文件选择器
    print("  点击 添加文件...")
    add_file_btn = page.locator('.el-dialog button', has_text="添加文件").first
    add_file_btn.wait_for(state="visible", timeout=5000)
    add_file_btn.click()
    page.wait_for_timeout(500)

    # Step 5: 上传文件
    print(f"  上传文件: {filepath}")
    file_chooser = page.wait_for_event("filechooser", timeout=10000)
    file_chooser.set_files(str(filepath))
    page.wait_for_timeout(1000)

    # Step 6: 点击"导入"
    print("  点击 导入...")
    import_btn = page.locator('.el-dialog button', has_text="导入").last
    import_btn.wait_for(state="visible", timeout=5000)
    import_btn.click()

    # Step 7: 等待导入结果
    print("  等待导入结果...")
    page.wait_for_timeout(3000)
    # 赛狐会在弹窗里显示结果（成功X条/失败Y条）
    try:
        result = page.locator('.el-dialog .el-message, .el-dialog .el-alert').first
        if result.is_visible(timeout=3000):
            print(f"  结果: {result.text_content()}")
    except:
        pass

    # Step 8: 关闭弹窗
    print("  关闭弹窗...")
    try:
        close_btn = page.locator('.el-dialog button', has_text="关闭").first
        close_btn.click(timeout=3000)
    except:
        # JS fallback
        page.evaluate("""
            document.querySelectorAll('.el-dialog__wrapper button').forEach(btn => {
                if (btn.textContent.trim() === '关闭') btn.click();
            });
        """)
    page.wait_for_timeout(500)

    # Step 9: 刷新页面查看结果
    print("  刷新页面查看结果...")
    page.goto(PAGE_URL, timeout=30000)
    page.wait_for_timeout(3000)

    print(f"  完成!")
    return True


def main():
    fresh = "--fresh" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--fresh"]

    # 确定要导入的文件列表
    if args and not args[0].startswith("--"):
        files = [Path(a).resolve() for a in args]
    else:
        files = sorted(
            f for f in DEFAULT_IMPORT_DIR.glob("*.xlsx")
            if not f.name.startswith("~$")
        )

    if not files:
        print("未找到要导入的 xlsx 文件。")
        print("用法: uv run python sellfox_import_other_outbound.py [file1.xlsx ...]")
        print("     或放入 outbound/ 目录下自动选取")
        return

    print(f"\n赛狐 其他出库 一键导入")
    print(f"文件数: {len(files)}")
    for f in files:
        print(f"  - {f.name}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()

        # 登录检测
        page.goto(PAGE_URL, timeout=30000)
        page.wait_for_timeout(3000)

        if is_logged_in(page):
            print("\n[OK] 已登录，跳过登录步骤")
        elif fresh:
            print("\n[fresh] 强制重新登录...")
            page.goto(LOGIN_URL, timeout=30000)
            if not wait_for_login(page):
                print("[失败] 登录超时")
                context.close()
                return
        else:
            print("\n[!] 未登录 → 打开登录页")
            page.goto(LOGIN_URL, timeout=30000)
            if not wait_for_login(page):
                print("[失败] 登录超时")
                context.close()
                return

        # 逐个导入
        results = []
        for fp in files:
            if not fp.exists():
                print(f"\n[跳过] 文件不存在: {fp}")
                results.append((fp.name, False))
                continue
            ok = import_one_file(page, fp)
            results.append((fp.name, ok))

        # 汇总
        print(f"\n{'='*50}")
        print("导入汇总")
        print(f"{'='*50}")
        for name, ok in results:
            print(f"  {'✓' if ok else '✗'} {name}")
        print(f"\n注意: 导入后需手动去赛狐页面确认出库")
        print(f"关闭浏览器...")
        context.close()


if __name__ == "__main__":
    main()
