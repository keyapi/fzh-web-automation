--- 
okf: v0.1
type: Log
title: Changelog
timestamp: 2026-07-07
---

# Changelog

## 2026-07-09

- **ddddocr 自动登录全修复验证**：
  - `tongtu_login_ocr.py` 重写：HTTP 下载原始 JPG → ddddocr（匹配 CDP 方案），直连循环替代 login_loop
  - `sellfox_login_ocr.py` 7 处修复：语法错误、SUCCESS_FRAGMENT、agree checkbox 简化、captcha 刷新、URL 轮询
  - `ddddocr_login.py` `_checkbox_looks_checked` 增强：原生 checkbox + 祖先 label 检测
  - 两个脚本均独立验证：通途 22s 一次成功、赛狐 15s 一次成功、无 Target crashed
  - 新建 `docs/solutions/integration-issues/ddddocr-playwright-login-fixes.md`
  - 更新 `docs/lessons/ddddocr-login-pitfalls.md` 验证状态 → ✅
  - 更新 `AGENT_HANDOFF.md` 第 8 节状态

- **Skill 自动登录规则更新**：
  - `tongtu-automation/SKILL.md`：快速运行默认加 `--auto-login`，新增 Agent 执行规则（禁止不加 flag）
  - `sellfox-automation/SKILL.md`：登录流程改为 `--auto-login` 自动登录，新增 Agent 执行规则
  - `tongtu_sales_report.py`：新增 `--auto-login` 支持（复用 `tongtu_login_ocr`）
  - 用户说"导出库存"时 Agent 自动带 `--auto-login`，有 cookie 跳过，无 cookie 时 ddddocr 识别验证码

- **Playwright + ddddocr 自动登录踩坑文档增强**：
  - ce-compound 增强 `docs/lessons/ddddocr-login-pitfalls.md`：新增诊断陷阱说明、GitHub issue 引用、last_updated
  - 更新 `AGENT_HANDOFF.md`：新增 ddddocr login 脚本清单 + 踩坑速查

## 2026-07-08

- **Playwright + ddddocr 自动登录（通途 + 赛狐）**：
  - 新建 `ddddocr_login.py`：共享 OCR 引擎（惰性加载、熔断、预处理、solve_captcha_from_bytes）
  - 新建 `tongtu_login_ocr.py`：通途登录适配器
  - 新建 `sellfox_login_ocr.py`：赛狐登录适配器
  - 修改 `tongtu_auto_export.py`、`sellfox_auto_export.py`：+ `--auto-login` 标志
  - 新建 `docs/lessons/ddddocr-login-pitfalls.md`：6 个踩坑汇总
  - 新建 `docs/reference/tongtu-captcha-ocr.md`：ddddocr 方案文档（WX 贡献）
  - 从 fzh-data 拷贝 `.agents/skills/okf/SKILL.md`
  - AGENTS.md 补充 3 条规则（凭证扫描、OKF 详解、commit 格式）+ 团队角色表

- **Gitee 贡献流程文档**：
  - 新建 `docs/reference/gitee-contribution-guide.md`（v1）：Fork 版贡献流程 + WorkBuddy 提示词模板
  - 新建 `docs/reference/gitee-to-github-merge.md`：项目主 Gitee→GitHub 合并 SOP
  - **v2 更新** `gitee-contribution-guide.md`：新增**协作者模式**（推荐）— 无需 Fork，Agent 通过 Gitee OpenAPI 自动创建 PR。仅需 1 步人工（注册 Gitee）+ keyapi 添加协作者，后续全由 Agent 接管
  - 更新 `docs/index.md`、`docs/reference/index.md`

## 2026-07-07

- **通途销售及库存报表自动导出**：
  - 新建 `tongtu_sales_report.py`：自动提交统计任务 → 轮询等待完成 → 下载 zip
  - 新建 `process_sales_report.py`：解压 zip → 按「仓库」列分表 → FZH-DANEEY 系列合并为一个工作表
  - MCP 浏览器探路选择器（Node REPL 内置 Playwright），确认完整操作流后再写代码
  - 新增坑 15-19 至 tongtu-pitfalls.md

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
