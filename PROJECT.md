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

### 每次使用（两步）
```powershell
cd C:\Users\zhang\通途库存Excel
uv run tongtu_auto_export.py --launch
```

1. 浏览器自动弹出，打开库存结存页面
2. 在浏览器里登录通途、手动选择仓库 `FZH-DANEEY-皮壳仓库`
3. 切回终端按回车
4. 脚本自动：点击导出 → 下载Excel → 调用generate生成导入文件

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

### 问题4：自动选仓库未实现
- **尝试：** `page.locator("select").first.select_option(label=...)` 无效
- **原因：** 通途的仓库选择器不是标准`<select>`元素，可能是自定义下拉框组件
- **inspect_page函数：** 最初用`querySelectorAll('[onclick]')`只抓到86个元素，改成全量扫描又降到24个（过多过滤条件过滤掉了关键元素）
- **待改进：** 需要正确地dump出仓库选择器的DOM结构，才能写出自动选择逻辑
- **当前方案：** 用户手动选仓库。这是本项目唯一的半自动化环节。

### 问题5：Python文件同步
- **现象：** 沙箱内改的Python文件，用户需要知道改动并手动更新本地文件
- **本质：** Cowork模式的Linux沙箱和用户Windows主机是隔离的，无法直接执行命令或部署

## 六、关键代码片段

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

## 七、给Claude Code/Cursor的接手建议

### 立即改善项
1. **自动选仓库**：用`page.evaluate()`执行JS找到仓库选择器的真实DOM结构（自定义组件可能有`data-value`、`data-id`或Vue/React绑定数据）
2. **CDP持久化登录**：解决Chrome调试端口问题，用户可以关掉Chrome后重新启动但保留登录session
3. **一站式**：考虑把导出和生成合并成一个Click，用户双击一个bat就能完成

### 排查仓库选择器的方法
在浏览器Console里执行这段：
```javascript
// 找到所有包含"仓库"文字的元素及其DOM结构
document.querySelectorAll('*').forEach(el => {
    if (el.innerText && el.innerText.includes('仓库') && el.offsetParent) {
        console.log(el.tagName, el.className, el.id, el.outerHTML.slice(0,200));
    }
});
```

### 如果使用Claude Code + Playwright MCP
Claude Code可以直接安装 `@anthropic/mcp-server-playwright`（或社区版），这样：
- Agent可以直接 `page.goto`, `page.locator`, `page.click` 
- 可以直接 `page.evaluate()` 查看DOM
- 可以读写页面元素、截图、执行JS
- **不需要Chrome扩展**，纯Playwright MCP驱动
- Agent可以自主调试，不需要用户一步步跑脚本反馈

### uv环境信息
- Python: 3.10 (Anaconda)
- 虚拟环境: `.venv/`
- 包: pandas 2.3.3, openpyxl 3.1.5, playwright 1.58.0
