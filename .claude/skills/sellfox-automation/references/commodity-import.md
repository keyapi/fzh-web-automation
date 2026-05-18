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

### 字段区域（从上到下，需要滚动）

| 区域 | 包含字段 | 默认状态 |
|------|----------|----------|
| **基础信息** | SKU(✅已选+禁用), 图片链接, 品名, 开发员, 开发时间, 查看人, 状态, 识别码, 来源, 开启加工过程, 加工费, 分类, 商品品牌, 材质, 型号, 用途, 单位, 商品备注 | SKU强制选中 |
| **物流信息** | 中文报关名, 英文报关名, 报关单价, ~15个报关相关字段 | 全部未选 |
| **头程信息** | 默认头程费用(CNY), 清关HSCODE, 清关单价, ~7个字段 | 全部未选 |
| **采购信息** | 采购成本, 采购备注, 采购交期, 最低采购量, 采购员 | 全部未选 |
| **质检信息** | 开启质检流程, 质检内容 | 全部未选 |
| **规格信息** | 商品规格, 商品重量, 箱规, 单箱重量, 单箱数量, 商品包装规格, 商品包装重量 | 勾选父项→自动勾选7个子项 |
| **自定义字段** | (自定义字段区域) | 全部未选 |

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
| 导入 | 执行导入（需先上传文件） |
| 添加文件 | 选择要导入的 Excel 文件 |
| 准备数据 | ? |
| 下载商品模板 | 下载当前勾选字段的 Excel 模板 |
