---
okf: v0.1
type: Reference
title: Gitee→GitHub 合并操作手册
description: 项目主将 Gitee PR 手动合并回 GitHub 的标准操作流程
tags: [gitee, github, merge, pr, workflow]
timestamp: 2026-07-08
---

# Gitee → GitHub 合并 SOP

> 你是项目主（keyapi）。有同事从 Gitee 提了 PR，你需要审查代码、调整规范，然后合并到 GitHub。

## 前提

- GitHub repo: `keyapi/fzh-web-automation`（source of truth）
- Gitee repo: `keyapi/fzh-web-automation`（单向镜像，read-only mirror）
- GitHub Action 自动 sync：每 push main → force push 到 Gitee

## 整体流程

```
Gitee PR → 本地 fetch → 审查 + 规范调整 → push GitHub → 创建 PR → merge main → Gitee 自动同步
```

## 操作步骤

### 1. 添加 Gitee Remote（只做一次）

```bash
cd /path/to/fzh-web-automation
git remote add gitee https://gitee.com/keyapi/fzh-web-automation.git
```

### 2. 收到 Gitee PR 后，Fetch 贡献分支

在 Gitee PR 页面查看贡献者的分支名，然后：

```bash
git fetch gitee
```

### 3. 基于贡献分支创建审查分支

```bash
git checkout -b review/<contributor-name> gitee/<pr-branch-name>
```

### 4. 审查 + 调整

检查项：

- [ ] 无硬编码密钥、token、密码
- [ ] 无敏感文件（chrome-profile/、sellfox-profile/、.env、cookies）
- [ ] commit 格式符合规范（中文 type(scope): 描述）
- [ ] Python 依赖用 `uv add` 添加（pyproject.toml 有变化）
- [ ] onnxruntime 版本钉死（如果用 ddddocr）
- [ ] 有对应的文档（OKF 格式）
- [ ] 脚本命名符合 sellfox_*.py / tongtu_*.py 模式
- [ ] 功能验证通过

必要时在本地调整代码、补充文档、修改 commit message。直接在此分支上 commit。

### 5. 推到 GitHub

```bash
git push -u origin review/<contributor-name>
```

### 6. 创建 GitHub PR

```bash
gh pr create \
  --title "feat(scope): <贡献者名> 贡献 - <功能描述>" \
  --body "$(cat <<'EOF'
## 来源
Gitee PR: <gitee-pr-url>
贡献者: <name>

## 改动
- <改动1>
- <改动2>

## 审查
- [x] 无硬编码密钥
- [x] 依赖正确
- [x] 文档齐全
- [x] 功能验证通过

Co-Authored-By: <contributor-name> <<email>>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 7. Review + Merge

在 GitHub 上走正常 PR review 流程 → merge 到 main。

### 8. 验证同步

Merge 后约 30 秒，检查 GitHub Actions `Sync to Gitee` workflow 是否成功。

或者直接检查 Gitee 仓库的最新 commit 是否与 GitHub main 一致：

```bash
git fetch gitee main
git log gitee/main -1 --oneline
git log origin/main -1 --oneline
# 两者应相同
```

## 快速参考

| 步骤 | 命令 |
|------|------|
| 添加 remote | `git remote add gitee https://gitee.com/keyapi/fzh-web-automation.git` |
| 拉取 PR 分支 | `git fetch gitee` |
| 创建审查分支 | `git checkout -b review/<name> gitee/<branch>` |
| 推送 GitHub | `git push -u origin review/<name>` |
| 验证同步 | 检查 GitHub Actions 或对比 `gitee/main` vs `origin/main` |
