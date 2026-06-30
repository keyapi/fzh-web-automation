---
name: web-automation
description: >
  浏览器自动化通用模式和踩坑经验。Playwright MCP 操控任意网站的通用方法：
  登录处理、选择器策略、下载处理、批量操作。
  当用户提到"浏览器自动化"、"Playwright"、"自动登录"、"cookie 持久化"、
  "选择器"、"下载文件"、"批量操作"、"DOM 探路"、"截图"等时触发。
  不要用于通途/赛狐具体操作 — 那些用 tongtu-automation / sellfox-automation skill。
compatibility: >
  需要 Playwright MCP 或 Python Playwright (sync_api)。
  通用模式，不限平台。配合平台 skill（tongtu-automation、sellfox-automation）使用。
metadata:
  module: web-automation
  updated: 2026-06-30
---

# 浏览器自动化通用模式

## 核心 MCP 工具速查

| 工具 | 用途 |
|------|------|
| `browser_tabs` | 列出/创建/切换标签页 |
| `browser_navigate` | 打开 URL |
| `browser_snapshot` | 获取页面元素树（比截图更好） |
| `browser_click` | 点击元素 |
| `browser_take_screenshot` | 截全页或元素 |
| `browser_run_code` | 执行任意 JS |
| `browser_wait_for` | 等待时间或文本 |
| `browser_evaluate` | 执行 JS 并返回结果 |

**黄金法则**：优先用 `browser_snapshot` 看页面结构，不要一直截图。

## Hard Constraints

- **MCP 先探路**：新页面必须先 MCP 浏览器探路 → 确认选择器 → 再写 Python 代码
- **禁止凭猜测凑 URL**：必须通过浏览器真实操作找到入口
- **选择器优先级**：CSS 属性选择器 > ID+文字 > ref 引用 > 纯文字
- **登录检测**：找到仅在登录后出现的特征元素，用它判断状态

## 模式 1：登录处理

### "记住我" 模式（推荐）

1. 导航到目标页面 → 检测登录状态
2. 未登录 → 截图让用户手动登录
3. 登录后 `context.cookies()` 提取并保存
4. 后续使用时注入 cookies 再导航

### 登录检测

```js
const loggedIn = await page.evaluate(() => {
  return !!document.querySelector('#user-menu');
});
```

## 模式 2：选择器策略（优先级从高到低）

1. **CSS 属性选择器**：`a[onclick="doExport()"]` — 最稳定
2. **ID 限定 + 文字**：`#sidebar a:has-text("导出")` — 限定区域
3. **ref 引用**：snapshot 中的 `[ref=e123]`
4. **纯文字**：`text=导出Excel` — 最不可靠

### DOM 诊断

```js
document.querySelectorAll('*').forEach(el => {
  if (el.innerText && el.innerText.includes('关键词') && el.offsetParent) {
    console.log(el.tagName, el.className, el.id, el.outerHTML.slice(0,200));
  }
});
```

## 模式 3：下载文件

- **Python 模式**：`page.expect_download()` 精确控制保存位置
- **MCP 模式**：文件自动保存到 `.playwright-mcp/`，用桥接脚本整理

## 模式 4：批量操作

```
for each item in list:
  1. 点击切换
  2. 等待渲染（5-8 秒，看框架）
  3. 执行操作
  4. 验证状态
  5. 记录结果
```

## 踩坑速查

| # | 坑 | 解决 |
|---|-----|------|
| 1 | Cookie 加密 (Windows DPAPI) | Playwright `context.cookies()` 获取解密值 |
| 2 | Session cookie 丢失 | 依赖"记住我"长期 cookie 触发自动登录 |
| 3 | MCP 热加载限制 | 必须新建对话 |
| 4 | 中文路径编码 | `subprocess.run(encoding="utf-8")` |
| 5 | 下载路径不一致 | MCP 用 `.playwright-mcp/`，Python 用 `expect_download()` |
| 6 | 仓库切换等待不足 | 3 秒不够，建议 5-8 秒 |

## Quality Checklist

- [ ] MCP 先探路确认选择器再写 Python？
- [ ] 登录状态检测（特征元素）？
- [ ] 选择器用了最稳定方式（属性选择器优先）？
- [ ] 下载后文件位置确认了？
- [ ] 批量操作每个步骤有等待时间？

## 参考

- [tongtu-automation](../tongtu-automation/SKILL.md) — 通途 ERP 专项
- [sellfox-automation](../sellfox-automation/SKILL.md) — 赛狐 ERP 专项
