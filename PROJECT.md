# 通途库存导入自动化项目

## 一、目标

从通途ERP导出库存结存清单 → 生成可直接导入通途的Excel（仅更新头程运费、其他费用）。

导入目标仓库：`FZH-DANEEY-皮壳仓库`

## 二、涉及文件

| 文件 | 说明 |
|------|------|
| `库存结存清单*.xlsx` | 通途导出（19列），第4行是表头，数据从第5行开始 |
| `批量导入模板.xlsx` | 通途标准导入模板（5列），含Sheet2/Sheet3空表 |
| `generate_tongtu_import.py` | 核心脚本：读取库存清单 → 生成导入文件 |
| `tongtu_auto_export.py` | 浏览器自动化：打开通途 → 依次选6个仓库 → 导出 → 调generate脚本 |
| `pyproject.toml` | uv项目配置，依赖：pandas、openpyxl、playwright |
| `SKILL_deploy_playwright_mcp.md` | Skill: Playwright MCP 部署详细版（给 Claude 看的踩坑指南） |
| `SKILL_tongtu_automation.md` | Skill: 通途库存自动化专项（给 Claude 看的通途特化指南） |
| `SKILL_quick_start.md` | Skill: 通用环境安装（Windows/Mac，零基础，一句话启动） |
| `SKILL_web_automation.md` | Skill: 浏览器自动化通用模式（选择器、登录、下载、踩坑） |
| `README_给同事.md` | 给同事看的人口文件：这是什么、怎么开始 |
| `inspect_warehouse.py` | DOM诊断脚本：打开页面 → dump包含指定文字的DOM元素 → JSON输出 |
| `chrome-profile/` | 持久化浏览器会话目录（自动创建，含cookies/localStorage，已在.gitignore排除） |
| `mcp_to_output.py` | MCP模式桥接脚本：将 MCP 下载的文件整理到 downloads/ + output/ |
| `extract_cookies.py` | 临时工具：从 chrome-profile 提取 cookies 供 MCP 注入（已整合到 tongtu_auto_export.py --export-cookies） |
| `downloads/` | 多仓库模式：下载的原始库存清单（按仓库重命名） |
| `output/` | 多仓库模式：生成的导入文件（按仓库重命名） |

## 三、数据映射

库存结存清单（源，19列）→ 导入模板（目标，5列）：

| 导入模板列 | 库存结存清单来源 | 规则 |
|-----------|-----------------|------|
| SKU/SKU别名(必填) | A列: SKU | 原样填入 |
| 安全库存 | — | **留空（None），禁止填0** |
| 头程报关费（CNY） | — | **留空（None），禁止填0** |
| 头程运费（CNY） | Q列(17): 头程运费(CNY) | 原值填入 |
| 其他费用（CNY） | S列(19): 头程其它费(CNY) | 原值填入 |

**关键规则：**
- 安全库存和头程报关费必须是None（留空），填0会导致通途把这两个字段也更新为0
- 头程运费和其他费用保留原始精度（当前数据含3位小数，测试验证通过）
- 数值为None时通途跳过不更新，为0时更新为0

## 四、日常使用

### 前置条件（一次性）
```powershell
winget install --id=astral.uv -e          # 安装uv
cd C:\Users\zhang\通途库存Excel
uv sync                                    # 创建虚拟环境+装依赖
uv run playwright install chromium         # 装Chromium浏览器
```

### 每次使用
```powershell
cd C:\Users\zhang\通途库存Excel
uv run python tongtu_auto_export.py
```

1. 浏览器自动弹出，自动加载持久化会话
2. **首次使用：** 需要手动登录通途（输入用户名、密码、验证码，勾选 remember），登录后 cookies 保存到 `chrome-profile/`
3. **后续使用：** 自动检测已登录 → 自动依次处理 **6 个仓库**：
   - `CENTRADE` `FZHPoland-covers` `FZH-DANEEY-皮壳仓库` `FZH-DANEEY-退货产品仓` `FZH-DANEEY-成品仓` `FZH-DANEEY-半成品仓`
4. 每个仓库：切换 → 导出 → 下载到 `downloads/` → 生成导入文件到 `outputs/`
5. 文件名格式：`{仓库名}_库存结存清单2026-04-29...xlsx` 和 `{仓库名}_通途导入_头程运费_其他费用.xlsx`

### 重新登录（会话过期时）
```powershell
uv run python tongtu_auto_export.py --fresh
```
清除旧会话，强制重新登录。

### 也可以只生成导入文件（已有库存清单时）
```powershell
uv run python generate_tongtu_import.py 库存结存清单.xlsx 输出文件名.xlsx
```

## 五、浏览器自动化调试历程

### 问题1：CDP / 持久化登录 —— ✅ 已解决 (2026-04-29)
- **原始尝试：** `chrome.exe --remote-debugging-port=9222` → CDP端点不可达
- **最终方案：** Playwright `launch_persistent_context(user_data_dir="chrome-profile/")` 
- **原理：** Playwright 自己管理 Chromium 实例，cookies/localStorage 持久化到磁盘的 `chrome-profile/` 目录。首次手动登录后，后续运行自动加载已保存的会话，免登录
- **`--fresh` flag：** 强制删除 `chrome-profile/` 重新登录（会话过期时使用）

### 问题2：13个"导出Excel"按钮冲突
- **现象：** `page.locator("text=导出Excel")` 报 strict mode violation
- **原因：** 页面有FBA、FBF、Shein、Temu等13个不同平台的导出按钮
- **解决：** 用 CSS选择器 `a[onclick="exportExcelPage()"]` 精确匹配库存清单的导出按钮
- **技巧：** 跑脚本时报错信息列出了所有13个元素，从class和onclick函数名推断出正确选择器

### 问题3：文件下载未被捕获
- **错误1版本：** 监听 Windows Downloads 文件夹等新xlsx文件 → 超时
- **原因：** Playwright自带的Chromium下载到临时目录，不是系统Downloads
- **解决：** 改用 Playwright原生下载事件 `page.expect_download()`，拦截浏览器下载事件

### 问题6：os.system子进程找不到uv
- **现象：** `run_generate` 中 `os.system('uv run python ...')` 返回 exit=1，提示 'uv' 不是内部命令
- **原因：** 脚本通过 `uv run` 启动时 uv 在 PATH 中，但 `os.system` 启动的子进程不继承这个临时 PATH
- **解决：** 改用 `sys.executable` 直接调用 venv 中的 Python：`os.system(f'"{sys.executable}" "{script}" "{path}"')`

### 问题4：自动选仓库 —— ✅ 已解决 (2026-04-29, Claude Code模式)
- **原因：** 通途的仓库选择器不是标准`<select>`元素，而是自定义 `xtype="togglebutton"` 组件
- **DOM结构：** `div#warehouseDisableDiv > div#coll` 容器内，每个仓库是 `<span xtype="togglebutton">` 内含 `<a class="toggle_btn">仓库名</a>`
- **选中态：** `toggle_btn_down`（未选中是 `toggle_btn`）
- **解决：** 用 `page.locator("#warehouseDisableDiv a", has_text="FZH-DANEEY-皮壳仓库")` 定位并点击
- **自动化登录检测：** 用 `page.locator("#warehouseDisableDiv").is_visible()` 轮询检测登录完成（出现仓库选择器即表示已登录）
- **调试方法：** 先写 `inspect_warehouse.py` 诊断脚本 dump 所有含"仓库"/"皮壳"的元素 → 分析JSON找到DOM结构 → 改写主脚本

### 问题5：Python文件同步 —— ✅ 不再适用 (Claude Code模式)
- **本质改变：** Claude Code直接在本机执行，无沙箱隔离，文件实时生效

## 六、关键代码片段

### 持久化浏览器上下文（免登录核心）
```python
context = p.chromium.launch_persistent_context(
    user_data_dir=str(PROFILE_DIR),
    headless=False,
    accept_downloads=True,
    viewport={"width": 1280, "height": 800},
    args=["--disable-blink-features=AutomationControlled"],
)
page = context.pages[0] if context.pages else context.new_page()
```

### 快速检测已登录会话
```python
def is_already_logged_in(page):
    try:
        el = page.locator("#warehouseDisableDiv")
        return el.count() > 0 and el.is_visible()
    except:
        return False
```

### 自动检测登录完成（Playwright轮询）
```python
def wait_for_login(page, timeout=300):
    for i in range(0, timeout, 3):
        time.sleep(3)
        el = page.locator("#warehouseDisableDiv")
        if el.count() > 0 and el.is_visible():
            return True
    return False
```

### 自动选仓库（自定义ToggleButton组件）
```python
target = page.locator("#warehouseDisableDiv a", has_text="FZH-DANEEY-皮壳仓库").first
if "toggle_btn_down" not in (target.get_attribute("class") or ""):
    target.click()
    page.wait_for_timeout(3000)  # 等待页面刷新
```

### 导出按钮点击（Playwright）
```python
with page.expect_download(timeout=90000) as download_info:
    export_btn = page.locator('a[onclick="exportExcelPage()"]')
    export_btn.click()
download = download_info.value
download.save_as(str(target_path))
```

### 库存清单表头查找（pandas）
```python
df = pd.read_excel(path, header=None)
header_idx = df[df.iloc[:, 0].astype(str).str.strip() == 'SKU'].index[0]
df.columns = df.iloc[header_idx].astype(str).str.replace('\n', '').str.strip()
df = df.iloc[header_idx + 1:]
```

### 列名模糊匹配
```python
freight_col = [c for c in df.columns if '头程运费' in c][0]
other_col = [c for c in df.columns if '头程其它费' in c or '其他费用' in c][0]
```

## 七、Claude Code 接手记录

### 已完成 (2026-04-29)
1. ✅ **自动选仓库**：解析 DOM → 发现 `togglebutton` 组件 → 用 `#warehouseDisableDiv a` 定位 → 代码已更新
2. ✅ **一站式流程**：登录后全自动——检测登录→选仓库→导出→生成导入文件
3. ✅ **Git管理**：`.gitignore` 排除 `.xlsx`/`.png`，只追踪源码和配置
4. ✅ **持久化登录**：`launch_persistent_context` + `chrome-profile/` 目录保存 cookies，首次手动登录，后续免登录
5. ✅ **MCP 配置修复**：定位到正确路径 `Claude-3p/claude_desktop_config.json`（Microsoft Store版），添加 `mcpServers.playwright`，清理了之前写入错误路径的配置
6. ✅ **多仓库依次导出**：脚本自动遍历 6 个仓库（CENTRADE / FZHPoland-covers / 皮壳仓库 / 退货产品仓 / 成品仓 / 半成品仓），每个仓库导出+生成分别保存到 `downloads/` 和 `output/`
7. ✅ **Skill 文档**：创建 `SKILL_deploy_playwright_mcp.md` 和 `SKILL_tongtu_automation.md`，无 IT 背景的同事照着文档操作即可部署
8. ✅ **Playwright MCP 实测**：用 Playwright MCP 完成 6 仓库导出，验证了 cookie 注入、仓库切换、导出下载全流程（详见"八、MCP 调试记录"）
9. ✅ **Cookie 提取工具**：`--export-cookies` flag 可从 chrome-profile 提取非 session cookie 供 MCP 注入使用
10. ✅ **MCP 桥接脚本**：`mcp_to_output.py` 将 MCP 下载的文件整理到 `downloads/` 和 `output/`

### MCP 部署关键注意事项
- **Claude Desktop 必须彻底 Quit**：Windows 任务栏右下角系统托盘有常驻进程，只关窗口不够，必须 **右键托盘图标 → Quit**，再重新启动才能加载新 MCP
- **Microsoft Store 版配置路径特殊**：`%LOCALAPPDATA%\Packages\Claude_xxx\LocalCache\Roaming\Claude-3p\claude_desktop_config.json`
- 详见 `SKILL_deploy_playwright_mcp.md`

### 待改善项
1. **会话过期自动处理**：当前会话过期时回退到轮询手动登录，可考虑加入 cookie 有效期检测
2. **MCP 模式一键化**：目前 MCP 模式仍需要手动在对话中执行，可探索将整个 MCP 交互流程封装为 Claude skill/command

## 八、MCP 调试记录 (2026-04-29 16:30-17:00)

### 背景
上一个 session 创建了 worktree 并激活了 Playwright MCP，但因 MCP 在 session 开始之后才激活，无法使用 `browser_navigate`。本 session（`affectionate-snyder-71ad77` worktree）新开对话，Playwright MCP 已可用。

### 流程
1. 用 `browser_tabs` → `browser_navigate` 打开库存结存页面
2. 页面重定向到 passport.tongtool.com → 需要登录

### 踩坑 1：Cookie 注入绕过登录
- **尝试**: 直接从 `chrome-profile/Default/Network/Cookies` SQLite 读 cookie
- **问题**: Cookie 值被 Chromium DPAPI 加密，sqlite3 读取为空
- **解决**: 用 Playwright Python 的 `launch_persistent_context` + `context.cookies()` 获取解密后的 cookie
- **结果**: 提取到 21 个 cookie（username, password hash, ttcuid 等），但 session cookie (JSESSIONID, SERVERID) 在启动新的 headless 实例时丢失

### 踩坑 2：Session cookie 无法持久化
- **现象**: 注入 21 个 cookie 后，session cookie (JSESSIONID) 不在其中
- **原理**: JSESSIONID 是 Java 标准的 HTTP session cookie（无 expires），浏览器关闭即清除
- **解决**: 虽然 JSESSIONID 丢失，但 passport 的记住密码 cookie (username + password hash + ttcuid) 仍然可用。注入 cookie 后导航到 ERP 页面，passport 检测到记住密码 cookie，自动完成登录并签发新的 JSESSIONID
- **验证**: 注入后导航到 `erp102.tongtool.com/.../goodsbalance/...`，页面正常显示"库存结存>仓储管理"，用户名 张克勇

### 踩坑 3：MCP 下载位置
- **现象**: MCP 下载的文件保存在主仓库 `.playwright-mcp/` 目录，而非项目 worktree 下
- **解决**: 创建 `mcp_to_output.py` 桥接脚本，扫描 MCP 下载目录 → 按仓库重命名 → 复制到 `downloads/` → 调用 `generate_tongtu_import.py` 生成导入文件到 `output/`

### 踩坑 4：text= 选择器的歧义风险
- **现象**: `text=FZH-DANEEY-半成品仓` 可能匹配到表格数据中的同名字段
- **解决**: Python 脚本中已使用 `#warehouseDisableDiv a.toggle_btn` 限定范围，比纯 `text=` 更安全

### 踩坑 5：仓库切换等待时间
- **Python 脚本**: 原用 3s
- **MCP 实测**: 5s 更可靠（网络波动时 3s 可能不够）
- **已更新**: `select_warehouse()` 等待时间改为 5s

### MCP 模式下各仓库导出数据量
| 仓库 | SKU 数 | 文件大小 |
|------|--------|---------|
| CENTRADE | 1,624 | 206 KB |
| FZHPoland-covers | 1,359 | 221 KB |
| FZH-DANEEY-皮壳仓库 | 895 | 165 KB |
| FZH-DANEEY-退货产品仓 | 504 | 101 KB |
| FZH-DANEEY-成品仓 | 241 | 48 KB |
| FZH-DANEEY-半成品仓 | 146 | 31 KB |
| **合计** | **4,769** | **772 KB** |

### 诊断工具
- `inspect_warehouse.py`：打开页面 → 用户登录 → 自动dump含指定文字的DOM元素 → 输出JSON
  ```bash
  uv run python inspect_warehouse.py
  ```

### 排查仓库选择器的方法（已完成，留作参考）
```javascript
document.querySelectorAll('*').forEach(el => {
    if (el.innerText && el.innerText.includes('仓库') && el.offsetParent) {
        console.log(el.tagName, el.className, el.id, el.outerHTML.slice(0,200));
    }
});
```

### uv环境信息
- Python: 3.10 (Anaconda)
- 虚拟环境: `.venv/`
- 包: pandas 2.3.3, openpyxl 3.1.5, playwright 1.58.0
