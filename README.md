# fzh-web-automation

FZH 跨境电商浏览器自动化工具集 — Playwright 驱动通途 / 赛狐 ERP 自动导出导入。

## 快速开始

```bash
# 1. 安装环境（首次）
uv sync
uv run playwright install chromium

# 2. 通途导出 6 仓库存
uv run python tongtu_auto_export.py

# 3. 赛狐导出库存
uv run python sellfox_auto_export.py
```

> 首次运行需手动登录一次（浏览器弹窗），之后 cookie 持久化免登录。

## 项目简介

本项目为 FZH 跨境電商提供通途和赛狐两个 ERP 系统的浏览器自动化能力：

- **通途**：自动导出 6 个仓库库存结存清单 → 生成导入文件 → 合并多仓清单
- **赛狐**：库存导出（浏览器 + API 双模式）、商品导入更新、海外仓备货单

自动化基于 Playwright persistent_context 实现持久化登录（chrome-profile / sellfox-profile）。

## 模块

| 模块 | 脚本 | 功能 |
|------|------|------|
| 通途导出 | `tongtu_auto_export.py` | 6 仓库存自动导出 + 导入文件生成 |
| 通途导入生成 | `generate_tongtu_import.py` | 库存清单 → 5 列导入模板 |
| 通途合并 | `merge_inventory.py` | 多仓原始清单合并 |
| 赛狐库存导出 | `sellfox_auto_export.py` | 浏览器 + API 双模式导出 |
| 赛狐商品导入 | `sellfox_import_update.py` | 商品导入更新 |
| 赛狐备货单 | `sellfox_restock_api.py` | 海外仓备货单 API E2E |
| MCP 桥接 | `mcp_to_output.py` | MCP 下载文件整理 |

## 数据源

脚本从以下目录读取数据：
- `downloads/` — 通途原始库存清单（gitignored）
- `output/` — 生成的导入文件（gitignored）

## 依赖

- Python >= 3.10 + uv
- Playwright + Chromium
- pandas, openpyxl
- 详见 `pyproject.toml`

## 更多

- [AGENTS.md](AGENTS.md) — 项目指令源 + 行为规则
- [AGENT_HANDOFF.md](AGENT_HANDOFF.md) — Agent 交接文档
- [docs/](docs/) — OKF v0.1 文档体系
- [.agents/skills/](.agents/skills/) — Agent Skills
