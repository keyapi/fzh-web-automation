#!/usr/bin/env python3
"""
赛狐登录 — ddddocr 自动识别验证码 + Playwright

关键：验证码有时效，必须点击刷新后立刻识别+填入+登录。
"""
import base64
import logging
import os
import sys
import time

from ddddocr_login import DdddocrLogin

# Windows 中文编码
sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

# ── 配置 ──
LOGIN_URL = "https://www.sellfox.com/amzup-web-main/login.html"
SUCCESS_FRAGMENT = "dashboard"  # 登录成功后跳转到 dashboard.html，不是 /home
MAX_ATTEMPTS = 10

USERNAME = os.getenv("SELLFOX_USER", "")
PASSWORD = os.getenv("SELLFOX_PASSWORD", "")

# ── 选择器（2026-07 MCP 探路实测确认）──
SELECTORS = {
    "username": "#username",
    "password": 'input[placeholder*="请输入密码"]',
    "captcha_img": 'img[src^="data:image/jpg"]',
    "captcha_refresh": 'text=点击刷新',
    "captcha_input": 'input[placeholder*="图形验证码"]',
    "login_btn": 'button:has-text("登录")',
    "auto_login_cb": 'text=5天内自动登录',
    "agree_cb": 'label.el-checkbox:has-text("阅读并接受") span.el-checkbox__inner',
}


def login(page) -> bool:
    if not USERNAME or not PASSWORD:
        logger.error("请设置环境变量 SELLFOX_USER 和 SELLFOX_PASSWORD")
        return False

    ocr = DdddocrLogin()
    ocr.set_page(page)

    logger.info("导航到赛狐登录页...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)

    # 已有有效 cookie → 自动跳转 → 无需登录
    if SUCCESS_FRAGMENT in (page.url or ""):
        logger.info("已有登录态，跳过登录（URL: %s）", page.url)
        return True

    # 等登录表单（可能被 cookie 触发 JS 跳转，这里等不到就再检查 URL）
    try:
        page.wait_for_selector('#username', state='attached', timeout=10000)
    except Exception:
        if SUCCESS_FRAGMENT in (page.url or ""):
            logger.info("已有登录态（延迟跳转），跳过登录")
            return True
        raise

    # 勾选"5天内自动登录"
    try:
        ocr.ensure_checkbox(SELECTORS["auto_login_cb"], "5天内自动登录")
    except Exception as e:
        logger.warning("勾选自动登录失败: %s", e)

    # 勾选协议（存在时直接点击 el-checkbox__inner，避免 Target crashed）
    agree_loc = page.locator(SELECTORS["agree_cb"])
    if agree_loc.count() > 0:
        try:
            agree_loc.first.click(timeout=5000)
            logger.info("已勾选: 阅读并接受协议")
        except Exception as e:
            logger.warning("勾选协议失败: %s", e)
    else:
        logger.info("协议勾选框未显示(已有登录态)，跳过")

    # 填入账号密码（只填一次）
    logger.info("填入账号密码...")
    ocr.fill_field(SELECTORS["username"], USERNAME)
    ocr.fill_field(SELECTORS["password"], PASSWORD)

    last_captcha_src = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.info("第 %d/%d 次尝试...", attempt, MAX_ATTEMPTS)

        # 刷新验证码
        if attempt > 1:
            try:
                refresh_el = page.locator('text=点击刷新').first
                if refresh_el.count() > 0:
                    refresh_el.click()
                else:
                    page.locator(SELECTORS["captcha_img"]).first.click()
            except Exception:
                pass
            # 等新图（最多 10s）
            for _ in range(20):
                page.wait_for_timeout(500)
                try:
                    cur = page.evaluate(
                        'document.querySelector(\'img[src^="data:image/jpg"]\')?.src || ""'
                    )
                    if cur and cur != last_captcha_src:
                        break
                except Exception:
                    pass

        # 读图 → OCR（至少4位）
        png = None
        captcha_src = None
        try:
            result = page.evaluate(
                """() => {
                    const img = document.querySelector('img[src^="data:image/jpg"]');
                    if (!img || !img.src) return null;
                    const s = img.src;
                    const i = s.indexOf(',');
                    return { b64: i > 0 ? s.substring(i + 1) : null, src: s };
                }"""
            )
            if result and result.get("b64"):
                png = base64.b64decode(result["b64"])
                captcha_src = result.get("src")
        except Exception:
            pass

        if not png:
            logger.warning("获取验证码失败(URL: %s)，重试...", page.url[:80])
            if SUCCESS_FRAGMENT in (page.url or ""):
                logger.info("登录成功！URL: %s", page.url)
                return True
            # 可能页面状态异常，尝试刷新回登录页
            if "login" not in (page.url or ""):
                page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1000)
            time.sleep(0.5)
            continue

        last_captcha_src = captcha_src

        text = ocr.solve_captcha_from_bytes(png, use_preprocess=False, min_length=4)
        if not text:
            logger.warning("OCR 失败，重试...")
            time.sleep(0.3)
            continue

        # 填入验证码
        try:
            page.locator(SELECTORS["captcha_input"]).first.fill(text)
        except Exception as e:
            logger.warning("填入验证码失败: %s", e)
            time.sleep(0.3)
            continue

        # 点击登录
        try:
            page.locator(SELECTORS["login_btn"]).first.click()
        except Exception as e:
            logger.warning("点击登录失败: %s", e)
            time.sleep(0.3)
            continue

        # 等结果（轮询 URL，最多 5 秒）
        for _ in range(10):
            page.wait_for_timeout(500)
            url = page.url or ""
            if SUCCESS_FRAGMENT in url:
                logger.info("登录成功！URL: %s", url)
                return True

        if SUCCESS_FRAGMENT not in (page.url or ""):
            logger.info("未跳转（验证码错误或过期），刷新重试...")
        time.sleep(0.3)

    logger.error("全部 %d 次尝试失败", MAX_ATTEMPTS)
    return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="sellfox-profile-login",
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        pg = context.pages[0] if context.pages else context.new_page()

        success = login(pg)
        print("登录成功！" if success else "登录失败")
        if success:
            pg.wait_for_timeout(3000)

        context.close()
        sys.exit(0 if success else 1)
