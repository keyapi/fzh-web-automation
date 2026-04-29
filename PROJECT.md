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
| `tongtu_auto_export.py` | 浏览器自动化：用Playwright打开通途 → 点导出 → 调generate脚本 |
| `pyproject.toml` | uv项目配置，依赖：pandas、openpyxl、playwright |

| `inspect_warehouse.py` | DOM诊断脚本：打开页面 → dump包含指定文字的DOM元素 → JSON输出 |

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

### 每次使用（两步 → 现在只需一步！）
```powershell
cd C:\Users\zhang\通途库存Excel
uv run tongtu_auto_export.py
```

1. 浏览器自动弹出，打开库存结存页面
2. 在浏览器里登录通途
3. **脚本自动：** 检测登录完成 → 切换仓库至 `FZH-DANEEY-皮壳仓库` → 点击导出 → 下载Excel → 调用generate生成导入文件

### 也可以只生成导入文件（已有库存清单时）
```powershell
uv run python generate_tongtu_import.py 库存结存清单.xlsx 输出文件名.xlsx
```

## 五、浏览器自动化调试历程

### 问题1：CDP模式连接Chrome失败
- **尝试：** `chrome.exe --remote-debugging-port=9222`，用Playwright `connect_over_cdp` 连接
- **现象：** Chrome启动了但 `curl.exe http://127.0.0.1:9222/json/version` 始终连不上
- **尝试过的修复：** 改127.0.0.1、加`--remote-allow-origins=*`、杀残留进程
- **结论：** Windows环境CDP连接不稳定，放弃CDP模式，改用`--launch`（Playwright自己启动Chromium）
- **影响：** launch模式需要手动登录（每次会话独立，无cookie持久化）。如果能解决CDP，可以免登录。

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

### 待改善项
1. **CDP持久化登录**：解决Chrome调试端口问题，免去每次登录。P0需求
2. **Playwright MCP**：已配置 `%APPDATA%\Claude\claude_desktop_config.json` 但 MCP 服务器未被加载（待排查 Claude Desktop 的 MCP 加载机制）

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
