---
okf: v0.1
type: Lesson
title: Hooks 钩子学习结论 — 当前项目不需要 Hooks
description: 学习 Claude Code Hooks 机制后的结论：当前项目不需要也不使用 Hooks
tags: [hooks, claude-code, sessionstart, pretooluse, architecture]
timestamp: 2026-05-20
---

# Hooks 钩子学习记录

## 结论：当前项目不需要也不使用 Hooks

### 知识来源

1. 官方 Blog: [How Claude Code works in large codebases](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start)
2. 社区教程/案例（CSDN、dev.to、GitHub Issues）

### Hooks 核心知识

| 生命周期事件 | 作用 | 我们适用？ |
|-------------|------|-----------|
| `SessionStart` | 注入动态上下文（git 分支等） | 否 GUI/Desktop 不支持 (Bug #16763) |
| `PreToolUse` | 拦截危险命令（exit 2 阻止） | 否 无强拦截需求 |
| `PostToolUse` | 自动格式化、lint | 否 不做 Web 开发 |
| `UserPromptSubmit` | 每次提示前预处理 | 否 频率太高，过度设计 |
| `Stop` | 会话结束反思总结 | 否 不需要 |

### 实测结论

1. **Claude Desktop 3P 安装版不支持 SessionStart hooks**（官方已知 Bug [#16763](https://github.com/anthropics/claude-code/issues/16763)）——只对 CLI 启动的 session 有效，GUI pane 不触发
2. **Plugin 中的 SessionStart hook 也有问题**（官方 Bug [#16538](https://github.com/anthropics/claude-code/issues/16538)）——`additionalContext` 不会被传递给 Claude

### 设计原则

- Hooks 适合**企业团队场景**（强制代码规范、审查流程）和**确定性拦截**（PreToolUse 拦截 `rm -rf` / `git push --force`）
- 个人项目如果只是"想让 Claude 知道些信息"，用 CLAUDE.md + SKILL.md 就够，不需要 Hook
- `git status` 这类即时查询，让 Claude 现场跑一下就行（1 秒完成），不需要 Hook 预注入
- **过度设计比不做更糟糕**——别为了用一个技术而去用它
