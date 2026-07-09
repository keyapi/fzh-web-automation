---
okf: v0.1
type: Lesson
title: Playwright + ddddocr 自动登录踩坑汇总
description: 为通途和赛狐实现 Playwright + ddddocr 自动登录过程中遇到的所有问题、根因、解决方案和遗留问题
tags: [playwright, ddddocr, login, tongtu, sellfox, ocr, captcha, element-ui]
timestamp: 2026-07-09
---

# Playwright + ddddocr 自动登录 — 踩坑汇总

## 背景

为 fzh-web-automation 的通途（tongtu）和赛狐（sellfox）两个平台实现 Playwright + ddddocr 自动登录。MCP 浏览器实测两个平台均登录成功，但 Python 脚本遇到多个问题。

## 已验证成功（MCP 浏览器）

| 平台 | 验证码 | ddddocr 识别 | 登录结果 |
|------|--------|-------------|---------|
| 通途 | 5位字母数字 `bw63n` | ✅ | `passport.tongtool.com` → `erp102.tongtool.com/dashboard` |
| 赛狐 | 4位字母数字 `NKBk` | ✅ | `login.html` → `web/dashboard.html` |

## 踩坑 1: page.goto `wait_until="load"` 超长等待

**现象**：`page.goto(url)` 默认 `wait_until="load"`，等待页面所有资源（图片、字体、iframe、追踪像素）加载完成才返回。赛狐页面包含 `bat.bing.com` 追踪像素和 Tencent CAPTCHA JS，这些第三方资源在网络受限环境下可能永不触发 `load` 事件，导致 `page.goto` 阻塞 3+ 分钟。

**根因**：`wait_until="load"` 等待 `window.load` 事件，该事件要求所有子资源加载完成。

**解决**：
- `page.goto(url, wait_until="domcontentloaded")` — 只等 HTML 解析完成
- `page.goto(url, wait_until="commit")` — 最快，只等导航提交
- 然后用 `page.wait_for_selector('#element', state='attached')` 手动等待关键 DOM 元素

**代码**：
```python
# ❌ 慢
page.goto(url)  # 默认 wait_until="load"

# ✅ 快
page.goto(url, wait_until="domcontentloaded", timeout=30000)
page.wait_for_selector('#username', state='attached', timeout=15000)
```

## 踩坑 2: Element UI checkbox 内含 `<a>` 链接导致 Target crashed

**现象**：赛狐"阅读并接受"协议勾选框，`label.el-checkbox` 内含两个 `<a>` 链接（"赛狐用户注册协议"和"隐私协议"）。点击 label 时如果命中 `<a>` 标签，浏览器会导航到协议页面（`target="_blank"`），导致 Chromium 渲染进程崩溃（`Page.evaluate: Target crashed`）。崩溃后所有后续 Playwright 操作挂死——`wait_for_selector` 永远等不到。

**DOM 结构**：
```html
<label class="el-checkbox">
  <span class="el-checkbox__input">
    <span class="el-checkbox__inner"></span>   ← 安全的点击目标
  </span>
  <span class="el-checkbox__label">
    阅读并接受
    <a href="aup.html" target="_blank">赛狐用户注册协议</a>  ← 危险！
    及
    <a href="protection.html" target="_blank">隐私协议</a>       ← 危险！
  </span>
</label>
```

**解决**：选择器精确到 `span.el-checkbox__inner`（纯 span，无子元素，不会触发导航）。

```python
# ❌ 可能点到 <a> 链接 → Target crashed
"agree_cb": 'label.el-checkbox:has-text("阅读并接受")'

# ✅ 精确点击 checkbox 小方块
"agree_cb": 'label.el-checkbox:has-text("阅读并接受") span.el-checkbox__inner'
```

**遗留问题**：使用 `ensure_checkbox()` 的 `_checkbox_looks_checked()` 检测 `is-checked` class 的 Element UI 兼容逻辑在 Python Chromium 中未充分验证。MCP 浏览器中正常。

## 踩坑 3: 验证码刷新后 DOM 重建导致截图失败

**现象**：点击验证码刷新后，旧的 `<img>` 元素被删除，新的 `<img>` 元素由服务端异步创建。如果在 DOM 重建期间调用 `locator.screenshot()`，会报 `Timeout 10000ms exceeded`。

**解决**：不用 Playwright 截图，改用 JS 直接读取 `<img>` 的 `src` 属性（data URI），在 Python 中 base64 decode。

```python
# ❌ Playwright 截图 — DOM 重建时报 timeout
png = page.locator('img[src^="data:image/jpg"]').screenshot()

# ✅ JS 直读 data URI
b64 = page.evaluate(
    """() => {
        const img = document.querySelector('img[src^="data:image/jpg"]');
        if (!img) return null;
        const s = img.src;
        const i = s.indexOf(',');
        return i > 0 ? s.substring(i + 1) : null;
    }"""
)
png = base64.b64decode(b64) if b64 else None
```

配合 `ddddocr_login.py` 新增的 `solve_captcha_from_bytes()` 方法直接处理 bytes。

## 踩坑 4: ddddocr 识别结果少于 4 位

**现象**：ddddocr 偶发识别出 3 位或更少字符（验证码实际 4-5 位字母数字），导致登录失败。

**解决**：`solve_captcha` 加 `min_length` 参数，结果 < 4 位视为失败返回 None，触发重试（自动刷新验证码）。

```python
text = ocr.solve_captcha_from_bytes(png, min_length=4)
# 内部: if len(text) < 4 → return None → retry
```

## 踩坑 5: 验证码有时效，必须刷新后立刻提交

**现象**：赛狐验证码有时效。页面加载后如果等待太久（如 ddddocr 首次加载 ONNX 模型需 5-10 秒），验证码可能已过期。填入过期验证码 → 登录失败 → URL 不跳转。

**解决**：每次登录尝试前先点刷新获取新验证码，然后立刻 OCR → 填入 → 登录。ddddocr 首次加载慢的问题是固定的（ONNX 模型 70MB+），后续调用秒出。

## 踩坑 6: 赛狐验证码选择器歧义

**现象**：赛狐登录页有多个 `data:image` 图片（包括 Tencent CAPTCHA 的 PNG 图标）。`img[src^="data:image"]` 匹配 15 个元素。

**解决**：字母验证码是 JPG 格式，滑块图标是 PNG。用 `img[src^="data:image/jpg"]` 精确匹配。

## 验证状态

| 项目 | MCP 浏览器 | Python 脚本 |
|------|-----------|------------|
| 通途登录 | ✅ 成功 | ⚠️ 未独立测试（逻辑与 MCP 一致） |
| 赛狐登录 | ✅ 成功 | ❌ 未跑通（agree checkbox Target crashed 问题待最终确认） |
| ddddocr 识别 | ✅ 两者均可用 | ✅ `test_ocr.py` 通过 |
| 页面加载速度 | ✅ 秒开 | ✅ `wait_until="commit"` 后 0.2s |

## 关键文件

| 文件 | 说明 |
|------|------|
| `ddddocr_login.py` | 共享 OCR 引擎（惰性加载、熔断、预处理、solve_captcha_from_bytes） |
| `tongtu_login_ocr.py` | 通途登录适配器 |
| `sellfox_login_ocr.py` | 赛狐登录适配器 |
| `tongtu_auto_export.py` | + `--auto-login` 集成 |
| `sellfox_auto_export.py` | + `--auto-login` 集成 |
| `cdp-based/` | WX 的 CDP 方案（WorkBuddy 专用，保留） |

## 下一步建议

1. 新对话中用 MCP 浏览器单独验证 agree checkbox 的 `el-checkbox__inner` 选择器
2. 通途 Python 脚本独立测试（选择器简单，没有 agree checkbox 的 `<a>` 链接问题，应该直接能跑）
3. 赛狐 agree checkbox 如果 Playwright locator 仍 crash，考虑直接用 `page.locator(...).click()` 而非 JS evaluate
4. 清除 `chrome-profile-test/` 等测试目录的 git 跟踪
