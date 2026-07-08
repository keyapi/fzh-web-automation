---
okf: v0.1
type: Log
title: Changelog
timestamp: 2026-07-07
---

# Changelog

## 2026-07-08

- **AGENTS.md 规范补充 + OKF skill**：
  - 从 fzh-data 借用 3 条规则：凭证扫描、commit 格式、团队角色表
  - 新增 `.agents/skills/okf/SKILL.md`：OKF v0.1 完整规范（从 fzh-data 拷贝），Agent 新增模块前必读

- **通途验证码自动识别（WX 贡献）**：
  - 新增 `tongtu_export_ocr.py`：CDP 浏览器 + ddddocr 全自动登录导出（基于 wangxian-fzh 的 ddddocr-auto-login 分支）
  - 新建 `cdp-based/` 目录：存放 CDP 浏览器相关的辅助脚本（`export_via_cdp.py`、`get_captcha.py`、`test_captcha_ocr.py`）
  - 新增 `test_ocr.py`：独立 OCR 测试工具
  - 新建 `docs/reference/tongtu-captcha-ocr.md`：ddddocr 方案文档 + onnxruntime 版本踩坑记录
  - 新增依赖：dddddocr、Pillow、onnxruntime（>=1.20.1，Python 3.12 约束）

## 2026-07-07

- **通途下载文件名中文乱码修复**：
  - Playwright download.suggested_filename GBK 编码→ mojibake，导致合并步骤静默跳过
  - 修复：下载时用 Python 本地时间构造安全文件名；合并时用 iterdir() + 前缀匹配替代 glob()
  - 新增坑 14 至 tongtu-pitfalls.md，更新相关交叉引用

## 2026-06-30

- **非技术同事上手文档**：新建 `docs/onboarding.md`，`README_给同事.md` 精简为入口
- **项目标准化整改**：对齐 fzh-data 标准。
  - 新建 AGENTS.md（项目权威指令源）
  - CLAUDE.md 详细内容拆分到 docs/reference/ 和 docs/lessons/
  - 新建 OKF v0.1 文档体系（docs/index.md + docs/log.md）

## 2026-05-25

- **合并工作树 claude/interesting-hoover-f0339d**：tongtu-automation skill + sellfox 引用 + 清理点击脚本

## 2026-05-20

- **Hooks 学习结论**：确认当前项目不需要 Hooks
- **WebFetch 修复**：skipWebFetchPreflight 配置

## 2026-05-19

- **通途自动化 skill 创建**：从根级 SKILL_tongtu_automation.md 迁移到 .claude/skills/tongtu-automation/
- **通途导出脚本完善**：6 仓自动导出 + 踩坑修复
