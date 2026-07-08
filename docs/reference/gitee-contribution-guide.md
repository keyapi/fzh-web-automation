---
okf: v0.1
type: Reference
title: Gitee 贡献指南 — 非技术同事版
description: 无需 GitHub 账号、无需翻墙，通过 Gitee 为 fzh-web-automation 贡献代码的完整流程
tags: [gitee, contribution, non-technical, workbuddy, onboarding]
timestamp: 2026-07-08
---

# Gitee 贡献指南（非技术同事版）

> 你没有 GitHub 账号、不能翻墙？没关系。通过 Gitee（码云）贡献代码，项目主会帮你合并到 GitHub。

## 前提

- 你能访问 [gitee.com](https://gitee.com)（国内直连，不需要 VPN）
- 你有一个邮箱（注册 Gitee 用）
- 你的电脑上已经装好了 AI Agent（WorkBuddy / Codex / Claude Desktop）

---

## 第一步：注册 Gitee 账号（只做一次）

1. 打开 https://gitee.com
2. 点右上角「注册」→ 用邮箱注册
3. 验证邮箱 → 设置用户名（建议用拼音，如 `wangxiao`）→ 完成

> 不需要手机号，邮箱即可注册。

---

## 第二步：Fork 仓库（只做一次）

Fork = 把项目主仓库复制一份到你自己的 Gitee 账号下，你在这份副本上改代码。

1. 打开 https://gitee.com/keyapi/fzh-web-automation
2. 点右上角 **「Fork」** 按钮
3. 确认 Fork 到你自己的账号下

Fork 完成后，你会有一个自己的仓库：`https://gitee.com/<你的用户名>/fzh-web-automation`

---

## 第三步：Clone 你的 Fork 到本地

打开你的 Agent（WorkBuddy），粘贴以下种子指令：

```
帮我设置 fzh-web-automation 项目：

1. 检查 Git 是否安装——没装的话帮我装
2. git clone https://gitee.com/<我的用户名>/fzh-web-automation.git ~/fzh-web-automation
3. cd ~/fzh-web-automation
4. 安装 uv（Python 包管理器）
5. 运行 uv sync 安装项目依赖
6. 运行 uv run playwright install chromium 装浏览器
7. 读 AGENTS.md 了解项目规范
8. 创建功能分支: git checkout -b feature/my-contribution
```

> 把 `<我的用户名>` 换成你的 Gitee 用户名。

---

## 第四步：开发和提交

在你的功能分支上开发。每次改完代码后，告诉 Agent：

```
帮我提交代码：
1. git add <改的文件>
2. git commit -m "feat(模块): 做了什么"
3. git push -u origin feature/my-contribution
```

Commit 格式用中文：`feat(sellfox): 添加验证码自动识别登录`

---

## 第五步：创建 Pull Request

你 push 完后：

1. 打开你的 Gitee 仓库页面：`https://gitee.com/<你的用户名>/fzh-web-automation`
2. Gitee 会提示「你推送了一个新分支」→ 点 **「创建 Pull Request」**
3. 确认目标仓库是 `keyapi/fzh-web-automation`，目标分支是 `main`
4. 填写标题和描述（Agent 可以帮你写）
5. 点「提交」

完成后项目主（keyapi）会收到通知，审查代码后手动合并到 GitHub。

---

## WorkBuddy Agent 提示词模板

把下面这段复制到 WorkBuddy 对话开头（新建一个对话）：

```
你是 fzh-web-automation 项目的开发助手。先读取项目根目录的 AGENTS.md 和 docs/ 下所有文档，理解项目规范，然后严格遵守：

【代码规范】
1. Python 脚本放根目录，命名 sellfox_*.py 或 tongtu_*.py
2. 新增依赖用 uv add <包名>，不要手动改 pyproject.toml
3. 禁止硬编码密码/token/密钥，用 os.getenv() 从 .env 读取
4. 所有脚本用 uv run python <script.py> 运行

【Git 规范】
5. commit 格式: 中文 type(scope): 描述
   类型: feat(新功能) / fix(修复) / docs(文档) / refactor(重构)
6. 不要提交到 main 分支，始终在功能分支上工作
7. 不要提交 chrome-profile/ sellfox-profile/ .env 等含敏感信息的文件

【文档规范】
8. 新增模块必须写 docs/ 文档，格式参照项目已有文件（顶部 YAML frontmatter）
9. 文档用 OKF v0.1 标准: type 字段必填，可选值: Index/Reference/Log/Research/Spec/Lesson

【质量要求】
10. 做完功能后自己运行验证，确认输出正确
11. 有疑问先问用户，不要假设
12. 不要做没被要求的事情——最简方案优先
```

---

## 项目规范速查

### 文件夹结构

```
fzh-web-automation/
├── sellfox_*.py          ← 赛狐相关脚本（放根目录）
├── tongtu_*.py           ← 通途相关脚本（放根目录）
├── click-based/          ← 旧版点击脚本，不要再往里加
├── docs/                 ← 文档
│   ├── reference/        ← 技术参考
│   └── lessons/          ← 经验教训
├── .claude/skills/       ← Agent Skill 定义
├── AGENTS.md             ← 项目总纲（Agent 自动读）
└── pyproject.toml        ← 项目依赖配置
```

### 技术栈

| 项 | 选型 |
|----|------|
| Python | >= 3.10 |
| 包管理 | uv |
| 浏览器自动化 | Playwright |
| Excel | pandas + openpyxl |

### 如果你要加代码验证码识别（ddddocr）

参考 fzh-data 项目的经验：

```bash
uv add ddddocr selenium
uv add onnxruntime==1.16.3   # 钉死版本，高版本 Windows DLL 报错
```

---

## 常见问题

### Q: Gitee 上提了 PR 后多久能合并？
A: 项目主不定期检查 Gitee PR。如果你在 IM 上 ping 一下 keyapi 会更快。

### Q: 我的代码会被原样合并吗？
A: 不一定。项目主可能会调整代码格式、文件名、文档以符合项目规范，然后以你的名义合并。

### Q: 为什么要先 Fork 而不是直接 clone keyapi 的仓库？
A: 你没有 keyapi 仓库的写权限，不能直接 push。Fork 到你自己账号下，你就有完全控制权了。
