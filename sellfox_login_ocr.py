#!/usr/bin/env python3
"""
赛狐登录 — ddddocr 自动识别验证码 + Playwright

关键：验证码有时效，必须点击刷新后立刻识别+填入+登录。
"""
import logging
import os
import sys
import time

from ddddocr_login import DdddocrLogin

logger = logging.getLogger(__name__)

# ── 配置 ──
LOGIN_URL = "https://www.sellfox.com/amzup-web-main/login.html"
SUCCESS_FRAGMENT = "/home"
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
    "agree_cb": 'label.el-checkbox:has-text("阅读并接受")',            # 必须是 label 不是 span 文字
}


def login(page) -> bool:
    if not USERNAME or not PASSWORD:
        logger.error("请设置环境变量 SELLFOX_USER 和 SELLFOX_PASSWORD")
        return False

    ocr = DdddocrLogin()
    ocr.set_page(page)

    logger.info("导航到赛狐登录页...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)

    # 勾选协议 + 自动登录
    try:
        ocr.ensure_checkbox(SELECTORS["auto_login_cb"], "5天内自动登录")
    except Exception as e:
        logger.warning("勾选自动登录失败: %s", e)
    try:
        ocr.ensure_checkbox(SELECTORS["agree_cb"], "阅读并接受协议")
    except Exception as e:
        logger.warning("勾选协议失败: %s", e)

    # 填入账号密码（只填一次）
    logger.info("填入账号密码...")
    ocr.fill_field(SELECTORS["username"], USERNAME)
    ocr.fill_field(SELECTORS["password"], PASSWORD)

    # 主循环：刷新 → 立刻 OCR → 填入 → 登录
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.info("第 %d/%d 次尝试...", attempt, MAX_ATTEMPTS)

        # 1. 点击刷新验证码（用 JS 定位 a[href="javascript:"] 点击）
        try:
            page.evaluate(
                """() => {
                    const input = document.querySelector('input[placeholder*="图形验证码"]');
                    const link = input?.closest('.el-input')?.parentElement?.querySelector('a[href="javascript:"]');
                    if (link) link.click();
                }"""
            )
        except Exception:
            pass
        page.wait_for_timeout(400)  # 等待新图片加载

        # 2. 立刻截图+OCR
        text = ocr.solve_captcha(SELECTORS["captcha_img"])
        if not text:
            logger.warning("OCR 失败，重试...")
            time.sleep(0.3)
            continue

        # 3. 填入验证码
        try:
            page.locator(SELECTORS["captcha_input"]).first.fill(text)
        except Exception as e:
            logger.warning("填入验证码失败: %s", e)
            time.sleep(0.3)
            continue

        # 4. 点击登录
        try:
            page.locator(SELECTORS["login_btn"]).first.click()
        except Exception as e:
            logger.warning("点击登录失败: %s", e)
            time.sleep(0.3)
            continue

        # 5. 等待结果
        page.wait_for_timeout(2000)
        url = page.url or ""
        if SUCCESS_FRAGMENT in url:
            logger.info("登录成功！URL: %s", url)
            return True

        logger.info("未跳转（验证码错误或过期），刷新重试...")
        time.sleep(0.3)

    logger.error("全部 %d 次尝试失败", MAX_ATTEMPTS)
    return False


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
