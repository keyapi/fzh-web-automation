# Session Handoff — 2026-05-18

> 给下一个 Agent/Claude 实例的接手文档。
> 原则：**前向（需要知道什么才能继续），不啰嗦（引用已有文件，不复制内容）。**

## 1. Git 状态

```
分支: claude/affectionate-snyder-71ad77 (= main)
最新: cee373b 闭环完成: 商品详情弹窗→spec+weight正则提取验证通过
工作区: clean
```

## 2. 项目速览

这是一个跨境电商 ERP 自动化项目，覆盖两个平台：

| 平台 | 技术栈 | 核心脚本 | SKILL |
|------|--------|----------|-------|
| **通途** Tongtu | ExtJS | `tongtu_auto_export.py` | `SKILL_tongtu_automation.md` |
| **赛狐** Sellfox | Element UI (Vue) | `sellfox_auto_export.py`, `sellfox_import_update.py`, `commodity_import_template.py` | `.claude/skills/sellfox-automation/` |

**环境**：`uv` 管理 Python 依赖，`playwright` 浏览器自动化，`sellfox-profile/` / `chrome-profile/` 持久化登录。

## 3. 已完成功能

### 通途
- 6仓库库存结存导出 + 导入文件生成 + 多仓合并
- 通途 Bug 规避：先切走再切回

### 赛狐 — 库存明细
- 导出：浏览器点击 + API 双模式 (`sellfox_auto_export.py`)
- 搜索：SKU/品名 + 精确/模糊 (已验证 4 种组合)
- 仓库筛选：单仓/多仓/全部 (warehouseIds API)
- 隐藏0数据：影响 787 行，每次新 session 重置为 ON

### 赛狐 — 商品导入
- 下载模板：勾选字段 → 下载 Excel
- 上传导入：生成 Excel → 浏览器点击上传 → `POST /excel/import.json`
- **闭环验证**：搜索 SKU → 详情弹窗 → 规格 tab → 正则提取数值比对

## 4. 关键决策 & 踩坑（非妥协项）

| # | 决策/坑 | 说明 |
|---|---------|------|
| 1 | **uv 管理环境** | 永远 `uv run python`，不用 `pip` 或裸 `python` |
| 2 | **Cookie 持久化** | `launch_persistent_context(user_data_dir)`，MCP 做不到 |
| 3 | **Excel sheet 名** | 赛狐模板有 `['商品','hidden1','hidden2']`，必须 `sheet_name='商品'` |
| 4 | **禁止 read_excel 模板** | 会丢 hidden sheet，导入卡住 |
| 5 | **Element UI checkbox** | 必须 Playwright 真实点击，`evaluate` 不行 |
| 6 | **20+ 隐藏 dialog** | 必须 `filter(w => w.getBoundingClientRect().width > 0)` |
| 7 | **el-dropdown-item** | 对 Playwright 不可见，用 `evaluate` 点击 |
| 8 | **搜索框 placeholder 动态变化** | 用 `getByPlaceholder` 不用 `input[placeholder=...]` |
| 9 | **探索流程** | MCP 先探 → Python 代码 → 文件记录 → git 提交 |
| 10 | **闭环测试** | 任何自动化脚本写完后必须自己跑一遍验证 |
| 11 | **探索后更新** | 新发现立即更新对应 `references/*.md`，同步所有相关章节 |

**详细踩坑**（12 条）见 `CLAUDE.md` 踩坑记录章节。

## 5. 文件地图

### Skill 体系
```
.claude/skills/sellfox-automation/
├── SKILL.md                              # 赛狐平台总览 + 触发条件 + Hard Constraints
├── references/
│   ├── warehouse-detailed.md             # 库存明细页 — 选择器/API/全部已知未知已闭环
│   ├── commodity-import.md               # 商品导入 — 69字段/下载模板/上传API/Excel陷阱
│   └── code-snippets.md                  # MCP选择器→Python Playwright 代码翻译
```

### Python 脚本
```
sellfox_auto_export.py          # 库存导出 (浏览器+API双模式, --demo-search搜索演示)
sellfox_import_update.py         # 商品导入更新 (生成Excel→上传→闭环验证)
commodity_import_template.py    # 下载商品导入模板
tongtu_auto_export.py            # 通途6仓导出
```

### 文档
```
CLAUDE.md        # 总纲: 规则/踩坑/平台知识/文件清单 → 新Agent第一读物
PROJECT.md       # 详细项目文档
HANDOFF.md       # 本文件
README_给同事.md # 给人类的入口
```

## 6. 待办 (Next Steps)

- [ ] **商品详情API**: pageList.json 不返规格字段，需找真正的详情API
- [ ] **多仓库批量导入**: warehouseIds 参数的单仓/多仓切换
- [ ] **赛狐其他页面**: 采购/订单/财务等模块的探索
- [ ] **MCP 浏览器文件对话框**: 沙箱限制，已用 `fileChooser.setFiles()` 绕过
- [ ] **sf-vvv-i token**: 前端JS动态生成，纯REST API调用需从页面提取
- [ ] **导入异步等待**: 弹窗"正在导入"等WebSocket通知，可优化轮询逻辑
- [ ] **carton/wrap 字段正则**: Python Playwright innerText 排版与MCP不同，待完善

## 7. 恢复运行

```bash
# 进入工作目录
cd C:\Users\zhang\通途库存Excel\.claude\worktrees\affectionate-snyder-71ad77

# 赛狐库存导出
uv run python sellfox_auto_export.py          # 浏览器演示
uv run python sellfox_auto_export.py --api    # API模式

# 赛狐商品导入 (闭环)
uv run python sellfox_import_update.py

# 通途库存导出
uv run python tongtu_auto_export.py
```

## 8. 给接手 Agent 的启动指南

1. **先读** `CLAUDE.md` — 总纲，覆盖平台知识 + 12条踩坑 + 规则
2. **看 Skill** `.claude/skills/sellfox-automation/SKILL.md` — 赛狐 Hard Constraints
3. **看 references** `warehouse-detailed.md` / `commodity-import.md` — 页面选择器/行为
4. **复制代码** `code-snippets.md` — 每个 MCP 选择器都有 Python 等价代码
5. **记住铁律**: MCP先探→代码后写→文件记录→git提交→闭环验证
