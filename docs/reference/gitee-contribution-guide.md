---
okf: v0.1
type: Reference
title: Gitee 贡献指南 — 非技术同事版
description: 无需 GitHub 账号、无需翻墙，通过 Gitee 为 fzh-web-automation 贡献代码。两种模式：协作者模式（推荐，无需 Fork + Agent 全自动建 PR）和 Fork 模式（备用）
tags: [gitee, contribution, non-technical, workbuddy, onboarding, collaborator]
timestamp: 2026-07-08
---

# Gitee 贡献指南（非技术同事版）

> 你没有 GitHub 账号、不能翻墙？没关系。通过 Gitee（码云）贡献代码，项目主会帮你合并到 GitHub。

## 模式选择

| 模式 | 适合谁 | 人工步骤 | PR 创建方式 |
|------|--------|---------|------------|
| **A. 协作者模式**（推荐） | 内部同事，已被加为仓库协作者 | 仅注册 Gitee | Agent 调 API 自动建 |
| B. Fork 模式（备用） | 外部贡献者，未被加为协作者 | 注册 + Fork + 网页点按钮 | 人工网页操作 |

> 新同事默认走模式 A。项目主（keyapi）先把你加为协作者，之后一切由 Agent 搞定。

---

# 模式 A：协作者模式（推荐）

## ⚠️ 第零步：通知项目主（你做一次）

把你的 Gitee 用户名告诉 keyapi，他会在仓库后台把你加为协作者。

之后你就有权限直接 push 到 `gitee.com/keyapi/fzh-web-automation`，无需 Fork。

---

## 之后所有操作：复制给 WorkBuddy

如果你**已经在本地有代码**（比如之前 clone 过，有一个分支），复制下面这段：

```
我是 fzh-web-automation 项目的开发者，Gitee 用户名是 ___（填你的）。
项目主已经把我加为仓库协作者。请严格按以下步骤把我的代码贡献上去：

==== 第一步：配置 Gitee 认证（只做一次） ====

1. 帮我打开浏览器，导航到 https://gitee.com/profile/personal_access_tokens
   如果没登录，引导我先登录（手机号+密码）
2. 引导我点「生成新令牌」
   - 名称填 fzh-web-automation
   - 权限勾选 projects（仓库读写）
   - 点提交
3. 让我把生成的令牌复制粘贴给你
4. 把令牌写入项目根目录 .env 文件：GITEE_TOKEN=<令牌>
5. 配置 git 记住凭证（避免每次输入）：
   git config credential.helper store

==== 第二步：同步最新 main 到我的分支 ====

6. 先看看我现在在哪个分支，有没有未提交的改动（git status）
7. git stash （暂存未提交改动）
8. git remote -v （看当前 remote，如果是 keyapi 的仓库就不用改）
9. git fetch origin main
10. git checkout <我的功能分支名> （比如 ddddocr-auto-login）
11. git rebase origin/main （把我的分支变基到最新 main）
    ⚠️ 如果有冲突，帮我解决——改动以我的版本为准
12. git stash pop （恢复暂存的改动）

==== 第三步：读取项目规范 ====

13. 读 AGENTS.md 全文
14. 读 docs/reference/gitee-contribution-guide.md 全文
15. 读 docs/reference/company-context.md

==== 第四步：检查代码规范 ====

16. git diff origin/main --name-only （列出我改了哪些文件）
17. 检查每个文件：
    - 脚本名是否用 sellfox_ 开头？不是就重命名
    - 有没有 hardcode 密码/token/api_key？有就改成 os.getenv()
    - pyproject.toml 里的依赖：用 uv add 管理。如果有 ddddocr：
      uv add ddddocr selenium
      uv add "onnxruntime==1.16.3"  ← 版本必须钉死，高版本 Windows DLL 报错
    - 有没有 chrome-profile/ sellfox-profile/ .env 目录/文件被 track？如果有，确认 .gitignore 里已忽略
18. 如果代码没有问题，跳到下一步。如果有问题，先修好。

==== 第五步：写文档 ====

19. 创建 docs/reference/sellfox-login-ocr.md（参照已有 docs 文件的 YAML frontmatter 格式）：
    - type: Reference
    - 脚本干什么用、怎么用、依赖什么包、踩过什么坑

==== 第六步：提交 ====

20. git add -A
21. git diff --cached --name-only
    ⚠️ 此时必须停止，列出所有待提交文件，等我说「确认」再继续
22. 我确认后：
    git commit -m "feat(sellfox): 添加 ddddocr 验证码自动识别登录"

==== 第七步：推送 + 创建 PR ====

23. git push origin <分支名>  （用自己的 Gitee token 推送，不必用 https://user:token@ 格式，因为 credential.helper store 已记住）
    如果 git push 密码提示，输入你的 Gitee 用户名，密码用令牌（不是登录密码）
24. 推送成功后，用 Gitee OpenAPI 创建 Pull Request：

    curl -s -X POST "https://gitee.com/api/v5/repos/keyapi/fzh-web-automation/pulls" \
      -H "Content-Type: application/json;charset=UTF-8" \
      -d '{
        "access_token": "<你的Gitee令牌>",
        "title": "feat(sellfox): 添加 ddddocr 验证码自动识别登录",
        "head": "<分支名>",
        "base": "main",
        "body": "## 改动\n- 用 ddddocr 实现赛狐登录拼图验证码自动识别\n- 新增 sellfox_login_ocr.py\n\n## 测试\n- 已在本地验证登录成功"
      }'

25. API 返回的 html_url 就是 Gitee 上的 PR 链接。把链接告诉我。
```

如果你**还没有本地代码**（从零开始），用下面这段：

```
我是 fzh-web-automation 项目的开发者，Gitee 用户名是 ___（填你的）。
项目主已经把我加为仓库协作者。请帮我从零设置：

==== 第一步：配置 Gitee 认证（只做一次） ====

1. 帮我打开浏览器，导航到 https://gitee.com/profile/personal_access_tokens
2. 引导我生成新令牌，权限选 projects
3. 让我把令牌粘贴给你 → 写入项目根目录 .env

==== 第二步：克隆仓库 ====

4. git clone https://gitee.com/keyapi/fzh-web-automation.git .
5. git config credential.helper store
6. git checkout -b feature/my-contribution （创建功能分支）

==== 第三步：安装环境 ====

7. 检查 uv 是否安装，没装就装
8. uv sync
9. uv run playwright install chromium

==== 第四步：读规范 ====

10. 读 AGENTS.md、docs/reference/gitee-contribution-guide.md、docs/reference/company-context.md

现在环境就绪，功能分支已创建。告诉我可以开始写代码了。
```

---

## 再发新 PR（第二次及以后）

第一次的 token 和 git 配置都好了。之后每次贡献只需：

```
我要提交一个新功能。Git 凭证已配好。

1. git checkout main && git pull origin main
2. git checkout -b feature/<功能名>
3. [我写代码]
4. 读 AGENTS.md 确认我没有违反规范
5. git add -A && git commit -m "feat(scope): 描述"
6. git push -u origin feature/<功能名>
7. 用 Gitee API 创建 PR（token 在 .env 里）：
   curl -s -X POST "https://gitee.com/api/v5/repos/keyapi/fzh-web-automation/pulls" \
     -H "Content-Type: application/json;charset=UTF-8" \
     -d '{"access_token":"<从.env读取>","title":"<标题>","head":"feature/<功能名>","base":"main","body":"<描述>"}'
8. 告诉我 PR 链接
```

---

# 模式 B：Fork 模式（备用）

> 如果项目主没有把你加为协作者，或者你只是临时贡献一次，走 Fork 模式。

## 第一步：注册 Gitee 账号（一次）

打开 https://gitee.com → 注册 → 手机号或邮箱均可。

## 第二步：Fork 仓库（一次）

1. 打开 https://gitee.com/keyapi/fzh-web-automation
2. 点右上角 **Fork** → 确认

## 第三步：Clone + 开发（Agent 操作）

把下面粘贴给 WorkBuddy（把 `你的用户名` 换掉）：

```
git clone https://gitee.com/你的用户名/fzh-web-automation.git
cd fzh-web-automation
uv sync
uv run playwright install chromium
git checkout -b feature/my-contribution
读 AGENTS.md 和 docs/reference/gitee-contribution-guide.md
```

## 第四步：提交 PR（人工操作）

代码 push 后，打开自己的 Gitee 仓库页面 → 创建 Pull Request → 目标选 `keyapi/fzh-web-automation` main 分支。

---

## 项目规范速查

### 技术栈

| 项 | 选型 |
|----|------|
| Python | >= 3.10 |
| 包管理 | uv |
| 浏览器自动化 | Playwright |
| Excel | pandas + openpyxl |

### Git 规范

- 分支命名：`feature/xxx` 或 `fix/xxx`
- Commit 格式：中文 `type(scope): 描述`
- 类型：`feat`（新功能）、`fix`（修复）、`docs`（文档）、`refactor`（重构）
- **禁止**直接 push main、禁止提交密钥/密码

### 代码规范

- 脚本放根目录，命名 `sellfox_*.py` 或 `tongtu_*.py`
- 禁止硬编码密码/token：一律 `os.getenv()`
- 新增依赖：`uv add <包名>`
- 运行：`uv run python <script.py>`

### ddddocr 相关

```bash
uv add ddddocr selenium
uv add "onnxruntime==1.16.3"   # 版本必须钉死！
```

---

## 常见问题

### Q: push 密码提示填什么？
A: 用户名填 Gitee 用户名，密码填**私人令牌**（不是 Gitee 登录密码）。用 `git config credential.helper store` 之后只需输一次。

### Q: Agent 创建的 PR 链接在哪？
A: Gitee API 返回的 JSON 里 `html_url` 字段就是。

### Q: PR 提了之后多久合并？
A: 在 IM 上 ping keyapi。
