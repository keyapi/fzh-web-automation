# AGENTS.md

> 本文件是项目**唯一指令来源**，Claude Code / Codex CLI 共用。
> `CLAUDE.md` 应为此文件 symlink，不要直接编辑 CLAUDE.md。

## 通用守则

### 编码铁律 (Karpathy)

1. **编码前思考**：不假设。不确定就提问。
2. **简洁优先**：最少代码解决问题，不做投机性工作。
3. **精准修改**：只碰必须碰的，匹配已有风格，删掉死代码。
4. **目标驱动**：先写验证用例，再让它通过。

### 工作流三原则

**① 先搜再造 (Search Before Building)** — 三层搜索，按顺序：

1. **搜项目内**：模块索引定位 → 读 SKILL.md + references/ → 复用已有脚本/选择器
2. **搜网上**：Playwright 文档、ExtJS/Element UI 选择器模式、开源方案
3. **再自己造**：确认没有现成的之后才从零写。

**② 把湖煮干 (Boil the Lake)** — 自动化脚本版：

- 每次操作必须闭环验证：执行 → 读结果 → 确认数据正确
- 导出后检查行数、列名、末尾汇总行是否跳过
- 不验证 = 代码不可靠

**③ 用户主权 (User Sovereignty)** — Agent 推荐，用户决定。库存修改前必须备份，修改后必须导出对照。

## 项目信息

**fzh-web-automation** — FZH 跨境电商浏览器自动化工具集，Playwright 驱动通途 / 赛狐 ERP 自动导出导入。

### Agent 新机器首次 clone 后必做

```bash
# 1. 安装 uv (Python 包管理器)
#    Windows: powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
#    Mac/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装项目依赖 + Chromium
uv sync
uv run playwright install chromium

# 3. 检查并安装 Node.js（如未安装）
#    Windows: winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements
#    Mac: brew install node

# 4. 安装 Playwright MCP（浏览器自动化对话模式）
npm install -g @playwright/mcp

# 5. 初始化 CLAUDE.md symlink（仅 Claude Desktop 需要）
#    powershell -ExecutionPolicy Bypass -File setup.ps1

# ⚠️ MCP 装完后必须重启 Claude Desktop / Codex，配置才会生效！
```

> 所有脚本通过 `uv run python <script.py>` 运行，不需要全局 Python / conda。

### 项目依赖的外部项目

| 项目 | 路径 | 关系 |
|------|------|------|
| **fzh-data** | `D:\Work\赛狐\Cursor\` | 数据管道，消费本项目的通途/赛狐导出文件 |

此项目为 fzh-data 提供通途库存自动下载 + 赛狐导入能力。fzh-data 的 `stock-init`、`warehouse-restock` 等模块依赖本项目的导出结果。

## 模块索引

| Skill | 平台 | 一句话 |
|-------|------|--------|
| `tongtu-automation` | 通途 ERP (ExtJS) | 自动导出 6 仓库存结存 + 生成导入文件 + 合并多仓清单 |
| `sellfox-automation` | 赛狐 ERP (Element UI) | 库存导出 (浏览器+API) + 商品导入更新 + 海外仓备货单 |

> Skill 文件在 `.claude/skills/<name>/SKILL.md`，Agent 按触发词自动加载。
> 详细参考在 `references/` 子目录。

## 关键行为规则

1. **MCP 先探路铁律**：新页面/新功能必须先 MCP 浏览器探路 → 确认选择器 → 再写 Python 代码。禁止凭猜测凑 URL。
2. **闭环验证铁律**：脚本写完必须跑一遍闭环（执行 → 读结果 → 确认正确）。
3. **库存修改铁律**：修改库存前先下载备份，修改后再导出对照。
4. **永不硬编码凭据**：密钥/token/密码用 `os.getenv()` 或 `.env`。`chrome-profile/` 和 `sellfox-profile/` 含明文 cookie，绝不可提交 git。
5. **永不直接 push main**：任何改动必须走 `feature/xxx` 分支 → 提交 → PR → 审批后合并。
6. **探索后立即更新文档**：MCP 探索有新发现 → 立即更新对应 `references/*.md`，不攒记忆负担。
7. **uv 运行所有脚本**：`uv run python <script.py>`，`uv add <包名>` 加依赖。
8. **OKF 文档规范**：所有 `.md` 文件必须有 YAML frontmatter（`type` 字段必填），每个目录必须有 `index.md`，每个 bundle 必须有 `log.md`。

## 技术概览

| 维度 | 通途 | 赛狐 |
|------|------|------|
| URL | erp102.tongtool.com | www.sellfox.com |
| UI 框架 | ExtJS | Element UI (Vue.js) |
| 仓库选择器 | 自定义 togglebutton | el-select 标准下拉 |
| 导出方式 | `<a onclick>` 直接下载 | 图标按钮 → 弹窗 → 确定 |
| 登录 | passport 统一 | 独立 + 拼图滑块 |
| 持久化 | chrome-profile/ | sellfox-profile/ |

## 文档体系

```
AGENTS.md (< 200 lines)              ← 你正在读的，项目总纲 + 路由地图
├── README.md                        ← 人读项目介绍
├── README_给同事.md                 ← 给同事的入口（→ docs/onboarding.md）
├── AGENT_HANDOFF.md                 ← Agent 交接文档（脚本清单、字段映射、边界条件）
├── docs/
│   ├── index.md                     ← 文档导航
│   ├── log.md                       ← 变更记录
│   ├── onboarding.md                ← 非技术同事上手操作指南
│   ├── reference/
│   │   ├── tongtu-pitfalls.md       ← 通途 13 个踩坑记录
│   │   ├── sellfox-pitfalls.md      ← 赛狐踩坑 + 选择器文档
│   │   ├── technical-decisions.md   ← 关键技术决策
│   │   └── company-context.md       ← 公司背景、供应链、仓库映射
│   └── lessons/
│       ├── webfetch-fix.md          ← WebFetch 修复
│       └── hooks-learning.md        ← Hooks 学习结论
├── .claude/skills/
│   ├── tongtu-automation/           ← 通途 skill + references/
│   └── sellfox-automation/          ← 赛狐 skill + references/
└── .mcp.json                        ← 项目级 Playwright MCP 配置
```
