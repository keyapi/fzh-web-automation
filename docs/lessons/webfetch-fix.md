---
okf: v0.1
type: Lesson
title: WebFetch 失败修复 — skipWebFetchPreflight
description: Claude Code WebFetch 报错 Unable to verify if domain is safe to fetch 的修复
tags: [webfetch, claude-code, settings, preflight]
timestamp: 2026-05-20
---

# WebFetch 失败修复

## 问题

Claude Code WebFetch 报错 `Unable to verify if domain is safe to fetch`

## 原因

Claude Code 在获取网页前会访问 `claude.ai` 做域名安全预检，企业网络/GFW 会拦截这个预检请求。

## 解决

在用户级配置文件 `%USERPROFILE%\.claude\settings.json` 中加入：

```json
{
  "skipWebFetchPreflight": true
}
```

> 注意：这是用户级配置（不在项目 `.claude/` 下），需要重启 Claude Desktop 生效。
> 备选方案：用 `curl` 绕过（`Bash(curl:*)` 许可即可）
