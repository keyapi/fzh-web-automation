#!/usr/bin/env python3
"""
赛狐库存明细自动导出（演示 + API 双模式）

用法:
  uv run python sellfox_auto_export.py            # 浏览器演示模式（可见点击）
  uv run python sellfox_auto_export.py --api       # API 模式（请求直接调 API）
  uv run python sellfox_auto_export.py --headless  # 浏览器无头模式（后台运行）
  uv run python sellfox_auto_export.py --fresh     # 强制重新登录
  uv run python sellfox_auto_export.py --export-cookies  # 导出 cookies 供 API 使用

两种模式对比:
  | 浏览器模式 | 打开可见浏览器，能看到每一步点击          | 适合演示、调试 |
  | API 模式   | 直接调 HTTP API，速度快 10x，不依赖 DOM  | 适合批量生产    |

输出目录:
  downloads/    原始下载的 Excel
  output/       合并后的文件
  sellfox-profile/  持久化登录会话 (gitignore)
"""

import subprocess, sys, time, shutil, json, os
from pathlib import Path
from playwright.sync_api import sync_playwright
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = SCRIPT_DIR / "sellfox-profile"
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
OUTPUT_DIR = SCRIPT_DIR / "output"
LOGIN_TIMEOUT = 300

LOGIN_URL = "https://www.sellfox.com/amzup-web-main/login.html"
PAGE_URL = "https://www.sellfox.com/amzup-web-main/web/warehouse/detailed/index.html"
REPORT_URL = "https://www.sellfox.com/amzup-web-main/amzup-web-vue3?amzup-web-vue3=%2Fvue3%2Fweb%2Fv3%2Freport-center%2Findex.html"

EXPORT_API = "https://www.sellfox.com/api/warehouseManage/warehouseItem-export.json"
TASK_LIST_API = "https://www.sellfox.com/api/report/center/task/pageList.json"
DOWNLOAD_API = "https://www.sellfox.com/api/report/center/task/download.json"
PAGE_LIST_API = "https://www.sellfox.com/api/gw/sellfox/sellfox-warehouse/sellfox/warehouse/item/warehouseItemPageList"
PAGE_COUNT_API = "https://www.sellfox.com/api/gw/sellfox/sellfox-warehouse/sellfox/warehouse/item/warehouseItemPageCount"

HEAD_FIELD_API = "https://www.sellfox.com/api/excel/getHeadField.json"


# ─── 工具函数 ───────────────────────────────────────────────

def is_logged_in(page):
    """MCP 实测: 登录后 URL 不再含 'login'，且 stock 页有导出图标"""
    url = page.url
    if "login" in url:
        return False
    try:
        return page.locator(".icon_sf_download").first.is_visible()
    except:
        return "login" not in url  # fallback: URL 变了就算已登录


def wait_for_login(page):
    """MCP 实测: 轮询检测 URL 是否已离开登录页"""
    print(f"\n请在浏览器中登录赛狐（最长等待 {LOGIN_TIMEOUT}s）...")
    print("  登录页: 输入用户名/密码/验证码 → 拼图滑块 → 点登录")
    for i in range(0, LOGIN_TIMEOUT, 3):
        time.sleep(3)
        url = page.url
        if "login" not in url and url != "about:blank":
            print("检测到登录成功！（URL 已跳离登录页）")
            page.wait_for_timeout(2000)
            return True
        if i % 15 == 0 and i > 0:
            print(f"  等待登录中... ({i}/{LOGIN_TIMEOUT}s) 当前URL: {url[:80]}")
    return False


def ensure_page_ready(page):
    """等待页面 JS 渲染完成，关闭残留弹窗"""
    page.wait_for_timeout(5000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)


# ─── 浏览器模式 ─────────────────────────────────────────────

def browser_export_flow(page):
    """MCP 实测: 点击导出图标 → 弹窗确定 → 等通知 → 立即下载"""
    # 1. 点击导出图标 (同 MCP: browser_click .icon_sf_download)
    print("  1. 点击导出图标...")
    page.locator(".icon_sf_download.f_18").first.click()
    page.wait_for_timeout(2000)

    # 2. 弹窗出现 → 点击确定（MCP: getByRole last + browser_evaluate click）
    print("  2. 弹窗出现 → 点确定（导出 44 字段）")
    page.evaluate("""
      const btns = document.querySelectorAll('.el-dialog__footer button, .dcm button');
      const ok = [...btns].find(b => b.textContent.trim() === '确定' && b.offsetParent);
      if (ok) ok.click();
    """)
    page.wait_for_timeout(3000)

    # 3. 等待后台生成 → 通知出现 → 立即下载 (同 MCP)
    for _ in range(60):
        try:
            dl_btn = page.locator('button:has-text("立即下载")')
            if dl_btn.count() > 0:
                print("  3. 文件已生成 → 点击立即下载")
                # MCP: waitForEvent('download') + click 立即下载
                with page.expect_download(timeout=30000) as dl_info:
                    page.evaluate("""
                      const btns = document.querySelectorAll('button');
                      const dl = [...btns].find(b => b.textContent.includes('立即下载'));
                      if (dl) dl.click();
                    """)
                download = dl_info.value
                suggested = download.suggested_filename
                target = DOWNLOADS_DIR / suggested
                download.save_as(str(target))
                print(f"  4. 下载完成: {suggested} ({target.stat().st_size / 1024:.0f} KB)")
                return target
        except:
            pass
        time.sleep(2)

    print("  [失败] 导出超时（文件未在 120s 内生成）")
    return None


def run_browser(headless=False):
    """浏览器模式：先登录页 → 用户登录 → 仓库页 → 导出。MCP 实测流程。"""
    first_run = not PROFILE_DIR.exists()
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        print(f"[启动] 浏览器持久化目录: {PROFILE_DIR}")
        print(f"[启动] {'首次运行' if first_run else '已有会话(免登录)'}")

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            accept_downloads=True,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()

        # Step 1: 先到仓库页，看是否需要登录
        print("[1/4] 导航到库存明细页...")
        page.goto(PAGE_URL, timeout=60000)
        page.wait_for_timeout(5000)
        print(f"      当前URL: {page.url[:80]}")

        if is_logged_in(page):
            print("[OK] 已登录，跳过登录步骤\n")
        else:
            print(f"[!] 未登录 (URL={page.url[:60]}) → 打开登录页")
            page.goto(LOGIN_URL, timeout=30000)
            print(f"      登录页已打开，请登录...")
            if not wait_for_login(page):
                context.close()
                return False
            print(f"[!] 登录完成 → cookie 已自动保存到 {PROFILE_DIR}")
            print(f"[!] 下次运行将免登录！")

        # Step 2: 导航到仓库页并等待渲染
        print("[2/4] 跳转库存明细页...")
        page.goto(PAGE_URL, timeout=60000)
        print(f"      URL: {page.url[:80]}")
        print(f"      等待 SPA 渲染 (8s)...")
        page.wait_for_timeout(8000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        print(f"      渲染完成")

        # Step 3: 导出
        print("[3/4] 开始导出...")
        result = browser_export_flow(page)

        context.close()

        if result:
            print(f"[4/4] 完成! 文件: {result}")
        return bool(result)


# ─── API 模式 ───────────────────────────────────────────────

def get_api_cookies():
    """从 sellfox-profile 提取 cookies 用于 API 调用"""
    if not PROFILE_DIR.exists():
        print("sellfox-profile/ 不存在，请先用浏览器模式登录一次")
        return None

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=True,
        )
        cookies = context.cookies()
        context.close()

    sellfox_cookies = [c for c in cookies if "sellfox" in c.get("domain", "")]
    if not sellfox_cookies:
        print("未找到 sellfox cookies，请先用浏览器模式登录")
        return None

    result = {}
    for c in sellfox_cookies:
        result[c["name"]] = c["value"]

    print(f"提取到 {len(result)} 个 sellfox cookies")
    return result


def api_export_flow(cookies):
    """通过 HTTP API 完成导出（不打开浏览器）"""
    import requests

    ts = datetime.now().strftime("%Y-%m-%d")
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value, domain="www.sellfox.com")

    # Step 1: 使用已知的 44 个默认导出字段（MCP 探索验证）
    print("  1. 使用默认 44 个导出字段...")
    fields = [
        "commodityName","commoditySku","fnSku","mskuList","spu","spuName",
        "identificationCode","brandName","fullName","stateName",
        "commodityAttr","commodityAttrCn","model","platform","shopName",
        "shopNames","country","warehouse","productDevNames","commodityDevName",
        "shelfInfos","cartonQty","cartonNum","stockPlan","stockWait",
        "stockInspect","waitUpShelfNum","stockProcessing","stockOccupyAll",
        "stockAvailable","expectedAvailableQuantity","stockDefective",
        "stockAllNum","safeStock","perPurchase","perFee","perInventoryCost",
        "onWayPurchase","onWayFee","totalOnWayCostStock","totalPurchase",
        "totalFee","inventoryCost","totalCostStockSum","updateTime"
    ]
    print(f"     {len(fields)} 个字段")

    # Step 2: 触发导出
    print("  2. 触发异步导出...")
    export_body = {
        "orderField": "", "orderValue": "", "warehouseIds": "",
        "fullCid": "", "commodityAttrValueIds": "", "isExclusive": "",
        "attributeValue": None, "labelQuery": 0, "labelIdList": [],
        "searchType": "fuzzy", "searchField": "", "searchValue": "",
        "productDevIds": "", "commodityDevIds": "", "tableType": "1",
        "commodityCategories": "", "brandIds": [], "state": "",
        "shopInfoList": [], "includeList": fields, "isHidden": False,
        "dangerStock": False, "pageNo": 1, "pageSize": 20,
    }
    r = session.post(EXPORT_API, json=export_body,
                     headers={"content-type": "application/json"})
    if r.json().get("code") != 0:
        print(f"  [失败] {r.json()}")
        return None
    print(f"     OK")

    # Step 3: 轮询任务列表
    print("  3. 等待后台生成文件...")
    task_id = None
    for attempt in range(60):
        r = session.post(TASK_LIST_API, json={
            "status": "", "dateType": "createTime", "reportName": "",
            "createTimeStart": ts, "createTimeEnd": ts,
            "pageSize": 5, "pageNo": 1, "tabs": 1,
        })
        tasks = r.json().get("data", {}).get("rows", [])
        for t in tasks:
            if "仓库" in t.get("module", "") and t.get("status") == "COMPLETE":
                task_id = t["id"]
                break
        if task_id:
            print(f"     taskId={task_id}, 耗时 ~{attempt * 2}s")
            break
        time.sleep(2)

    if not task_id:
        print("  [失败] 任务未完成")
        return None

    # Step 4: 下载
    print("  4. 获取下载链接...")
    r = session.post(DOWNLOAD_API, json={"ids": [task_id]})
    cos_url = r.json().get("data", [None])[0]
    if not cos_url:
        print("  [失败] 无下载链接")
        return None

    print("  5. 下载文件...")
    r = requests.get(cos_url)
    filename = f"WarehouseItem_{ts}.xlsx"
    output_path = DOWNLOADS_DIR / filename
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    output_path.write_bytes(r.content)
    print(f"  [OK] {filename} ({len(r.content) / 1024:.0f} KB)")
    return output_path


def run_api():
    """API 模式：不打开浏览器"""
    cookies = get_api_cookies()
    if not cookies:
        print("请先用浏览器模式登录: uv run python sellfox_auto_export.py")
        return False

    print("API 模式：直接调接口...")
    result = api_export_flow(cookies)
    if result:
        print(f"\n文件: {result}")
    return bool(result)


# ─── Cookie 导出 ────────────────────────────────────────────

def export_cookies_cmd():
    """导出 sellfox cookies 为 JSON"""
    cookies = get_api_cookies()
    if not cookies:
        return

    out_path = SCRIPT_DIR / "sellfox_cookies.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)
    print(f"已导出 {len(cookies)} 个 cookie → {out_path}")


# ─── 主入口 ─────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if "--export-cookies" in args:
        export_cookies_cmd()
        return

    fresh = "--fresh" in args
    use_api = "--api" in args
    headless = "--headless" in args

    if fresh and PROFILE_DIR.exists():
        print("--fresh: 清除旧登录会话...")
        shutil.rmtree(PROFILE_DIR)

    if use_api:
        print("=" * 50)
        print("赛狐库存导出 — API 模式")
        print("=" * 50)
        success = run_api()
    else:
        print("=" * 50)
        mode = "无头" if headless else "演示"
        print(f"赛狐库存导出 — 浏览器{mode}模式")
        print("=" * 50)
        success = run_browser(headless=headless)

    if success:
        print("\n完成！")
    else:
        print("\n失败，请检查日志。")
        sys.exit(1)


if __name__ == "__main__":
    main()
