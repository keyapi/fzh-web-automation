#!/usr/bin/env python3
"""
通途登录 — ddddocr 自动识别验证码 + Playwright
"""
import logging
import os
import sys

from ddddocr_login import DdddocrLogin

logger = logging.getLogger(__name__)

# ── 配置 ──
LOGIN_URL = (
    "https://passport.tongtool.com/"
    "?u=http%3A%2F%2Ferp102.tongtool.com%2Fj_security_check"
)
SUCCESS_FRAGMENT = "erp102"
EXCLUDE_FRAGMENT = "passport"

USERNAME = os.getenv("TONGTU_USER", "")
PASSWORD = os.getenv("TONGTU_PASSWORD", "")

# ── 选择器（2026-07 通途 passport 登录页，已 MCP 探路确认）──
SELECTORS = {
    "username": 'input[name="username"]',
    "password": 'input[name="password"]',
    "captcha_img": 'img[alt="验证码"]',
    "captcha_input": 'input[name="captcha"]',
    "login_btn": 'button:has-text("立即登录")',
    "auto_login_cb": 'input[type="checkbox"]',  # "7天内自动登录"
}


def login(page) -> bool:
    """
    使用 ddddocr 自动登录通途。
    返回 True（成功）或 False（失败）。
    """
    if not USERNAME or not PASSWORD:
        logger.error("请设置环境变量 TONGTU_USER 和 TONGTU_PASSWORD")
        return False

    ocr = DdddocrLogin(max_attempts=5)
    ocr.set_page(page)

    logger.info("导航到通途登录页...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector('input[name="username"]', state='attached', timeout=15000)
    page.wait_for_timeout(2000)

    # 勾选"7天内自动登录"
    try:
        ocr.ensure_checkbox(SELECTORS["auto_login_cb"], "7天内自动登录")
    except Exception as e:
        logger.warning("勾选自动登录失败: %s，继续...", e)

    def fill():
        ocr.fill_field(SELECTORS["username"], USERNAME)
        ocr.fill_field(SELECTORS["password"], PASSWORD)

    return ocr.login_loop(
        fill_fn=fill,
        captcha_selector=SELECTORS["captcha_img"],
        captcha_input_selector=SELECTORS["captcha_input"],
        login_btn_selector=SELECTORS["login_btn"],
        url_fragment=SUCCESS_FRAGMENT,
        exclude_fragment=EXCLUDE_FRAGMENT,
        captcha_min_length=4,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        pg = ctx.new_page()

        success = login(pg)
        print("登录成功！" if success else "登录失败")
        if success:
            pg.wait_for_timeout(3000)

        browser.close()
        sys.exit(0 if success else 1)
