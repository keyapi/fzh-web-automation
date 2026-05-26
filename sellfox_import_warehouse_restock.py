#!/usr/bin/env python3
"""
sellfox_import_warehouse_restock.py
赛狐 海外仓备货单 一键导入 — 自动上传一个或多个备货单文件

用法:
  uv run python sellfox_import_warehouse_restock.py                         # 导入 restock/ 下所有文件
  uv run python sellfox_import_warehouse_restock.py file1.xlsx file2.xlsx    # 导入指定文件
  uv run python sellfox_import_warehouse_restock.py --fresh                  # 强制重新登录

流程: 登录→添加单据→导入海外仓备货单→添加文件→上传→导入→等结果→读结果→关闭→下一个

注意: 单个备货单不超过500条，文件需预拆批次。
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

SCRIPT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = SCRIPT_DIR / "sellfox-profile"
DEFAULT_IMPORT_DIR = SCRIPT_DIR / "restock"

PAGE_URL = "https://www.sellfox.com/amzup-web-main/web/warehouse/stockOrder/index.html"
LOGIN_URL = "https://www.sellfox.com/amzup-web-main/login.html"
LOGIN_TIMEOUT = 300


def wait_for_login(page):
    print(f"\n请在浏览器中登录赛狐（最长等待 {LOGIN_TIMEOUT}s）...")
    for i in range(0, LOGIN_TIMEOUT, 2):
        time.sleep(2)
        url = page.url
        if "login" not in url and url != "about:blank" and "sellfox" in url:
            print(f"✓ 登录成功")
            page.wait_for_timeout(1000)
            return True
        try:
            if page.locator('text=克勇').first.is_visible():
                print("✓ 登录成功")
                return True
        except:
            pass
    return False


def is_logged_in(page):
    """检测是否已登录 — 看页面是否有「添加单据」按钮。"""
    url = page.url
    if "login" in url or url == "about:blank":
        return False
    try:
        return page.locator("button:has-text(\"添加单据\")").first.is_visible(timeout=3000)
    except:
        return False


def _click_by_text(page, text: str, container_sel: str = "button"):
    """用 JS evaluate 点击匹配文字的按钮，绕过 Playwright has_text 的编码问题。"""
    escaped = text.replace("'", "\\'")
    page.evaluate(f"""
        (() => {{
            for (const el of document.querySelectorAll('{container_sel}')) {{
                if (el.textContent && el.textContent.includes('{escaped}')) {{
                    el.click();
                    return;
                }}
            }}
        }})()
    """)


def import_one_file(page, filepath: Path) -> dict:
    """导入一个备货单文件。返回 {file, success_count, fail_count, error_file}。"""
    print(f"\n{'='*50}")
    print(f"导入: {filepath.name}")
    print(f"{'='*50}")

    page.goto(PAGE_URL, timeout=30000)
    page.wait_for_timeout(5000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    # 关闭可能的公告弹窗
    page.evaluate("""
        document.querySelectorAll('.el-dialog__headerbtn, [class*="close"]').forEach(b => {
            if (b.offsetParent !== null) b.click();
        });
    """)
    page.wait_for_timeout(500)

    # Step 1: 点击"添加单据"
    print("  添加单据...")
    _click_by_text(page, "添加单据", "button")
    page.wait_for_timeout(800)

    # Step 2: 点击"导入海外仓备货单"
    print("  导入海外仓备货单...")
    page.evaluate("""
        document.querySelectorAll('.el-dropdown-menu__item').forEach(item => {
            if (item.textContent && item.textContent.includes('导入海外仓备货单')) item.click();
        });
    """)
    page.wait_for_timeout(800)

    # Step 3: 等待弹窗渲染 → 点击"添加文件"
    print("  添加文件...")
    page.wait_for_timeout(1500)
    add_file_btn = page.locator(".el-dialog button:has-text(\"添加文件\")").first
    add_file_btn.wait_for(state="visible", timeout=10000)
    add_file_btn.click()

    # Step 4: 上传文件
    print(f"  上传: {filepath.name}")
    file_chooser = page.wait_for_event("filechooser", timeout=10000)
    file_chooser.set_files(str(filepath))
    page.wait_for_timeout(1000)

    # Step 5: 点击"导入"
    print("  导入中...")
    page.evaluate("""
        (() => {
            const wrappers = document.querySelectorAll('.el-dialog__wrapper');
            for (const d of wrappers) {
                if (window.getComputedStyle(d).display !== 'none') {
                    for (const btn of d.querySelectorAll('button')) {
                        if (btn.textContent.trim() === '导入' && !btn.disabled) {
                            btn.click();
                            return;
                        }
                    }
                }
            }
        })()
    """)

    # Step 6: 轮询导入结果（赛狐后台处理，500条约需30s）
    result_text = None
    for attempt in range(40):
        time.sleep(2)
        try:
            dialog_text = page.locator('.el-dialog__wrapper').first.text_content(timeout=1000) or ""
            if "导入完成" in dialog_text:
                result_text = dialog_text
                break
        except:
            pass

    if not result_text:
        print("  [!] 超时未收到导入结果")
        return {"file": filepath.name, "success": 0, "fail": "timeout"}

    # Step 7: 解析结果
    import re
    success_match = re.search(r'成功(\d+)条', result_text)
    fail_match = re.search(r'失败(\d+)条', result_text)
    success_count = int(success_match.group(1)) if success_match else 0
    fail_count = int(fail_match.group(1)) if fail_match else 0

    error_file = None
    if fail_count > 0:
        print(f"  [!] 成功{success_count}条, 失败{fail_count}条 — 下载错误报告...")
        page.evaluate("""
            (() => {
                for (const el of document.querySelectorAll('*')) {
                    if (el.textContent.trim() === '下载查看失败原因') {
                        el.click();
                        return;
                    }
                }
            })()
        """)
        page.wait_for_timeout(2000)
        # Check downloads dir for latest error file
        downloads = sorted(Path(DEFAULT_IMPORT_DIR).parent.glob(".playwright-mcp/导入失败记录*.xlsx"),
                          key=lambda f: f.stat().st_mtime)
        if downloads:
            error_file = str(downloads[-1])
    else:
        print(f"  [OK] 成功{success_count}条")

    # Step 8: 关闭弹窗
    page.evaluate("""
        document.querySelectorAll('.el-dialog__wrapper button').forEach(btn => {
            if (btn.textContent.trim() === '关闭') btn.click();
        });
    """)
    page.wait_for_timeout(500)

    return {
        "file": filepath.name,
        "success": success_count,
        "fail": fail_count,
        "error_file": error_file,
    }


def main():
    fresh = "--fresh" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--fresh"]

    files = []
    if args and not args[0].startswith("--"):
        files = [Path(a).resolve() for a in args]
    else:
        files = sorted(
            f for f in DEFAULT_IMPORT_DIR.glob("*.xlsx")
            if not f.name.startswith("~$")
        )

    if not files:
        print("未找到要导入的 xlsx 文件。")
        print("用法: uv run python sellfox_import_warehouse_restock.py [file1.xlsx ...]")
        print("     或放入 restock/ 目录下自动选取")
        return

    print(f"\n赛狐 海外仓备货单 一键导入")
    print(f"文件数: {len(files)}")
    for f in files:
        print(f"  - {f.name}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()

        page.goto(PAGE_URL, timeout=30000)
        page.wait_for_timeout(3000)

        if is_logged_in(page):
            print("\n[OK] 已登录")
        elif fresh:
            page.goto(LOGIN_URL, timeout=30000)
            if not wait_for_login(page):
                context.close()
                return
        else:
            print("\n[!] 未登录 → 打开登录页")
            page.goto(LOGIN_URL, timeout=30000)
            if not wait_for_login(page):
                context.close()
                return

        results = []
        for fp in files:
            if not fp.exists():
                print(f"\n[跳过] 文件不存在: {fp}")
                results.append({"file": fp.name, "success": 0, "fail": "not found"})
                continue
            r = import_one_file(page, fp)
            results.append(r)

        print(f"\n{'='*50}")
        print("导入汇总")
        print(f"{'='*50}")
        total_success = 0
        total_fail = 0
        for r in results:
            status = f"✓ 成功{r['success']}" if not isinstance(r.get('fail'), int) or r['fail'] == 0 else f"✗ 失败{r['fail']}"
            print(f"  {status}  {r['file']}")
            if isinstance(r.get('success'), int):
                total_success += r['success']
            if isinstance(r.get('fail'), int):
                total_fail += r['fail']
        print(f"\n合计: 成功{total_success}条, 失败{total_fail}条")
        if any(r.get('error_file') for r in results):
            print(f"错误报告已下载到 .playwright-mcp/ 目录")
        print(f"\n关闭浏览器...")
        context.close()


if __name__ == "__main__":
    main()
