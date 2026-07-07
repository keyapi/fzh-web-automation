--- 
okf: v0.1
type: Log
title: Changelog
timestamp: 2026-07-07
---

# Changelog

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
