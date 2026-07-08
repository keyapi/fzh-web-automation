#!/usr/bin/env python3
"""
赛狐登录 — ddddocr 自动识别验证码 + Playwright
"""
import logging
import os
import sys

from ddddocr_login import DdddocrLogin

logger = logging.getLogger(__name__)

# ── 配置 ──
LOGIN_URL = "https://www.sellfox.com/amzup-web-main/login.html"
SUCCESS_FRAGMENT = "/home"

USERNAME = os.getenv("SELLFOX_USER", "")
PASSWORD = os.getenv("SELLFOX_PASSWORD", "")

# ── 选择器（2026-07 MCP 探路实测确认）──
SELECTORS = {
    "username": '#username',                                         # 密码登录 tab 下的用户名
    "password": 'input[placeholder*="请输入密码"]',                    # 密码输入框
    "captcha_img": 'img[src^="data:image/jpg"]',                     # 字母验证码（jpg，不匹配腾讯滑块 PNG）
    "captcha_refresh": 'text=点击刷新',                               # 刷新验证码
    "captcha_input": 'input[placeholder*="图形验证码"]',
    "login_btn": 'button:has-text("登录")',
    "auto_login_cb": 'text=5天内自动登录',
    "agree_cb": 'text=阅读并接受',
}
SLIDER_TEXT = "拖动下方拼图"


def _has_slider(page) -> bool:
    """检测腾讯滑块验证码是否弹出"""
    try:
        return page.locator(f'text={SLIDER_TEXT}').is_visible(timeout=3000)
    except Exception:
        return False


def login(page) -> bool:
    """
    使用 ddddocr 自动登录赛狐。
    返回 True（成功）或 False（失败）。
    """
    if not USERNAME or not PASSWORD:
        logger.error("请设置环境变量 SELLFOX_USER 和 SELLFOX_PASSWORD")
        return False

    ocr = DdddocrLogin(max_attempts=10)
    ocr.set_page(page)

    logger.info("导航到赛狐登录页...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)

    # 检测滑块 — Playwright 大概率触发腾讯滑块
    if _has_slider(page):
        logger.warning(
            "检测到腾讯滑块验证码（Playwright 自动化触发）。"
            "请在浏览器中手动拖动滑块完成验证（60s 超时）..."
        )
        try:
            page.wait_for_selector(
                f'text={SLIDER_TEXT}',
                state="hidden",
                timeout=60000,
            )
            logger.info("滑块已通过，继续自动登录...")
        except Exception:
            logger.error("滑块超时未完成，登录失败")
            return False

    # 勾选协议 + 自动登录
    try:
        ocr.ensure_checkbox(SELECTORS["auto_login_cb"], "5天内自动登录")
    except Exception as e:
        logger.warning("勾选自动登录失败: %s", e)
    try:
        ocr.ensure_checkbox(SELECTORS["agree_cb"], "阅读并接受协议")
    except Exception as e:
        logger.warning("勾选协议失败: %s", e)

    # 先点一次验证码刷新，触发「点击刷新」文本出现
    try:
        page.locator(SELECTORS["captcha_refresh"]).click(timeout=3000)
        page.wait_for_timeout(500)
    except Exception:
        # 如果还没出现就继续，login_loop 会截现有验证码
        pass

    def fill():
        ocr.fill_field(SELECTORS["username"], USERNAME)
        ocr.fill_field(SELECTORS["password"], PASSWORD)

    return ocr.login_loop(
        fill_fn=fill,
        captcha_selector=SELECTORS["captcha_img"],
        captcha_input_selector=SELECTORS["captcha_input"],
        login_btn_selector=SELECTORS["login_btn"],
        url_fragment=SUCCESS_FRAGMENT,
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
