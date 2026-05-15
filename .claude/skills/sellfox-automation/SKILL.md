---
name: sellfox-automation
description: >
  赛狐 (Sellfox) ERP 浏览器自动化。适用于仓库管理（库存明细、库存汇总）、
  商品管理、采购、财务等模块的网页操作。当用户提到"赛狐"、"Sellfox"、
  "sellfox.com"、库存明细、仓库导出等时触发。
---

# 赛狐 ERP 浏览器自动化

## 平台概览

| 属性 | 值 |
|------|-----|
| 网站 | https://www.sellfox.com |
| 系统类型 | 跨境电商 ERP（店小秘生态） |
| 前端框架 | **Element UI (Vue.js)** — `el-select`, `el-dialog`, `el-input`, `el-table` |
| 登录方式 | 密码登录 或 验证码登录 + 拼图滑块验证 |
| 记住登录 | "5天内自动登录" checkbox |
| 测试账号 | 用户名: `fzh`，显示名: 克勇 |

## 技术特征（与通途的关键差异）

| 维度 | 通途 (Tongtu) | 赛狐 (Sellfox) |
|------|--------------|----------------|
| UI 框架 | ExtJS (xtype/togglebutton) | **Element UI (el-*)** |
| 选择器模式 | `a.toggle_btn_down` 自定义组件 | `el-select` 标准下拉 |
| 导出流程 | 直接 `<a onclick>` 触发下载 | **图标按钮 → 弹窗选字段 → 确定导出** |
| 登录 | passport 统一认证 | 独立登录 + 拼图滑块 |
| 表格 | ExtJS grid | el-table / vxe-table |
| DOM 定位 | 依赖 onclick 属性 | 依赖 class/placeholder 属性 |

## 目录结构

```
.claude/skills/sellfox-automation/
├── SKILL.md                           # 本文件 — 平台总览 + 导航索引
├── references/
│   ├── login.md                       # 登录页知识 (待探索)
│   ├── warehouse-detailed.md          # 库存明细页 ✅ 已探索
│   ├── warehouse-summary.md           # 库存汇总页 (待探索)
│   └── ...                            # 后续页面逐一添加
└── scripts/
    └── sellfox_cookies.py             # Cookie 持久化脚本 (待开发)
```

## 操作流程（每次执行前）

1. **检查登录**：导航到目标页，如被重定向到 login 页则需登录
2. **注入 cookie**（如有）：用 `browser_run_code` + `addCookies()` 恢复会话
3. **加载页面**：赛狐是 SPA (Vue.js)，需等待 JS 渲染完成（5-8s）
4. **读取对应 reference**：根据当前页面加载对应的 `references/*.md`
5. **操作**：按 reference 中的选择器执行

## 已知未知

- [ ] Cookie 持久化方案是否有效（session cookie 能否跨 MCP 会话恢复）
- [ ] 导出确认后的实际下载行为（文件名格式、下载位置）
- [ ] 仓库切换时是否需要"先切走再切回"（类似通途 Bug）
- [ ] 分页加载大量数据时的处理
- [ ] 赛狐是否有 API 接口可绕过浏览器直接调用
- [x] 登录页结构
- [x] 库存明细页基本结构
- [x] 导出弹窗字段配置

## 参考资源

- [库存明细页](references/warehouse-detailed.md) — 页面结构、选择器、导出流程
