# AGENT_HANDOFF.md — fzh-web-automation

> Agent 交接文档。人类文档见 [README.md](README.md)。

## 1. 项目背景

FZH 跨境电商浏览器自动化工具集，Playwright 驱动通途 / 赛狐 ERP 自动导出导入。
为 fzh-data 项目提供通途库存自动下载 + 赛狐导入能力。

## 2. 脚本清单

| 脚本 | 功能 | 平台 |
|------|------|------|
| `tongtu_auto_export.py` | 6 仓库存结存导出 + 导入文件生成 | 通途 |
| `generate_tongtu_import.py` | 库存清单 → 5 列导入模板 | 通途 |
| `merge_inventory.py` | 多仓原始清单合并 | 通途 |
| `inspect_warehouse.py` | DOM 诊断 dump | 通途 |
| `mcp_to_output.py` | MCP 下载文件整理 | 通途 |
| `sellfox_auto_export.py` | 库存导出（浏览器+API 双模式） | 赛狐 |
| `sellfox_import_update.py` | 商品导入更新（生成→上传→闭环验证） | 赛狐 |
| `sellfox_restock_api.py` | 海外仓备货单 API E2E | 赛狐 |
| `commodity_import_template.py` | 商品导入模板下载 | 赛狐 |

## 3. 通途核心流程

```
登录态检测 → 6 仓依次: 选仓库(含Bug规避) → 点导出 → 等下载 → 保存
→ 所有仓库导出完成 → 调 generate_tongtu_import 生成 5 列导入文件
→ 调 merge_inventory 合并多仓清单
```

### 关键字段映射（库存清单 → 导入模板）

| 模板列 | 来源列 (Excel) | 说明 |
|--------|---------------|------|
| SKU/SKU别名 | A: SKU | 直接映射 |
| 安全库存 | — | **留空(None)**，填 0 会覆盖通途现有数据 |
| 头程报关费 | — | **留空(None)** |
| 头程运费 | Q(17): 头程运费(CNY) | |
| 其他费用 | S(19): 头程其它费(CNY) | |

### Excel 结构（库存结存清单）
- 第 1 行：标题
- 第 2 行：仓库信息 + 导出时间
- 第 3 行：空
- 第 4 行：列标题（19 列）
- 第 5+ 行：数据
- 末尾行：数量总计 / 金额总计（**必须跳过**）

### CLI 参数

| 参数 | 作用 |
|------|------|
| (无) | 日常导出 6 仓 |
| `--fresh` | 强制重新登录（删除 chrome-profile） |
| `--export-cookies` | 导出 cookie JSON 供 MCP 注入 |

## 4. 赛狐核心流程

### 库存导出
```
登录检测 → cancelHiddenZeroData → 选仓库 → 点导出按钮 → 弹窗选字段 → 确定
→ 下载 Excel → API 验证返回
```

### 商品导入
```
下载模板（69 字段勾选） → 构造 DataFrame → ExcelWriter(sheet_name='商品')
→ 浏览器上传 → POST /excel/import.json → 搜索验证
```

### 仓库 ID

| 仓库名 | 赛狐 ID |
|--------|---------|
| CENTRADE | 279814 |
| DANEEY | 279833 |
| POLAND | 279841 |

## 5. 边界条件与已知限制

1. **通途 ExtJS Bug**：仓库已选中但数据未渲染 → 必须"先切走再切回"
2. **13 个同名导出按钮**：通途页面 FBA/FBF/Shein/Temu 等各有导出按钮，必须用 `a[onclick="exportExcelPage()"]` 精确定位
3. **赛狐 20+ 隐藏 dialog**：所有弹窗预渲染在 DOM，必须 `filter(w => w.getBoundingClientRect().width > 0)`
4. **赛狐 Excel sheet 名**：必须是 `商品`（模板有 hidden sheet，不可 read_excel 后 to_excel）
5. **Cookie 持久化**：仅 persistent_context 支持，MCP 独立实例不共享
6. **JSESSIONID 不可持久化**：session cookie 无 expires，依赖记住密码 cookie 触发自动登录
7. **Windows 中文编码**：所有脚本开头 `sys.stdout.reconfigure(encoding='utf-8')`
8. **MCP 热加载**：session 中激活 MCP 后需新建对话

## 6. 数据路径约定

| 目录 | 用途 | Git |
|------|------|-----|
| `chrome-profile/` | 通途持久化登录 | ignore |
| `sellfox-profile/` | 赛狐持久化登录 | ignore |
| `downloads/` | 通途原始库存清单 | ignore |
| `output/` | 生成导入文件 | ignore |
| `.playwright-mcp/` | MCP 下载文件 | ignore |

## 7. 踩坑速查

| # | 坑 | 解决 |
|---|-----|------|
| 1 | 通途数据表格不加载 | 先切走再切回 |
| 2 | Cookie 加密 (DPAPI) | `context.cookies()` 解密 |
| 3 | Session cookie 丢失 | 记住密码 cookie 触发自动登录 |
| 4 | MCP 热加载 | 新建对话 |
| 5 | 中文路径编码 | `sys.stdout.reconfigure(encoding='utf-8')` |
| 6 | 下载路径差异 | Python 用 `expect_download`，MCP 用 `.playwright-mcp/` |
| 7 | el-dropdown 不可见 | `evaluate("item.click()")` |
| 8 | Element UI checkbox | 必须 Playwright 真实点击 |
| 9 | el-dialog wrapper 隐藏 | `filter(w => w.width > 0)` |
| 10 | Excel sheet 名 | `sheet_name='商品'` |

> 完整 13 条踩坑见 [docs/reference/tongtu-pitfalls.md](docs/reference/tongtu-pitfalls.md) 和 [docs/reference/sellfox-pitfalls.md](docs/reference/sellfox-pitfalls.md)。

---

> 如果本文档与 `.py` 代码冲突，以代码为准。
