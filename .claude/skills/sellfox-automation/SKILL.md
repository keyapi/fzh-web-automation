---
name: sellfox-automation
description: >
  操控赛狐 ERP (sellfox.com) 的仓库库存、商品管理、采购、财务等模块。
  当用户提到"赛狐"、"Sellfox"、库存明细、仓库导出等时触发。
  不要用于通途 (Tongtu) — 那是另一个独立系统。
compatibility: >
  需要 Playwright MCP 已配置。推荐配合 .claude/skills/ 同级目录下的
  SKILL_web_automation.md 使用（通用选择器、登录、下载模式）。
metadata:
  platform: Sellfox ERP (Element UI / Vue.js)
  account: fzh (克勇)
  updated: 2026-05-15
---

# 赛狐 ERP 浏览器自动化

## Hard Constraints

- 赛狐是 Element UI (Vue.js) 框架，**永远**不要用 ExtJS 选择器模式（如 `toggle_btn_down`）
- 导出按钮是纯图标 `.icon_sf_download`，**永远**不要用 `text=导出` 搜索
- 页面是 SPA，**永远**导航后等 5-8 秒再操作（等 Vue 渲染）
- **永远**先读 `references/` 下对应的页面文件，再操作该页面
- **永远**不在 SKILL.md 里硬编码密码或 token

## When NOT to Use

- 通途 (Tongtu) ERP 操作 → 用项目根目录的 `SKILL_tongtu_automation.md`
- 非赛狐网站的一般浏览器自动化 → 用 `SKILL_web_automation.md`
- 纯数据分析（已有 Excel 文件） → 直接用 pandas/Python 脚本

## Trigger Conditions

- 用户消息含 "赛狐"、"Sellfox"、"sellfox.com"
- 用户提到 "库存明细"、"仓库导出"、el-select、Element UI 等赛狐特征
- URL 包含 `sellfox.com/amzup-web-main/`

## 平台概览

| 属性 | 值 |
|------|-----|
| 网站 | https://www.sellfox.com |
| 系统类型 | 跨境电商 ERP（店小秘生态） |
| 前端框架 | Element UI (Vue.js) — `el-select`, `el-dialog`, `el-input`, `el-table` |
| 登录页 | `/amzup-web-main/login.html` |
| 登录方式 | 密码/验证码登录 + 拼图滑块验证 |
| 记住登录 | "5天内自动登录" checkbox |

## vs 通途 (快速对比)

| 维度 | 通途 | 赛狐 |
|------|------|------|
| UI | ExtJS | Element UI (Vue) |
| 下拉框 | 自定义 togglebutton | `el-select` |
| 导出 | `<a onclick>` 直接下载 | 图标按钮 → 弹窗 → 确定 |
| 选择器 | onclick 属性 | placeholder/class 属性 |
| 登录 | passport 统一 | 独立 + 滑块验证 |

## 目录结构

```
.claude/skills/sellfox-automation/
├── SKILL.md                          # 本文件 — 平台总览 + 导航
├── references/
│   ├── login.md                      # 登录页 (待探索)
│   ├── warehouse-detailed.md         # 库存明细页 ✅
│   ├── warehouse-summary.md          # 库存汇总页 (待探索)
│   └── ...                           # 后续页面逐一添加
└── scripts/
    └── sellfox_cookies.py            # Cookie 持久化 (待开发)
```

## 登录流程（踩坑总结）

### Python 持久化登录
```python
context = p.chromium.launch_persistent_context(
    user_data_dir="sellfox-profile/",  # cookies 自动持久化到这里
    headless=False,
)
```
- 首次：手动登录 → cookies 自动保存 → **下次免登录**
- 过期：`--fresh` 强制删除 profile 重新登录

### 登录检测（双重判定）
赛狐登录后跳转到 **dashboard**（不是库存页）。检测需两种方式：

1. **URL 检测**：`"login" not in page.url`（登录后跳离 login.html）
2. **用户元素检测**：`page.locator('text=克勇').first.is_visible()`（用户名出现）

### 登录后跳转
登录成功 → 立刻检测 `page.url`：
- 如果在 dashboard → `page.goto(PAGE_URL)` 跳到仓库页
- 如果已在仓库页 → 直接继续

### 踩坑：MCP vs Python 登录差异
| | MCP 浏览器 | Python Playwright |
|---|---|---|
| Cookie 持久化 | ❌ 会话关闭即丢失 | ✅ persistent_context 自动保存 |
| 登录检测 | 人工确认 | 代码双重检测(URL+元素) |
| httpOnly cookie | 无法获取 | context.cookies() 全量获取 |

## 标准操作流程

1. 导航到目标 URL
2. 检测登录状态（URL 是否被重定向到 `/login` 或首页）
3. 如有 cookie 文件则注入（`browser_run_code` + `addCookies`）
4. 等待 5-8 秒（SPA JS 渲染）
5. **读对应 `references/*.md`** 获取该页面的选择器
6. 按 reference 中的选择器执行操作
7. **操作前先关闭所有弹窗**：赛狐页面 el-popover/el-select-dropdown 容易残留，用 Escape 或点击页面标题关闭
8. **选择器优先用位置定位**（left/top），placeholder 会动态变化不可靠
9. 每次 MCP 探索后有新发现，**立即更新 reference 文件**

## 探索进度

```
库存明细页: ██████████ 95%
├── 页面结构: ✅
├── 过滤条件: ✅
├── 导出弹窗: ✅
├── 导出流程: ✅
├── API 接口: ✅
├── 仓库列表: ✅ (3个: CENTRADE/DANEEY/POLAND)
├── 搜索功能: ✅ (8类型+精/模)
├── 分页: ✅ (20/50/100/200)
├── 隐藏0数据: ✅ (影响 787 行)
└── 多仓导出: ❓
```

## 参考

- [库存明细页](references/warehouse-detailed.md) — 过滤器、导出弹窗、选择器、所有已知 DOM 知识
