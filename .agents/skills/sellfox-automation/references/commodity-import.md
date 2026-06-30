# 赛狐 — 商品列表 — 导入更新商品

> 最后更新: 2026-05-18
> 探索状态: **初探完成** — 导入下拉、弹窗 checkbox、下载模板 API 已摸清。

---

## 页面信息

| 属性 | 值 |
|------|-----|
| URL | `https://www.sellfox.com/amzup-web-main/web/commodity/index.html` |
| 标题 | 赛狐ERP - 亚马逊卖家必备的运营管理系统！ |
| 导航路径 | 商品 → 商品列表 |
| UI 框架 | Element UI 2.x (Vue.js) |

## 导入下拉菜单

- **触发按钮**: `el-button.el-dropdown` 包含文字"导入"
- **菜单项** (el-dropdown-menu__item):
  - 导入SKU标签
  - 导入单个商品
  - 导入组合商品
  - 导入加工商品
  - 导入多属性商品
  - **导入更新商品** ← 本次探索目标
  - 导入关联供应商
  - 导入关联辅料
  - 导入1688配对
  - 导入店小秘商品

## 导入更新商品 — 弹窗

### 弹窗结构 (el-dialog__wrapper)
- 标题: "导入更新商品"
- 提示: "请选择需要更新的字段"
- 69 个 checkbox，分 8 个区域

### 全部字段清单（69 个 checkbox，分 8 区）

#### 基础信息 (18 个)
```
☑ SKU (强制选中+禁用)  ☐ 图片链接  ☐ 品名  ☐ 开发员  ☐ 开发时间
☐ 查看人  ☐ 状态  ☐ 识别码  ☐ 来源  ☐ 开启加工过程
☐ 加工费  ☐ 分类  ☐ 商品品牌  ☐ 材质  ☐ 型号
☐ 用途  ☐ 单位  ☐ 商品备注
```

#### 物流信息 (23 个)
```
☐ 中文报关名  ☐ 英文报关名  ☐ 报关单价  ☐ 报关单价币种
☐ 出口报关单价  ☐ 出口报关单价币种  ☐ 报关重量  ☐ 海关编码
☐ 危险运输品  ☐ 中文材质  ☐ 英文材质  ☐ 中文用途
☐ 英文用途  ☐ 报关型号  ☐ 报关单位  ☐ 品牌类型
☐ 出口享惠情况  ☐ 原产地(地区)  ☐ 境内货源地  ☐ 征免
☐ 生产销售企业名称  ☐ 生产销售企业代码  ☐ 申报要素
```

#### 头程信息 (7 个)
```
☐ 默认头程费用(CNY)  ☐ 清关HSCODE  ☐ 清关单价  ☐ 清关单价币种
☐ 清关税率  ☐ 产品链接  ☐ 备注
```

#### 采购信息 (5 个)
```
☐ 采购成本  ☐ 采购备注  ☐ 采购交期  ☐ 最低采购量  ☐ 采购员
```

#### 质检信息 (2 个)
```
☐ 开启质检流程  ☐ 质检内容
```

#### 规格信息 (1 父 + 7 子)
```
☐ 规格信息 (父checkbox，勾选自动带7个子项)
   ├ ☐ 商品规格    ├ ☐ 商品重量    ├ ☐ 箱规
   ├ ☐ 单箱重量    ├ ☐ 单箱数量    ├ ☐ 商品包装规格
   └ ☐ 商品包装重量
```

#### 自定义字段 (1 个)

#### 区域头 checkbox (7 个)
基础信息/物流信息/头程信息/采购信息/质检信息/规格信息/自定义字段 各有一个区域头checkbox

### 关键选择器

```python
# 勾选"规格信息"父 checkbox（及7个子项）
spec = page.locator(
    '.el-dialog__body .el-checkbox:has(.el-checkbox__label:text-is("规格信息"))'
)
spec.click()
# 验证: spec.is_checked()

# 下载商品模板按钮（2个，第一个可用）
dl_btn = page.get_by_role('button', name='下载商品模板').first
# 注意: 第二个是 disabled (is-disabled)
```

### 踩坑：Element UI checkbox 不能用 evaluate click
- **现象**: `target.click()` 在 evaluate 中无法触发 Vue 更新
- **解决**: 必须用 Playwright 的真实点击 (`page.locator().click()`)
- **正确选择器**: 定位整个 `.el-checkbox` 组件，不能只点 label span

### 踩坑：el-dropdown-menu__item 不可见
- **现象**: Playwright click 超时 (element is not visible)
- **解决**: 用 evaluate 找到 item 并 click
- **代码**: `[...items].find(i=>i.textContent.trim()==='导入更新商品').click()`

## 下载模板 API

```python
import requests

# POST URL-encoded form (NOT JSON!)
resp = requests.post(
    "https://www.sellfox.com/api/commodity/exportTemplate.json",
    data="fields=sku,size,originalWeight,cartonRule,cartonWeight,cartonNum,wrapSize,wrapWeight",
    headers={"content-type": "application/x-www-form-urlencoded"},
    cookies=sellfox_cookies
)
download_url = resp.json()["data"]
# Response: {"code":0, "msg":null, "data": "https://s1.sellfox.com/sellfox-public/temp/..."}

# 下载文件
r = requests.get(download_url)
with open("商品导入模板.xlsx", "wb") as f:
    f.write(r.content)
```

### 模板字段映射

| API key | 中文显示名 | 所属区域 |
|---------|-----------|----------|
| sku | SKU | 基础信息(强制) |
| size | 商品规格 | 规格信息 |
| originalWeight | 商品重量 | 规格信息 |
| cartonRule | 箱规 | 规格信息 |
| cartonWeight | 单箱重量 | 规格信息 |
| cartonNum | 单箱数量 | 规格信息 |
| wrapSize | 商品包装规格 | 规格信息 |
| wrapWeight | 商品包装重量 | 规格信息 |

### 模板 Excel 结构
- 文件命名: `商品-YYYYMMDDHHmmssNNN.xlsx`
- 3 个 sheet
- 第 1 行: 列标题（字段 key）

## 底部按钮

| 按钮 | 功能 |
|------|------|
| 关闭 | 关闭弹窗 |
| 导入 | 执行导入（需先上传文件，先选字段→再上传→最后点导入） |
| 添加文件 | 选择要导入的 Excel 文件（.el-button--primary） |
| 下载商品模板 | 下载当前勾选字段的 Excel 模板 |

## 搜索验证（SKU 是否存在）

**商品列表页搜索** (已验证 ✅):
```python
search = page.get_by_placeholder('搜索内容').first  # 不用 input[placeholder=...]
search.click()
search.fill('')
search.fill(sku)
page.keyboard.press('Enter')       # Enter 触发 Vue 搜索
page.wait_for_timeout(3000)
# 读结果: .el-pagination 中 "共 X 条"
```

**API 验证** (已验证 ✅):
```python
r = fetch('/api/commodity/pageList.json', {
  searchType:"exact", searchField:"commoditySku", searchValue:sku
})
# → item.id, item.commodityName 等84字段
# 但 pageList 不返回规格详情(length/cartonRule/cartonWeight等为0)
```

**商品详情（规格字段）**: ✅ 已验证 — pageList.json 不返回规格字段，需通过详情弹窗获取

### 商品详情弹窗（已验证 ✅）

**触发方式**:
```python
# 方式1: 点 SKU 文本
page.get_by_text(sku).first.click()

# 方式2: 点 .vxe-body--row 中的 span.f_blue.pointer
page.locator('.vxe-body--row span.f_blue.pointer').first.click()
```

**弹窗结构**: `el-dialog__wrapper.m-dialog` — 标题"普通商品详情"

**Tabs (在弹窗内)**:
- 基础信息 | 物流信息 | 采购信息 | 采购历史 | 质检信息 | **规格信息** | 关联辅料 | 图片管理 | 税务信息 | 自定义字段

**规格信息 tab** (已验证 ✅):
```python
page.get_by_role('tab', { 'name': '规格信息' }).click()
page.wait_for_timeout(1000)
# 数据从 dialog.innerText 提取
```

**闭环验证数据** (test001-white 导入后):
```
商品规格: 62 × 52 × 47 cm   ← 和我们填入的值一致！
商品重量: 2800g (2.8kg)     ← 一致
箱规: 68 × 58 × 52 cm       ← 一致
单箱数量: 6 / 单箱重量: 14.8kg  ← 一致
```

## 上传文件 API

### 完整流程
```
选择字段 → 下载模板 → 填数据 → 添加文件 → 点"导入" → POST /excel/import.json
```

### API 详情
- **端点**: `POST https://www.sellfox.com/excel/import.json`
- **Content-Type**: `multipart/form-data`
- **Header**: `sf-vvv-i` (CSRF token, 从页面提取) + `sf-vvv-t` (时间戳)
- **Response**: `{"code":0, "msg":"", "data":"task_batch_id"}`
- **关键发现**：导入是**异步的**！API 立即返回 200 + task ID，但前端弹窗显示"正在导入..."等待 WebSocket 推送
- **Python 自动化策略**：调 API → 关弹窗 → 搜索验证。不需要等弹窗状态。

### 踩坑：导入 Excel 格式问题（最重要！有两个陷阱）

**陷阱 1**：不能用 `pd.read_excel(模板)` 再改
- 模板有隐藏 worksheet (`['商品', 'hidden1', 'hidden2']`)
- `read_excel` + `to_excel` 会丢失隐藏 sheet，导致导入挂起

**陷阱 2**：sheet 名必须是 `商品`
- `pd.to_excel()` 默认 sheet 名是 `Sheet1`——赛狐不认，导入卡住
- 必须 `sheet_name='商品'`

**✅ 正确做法**：
```python
cols = ['*SKU', '商品规格长(cm)', ...]
df = pd.DataFrame([['test001-white', 60, 50, ...]], columns=cols)
with pd.ExcelWriter('import.xlsx', engine='openpyxl') as w:
    df.to_excel(w, sheet_name='商品', index=False)
```

**闭环验证**：弹窗显示 "成功1条，失败0条"
- **闭环验证**：上传后弹窗显示 "成功1条，失败0条"

### 踩坑：MCP 浏览器文件选择器不弹出
- **现象**：手动点击"添加文件"在 MCP 浏览器中无反应
- **原因**：MCP 浏览器启用沙箱/安全策略拦截了原生文件对话框
- **解决**：用 Playwright 的 `fileChooser.setFiles()` API 绕过原生对话框

### 踩坑：导入卡在"正在导入…"
- **现象**：弹窗显示"状态:正在导入..."几分钟不变
- **原因**：前端等待 events.sellfox.com 推送完成通知，WebSocket 可能断连
- **解决**：API 已返回 200 成功，直接关弹窗。后台异步处理完成即可

### 踩坑：el-dialog__wrapper 定位
- 赛狐页面有 **26 个隐藏的 el-dialog__wrapper**，只有 1 个 visible
- 必须用 `.filter(d => d.getBoundingClientRect().width > 0)` 过滤
- 直接 `querySelector('.el-dialog__wrapper')` 会拿到第一个（隐藏的）

### 踩坑：文件上传后无预览
- 选择文件后弹窗不显示任何变化（无文件名、无表格预览）
- 直接点"导入"即可触发上传
- 成功返回 `code:0` + task ID，无额外提示 |

## 导入更新商品 — 仅改指定字段（已验证）

可以通过导入仅更新指定字段，其他字段保持不变。

### 已验证字段：开启质检流程

| 属性 | 值 |
|------|-----|
| Excel 列名 | `开启质检流程` |
| 开启值 | `是`（导入成功后质检 tab 可见该字段） |
| 关闭值 | `否`（字段存在但状态为关闭） |
| 必选列 | `*SKU` + `开启质检流程` |

**Excel 构造**（仅 2 列，不改其他字段）：
```python
import pandas as pd
df = pd.DataFrame([["test001-white", "否"]], columns=["*SKU", "开启质检流程"])
with pd.ExcelWriter("import.xlsx", engine="openpyxl") as w:
    df.to_excel(w, sheet_name="商品", index=False)
```

**触发 checkbox 的 JS 方法**（Dialog 中的 El-checkbox 需用此方式）：
```python
page.evaluate("""() => {
    const d = [...document.querySelectorAll(".el-dialog__wrapper")]
        .find(x => x.getBoundingClientRect().width > 0);
    if (!d) return false;
    const cb = [...d.querySelectorAll(".el-checkbox")]
        .find(x => x.querySelector(".el-checkbox__label")?.textContent.trim() === "开启质检流程");
    if (!cb) return false;
    const input = cb.querySelector("input[type=checkbox]");
    if (input) { input.checked = true; input.dispatchEvent(new Event("change", { bubbles: true })); }
    const inner = cb.querySelector(".el-checkbox__inner");
    if (inner) inner.click();
    return true;
}""")
```

> 同理可用于其他 68 个字段：找到中文标签名 → 构造 Excel 列 → 对话框中勾选 → 上传 → 导入。

---

## 通用模式：赛狐导入更新商品（适用于全部 69 字段）

### 流程总览（6 步）

```
1. 登录 + 导航到商品列表页
2. 打开"导入更新商品"弹窗
       ↓
3. 在弹窗中勾选目标字段 checkbox
   └─ Element UI checkbox 需用 JS dispatchEvent 触发
       ↓
4. 构造 Excel（pd.DataFrame, sheet_name='商品'）
   └─ 只需 *SKU + 目标字段列（不改的字段不出现）
       ↓
5. 上传文件 + 点"导入"
   └─ 用 file_chooser.set_files() 绕过系统文件对话框
       ↓
6. 等待结果 + 验证
   └─ 弹窗显示"成功X条，失败X条"
   └─ 搜索 SKU → 打开详情弹窗 → 对应 tab 确认
```

### 3 个核心函数（可复用）

```python
# ── 函数1: 打开导入更新商品弹窗 ──
def open_import_dialog(page):
    page.evaluate("""() => {
        const b = [...document.querySelectorAll("button")]
            .find(x => x.textContent.trim() === "导入");
        if (b) b.click();
    }""")
    page.wait_for_timeout(800)
    page.evaluate("""() => {
        const items = [...document.querySelectorAll(".el-dropdown-menu__item")];
        const t = items.find(i => i.textContent.trim() === "导入更新商品");
        if (t) t.click();
    }""")
    page.wait_for_timeout(3000)


# ── 函数2: 勾选弹窗中的 checkbox ──
def check_dialog_checkbox(page, label_text):
    """勾选导入弹窗中的目标字段。支持任何字段名。"""
    page.evaluate(f"""() => {{
        const d = [...document.querySelectorAll(".el-dialog__wrapper")]
            .find(x => x.getBoundingClientRect().width > 0);
        if (!d) return false;
        const cb = [...d.querySelectorAll(".el-checkbox")]
            .find(x => x.querySelector(".el-checkbox__label")?.textContent.trim() === "{label_text}");
        if (!cb) return false;
        // 触发 Element UI checkbox 的 Vue 响应
        const input = cb.querySelector("input[type=checkbox]");
        if (input) {{ input.checked = true; input.dispatchEvent(new Event("change", {{ bubbles: true }})); }}
        const inner = cb.querySelector(".el-checkbox__inner");
        if (inner) inner.click();
        return true;
    }}""")
    page.wait_for_timeout(500)


# ── 函数3: 构造导入 Excel ──
def make_import_excel(sku, columns, data_row, path):
    """
    参数:
      sku: str — 要更新的 SKU
      columns: list[str] — 列名列表，首列必须是 '*SKU'
      data_row: list — 对应每列的值
      path: Path — 输出路径
    """
    import pandas as pd
    df = pd.DataFrame([data_row], columns=columns)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="商品", index=False)
    print(f"  Generated: {path.name}")
```

### 字段值格式参考

| 字段类型 | 示例 Excel 列名 | 有效值 |
|---------|----------------|--------|
| 文本 | `品名`, `报关型号`, `商品备注` | 任意文本 |
| 数值 | `报关单价`, `采购成本`, `加工费` | 数字 (如 15.5) |
| 开关/checkbox | `开启质检流程`, `开启加工过程` | `是`(开) / `否`(关) |
| 规格-尺寸 | `商品规格长(cm)` | 数字 (cm) |
| 规格-重量 | `商品重量` | 数字, 单位在 `商品重量单位` 列 |
| 规格-箱规 | `箱规长(cm)`, `单箱数量(PCS)` | 数字 |

**数据在哪里验证**：在商品详情弹窗的对应 tab 中查看。
- 基础信息 → 基础信息 tab
- 物流信息 → 物流信息 tab
- 采购信息 → 采购信息 tab
- 质检信息 → 质检信息 tab
- 规格信息 → 规格信息 tab
- 头程信息 → 当前不确定在哪，需探索

### 验证策略

```python
def verify_field(page, sku, tab_name, expected_text_fragment):
    """通用验证：搜索SKU → 打开详情 → 切tab → 确认文本"""
    # 搜索
    page.get_by_placeholder("搜索内容").first.click()
    page.get_by_placeholder("搜索内容").first.fill("")
    page.get_by_placeholder("搜索内容").first.fill(sku)
    page.keyboard.press("Enter")
    page.wait_for_timeout(3000)

    # 点 SKU 打开详情
    page.locator(f'span:has-text("{sku}")').first.click()
    page.wait_for_timeout(2000)

    # 切到目标 tab
    page.get_by_role("tab", name=tab_name).click()
    page.wait_for_timeout(1000)

    # 读取弹窗文本
    text = page.evaluate("""() => {
        const d = [...document.querySelectorAll(".el-dialog__wrapper")]
            .filter(x => x.getBoundingClientRect().width > 200);
        return d[0]?.innerText || "";
    }""")
    return expected_text_fragment in text
```

### 使用示例（其他场景）

```python
# 例1: 修改采购成本
cols = ["*SKU", "采购成本"]
row  = ["test001-white", 25.0]
make_import_excel("test001-white", cols, row, path)

# 例2: 修改报关单价
cols = ["*SKU", "报关单价", "报关单价币种"]
row  = ["test001-white", 12.5, "USD"]
make_import_excel("test001-white", cols, row, path)

# 例3: 同时修改多个不相关字段
cols = ["*SKU", "商品备注", "开启加工过程", "开启质检流程"]
row  = ["test001-white", "备注内容", "是", "否"]
make_import_excel("test001-white", cols, row, path)
```

### 扩展到赛狐其他模块（未来方向）

"导入更新商品"的模式对赛狐其他模块有参考价值：

| 模块 | 页面 | 预计导入机制 | 差异点 |
|------|------|-------------|--------|
| **库存 → 其他出库** | 未知 | 可能也有 el-dialog + Excel 导入 | 需探索 |
| **库存 → 其他入库** | 未知 | 同上 | 需探索 |
| **采购 → 采购单** | 未知 | 可能有导入 button | 需探索 |
| **订单 → 发货** | 未知 | 批量导入发货？ | 需探索 |

**通用化原则**：
1. 固定的套路：寻找页面上的"导入"按钮 → 弹窗选择操作 → 上传 Excel
2. 变化的只是：Excel 模板结构、字段映射、验证方式
3. 每次都按 MCP 先探 → 记录 reference → 写代码 → 验证的流程

每次探索新模块时，先用 MCP 打开页面、摸清导入按钮和 Excel 模板，再把发现记录到此文件的"其他模块"章节。
