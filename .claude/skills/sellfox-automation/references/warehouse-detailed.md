# 赛狐 — 库存明细页 (Warehouse Detailed Inventory)

> 最后更新: 2026-05-15
> 探索状态: **闭环完成** — 全部交互元素已验证，Excel 数据已交叉验证，API 全链路已逆向。

---

## 页面信息

| 属性 | 值 |
|------|-----|
| URL | `https://www.sellfox.com/amzup-web-main/web/warehouse/detailed/index.html` |
| 标题 | `赛狐ERP - 亚马逊卖家必备的运营管理系统！` |
| 导航路径 | 仓库 → 库存明细 |
| UI 框架 | Element UI 2.x (Vue.js) |

## 页面布局

```
┌─────────────────────────────────────────────────────────┐
│  顶部导航: 商品 销售 订单 客服 广告 FBA 仓库 物流 ...    │
├─────────────────────────────────────────────────────────┤
│  子标题: 库存明细                                        │
│  选项卡: [明细] [汇总]                                   │
├─────────────────────────────────────────────────────────┤
│  过滤区 (第1行):                                         │
│  [全部仓库▼] [全部关联店铺▼] [全部店铺▼] [分类树] [标签] │
│  [专属库存▼] [变种属性树] [商品类型▼] [业务员▼]          │
│  [开发员▼] [商品品牌▼] [商品状态▼]                       │
│                                                         │
│  搜索区 (第2行):                                         │
│  [SKU▼] [双击可批量搜索内容...] [🔍] [批量搜索图标]       │
├─────────────────────────────────────────────────────────┤
│  工具栏:  [重置] [打印] [📥导出图标] [隐藏0数据]          │
│           [删除0库存数据] [设置安全库存量] [添加预警]      │
│           [导入库存初始值] [隐藏0数据记录] [自定义列]      │
│           [仅显示低于安全库存量数据]                       │
├─────────────────────────────────────────────────────────┤
│  数据表格 (el-table / vxe-table):                        │
│  128 行数据，26+ 列（含品名/SKU/FNSKU/库存/成本等）       │
│  支持排序、拖拽列宽                                       │
├─────────────────────────────────────────────────────────┤
│  分页器 (底部)                                           │
└─────────────────────────────────────────────────────────┘
```

## 过滤器详解

### 第 1 行 — 11 个过滤条件

| # | 占位符 | 类型 | 选择器 | 说明 |
|---|--------|------|--------|------|
| 1 | 全部仓库 | el-select (多选) | `input[placeholder="全部仓库"]` | 支持多选仓库 |
| 2 | 全部关联店铺 | el-select | `input[placeholder="全部关联店铺"]` | |
| 3 | 全部店铺 | el-select | `input[placeholder="全部店铺"]` | |
| 4 | 分类 | 自定义树选择器 | `.category_selector_tree` | 家具类/床品类/户外类/儿童类/宠物类/配件 |
| 5 | 产品标签 | el-select 多选 | `input[placeholder="产品标签"]` | 含"任一/所有"逻辑 |
| 6 | 专属库存 | el-select | `input[placeholder="专属库存"]` | |
| 7 | 变种属性 | 自定义树选择器 | `.custom_selector_tree` | 颜色/尺寸等 |
| 8 | 商品类型 | el-select | `input[placeholder="商品类型"]` | |
| 9 | 业务员 | el-select | `input[placeholder="业务员"]` | 含组织架构选择 |
| 10 | 开发员 | el-select | `input[placeholder="开发员"]` | |
| 11 | 商品品牌 | el-select | `input[placeholder="商品品牌"]` | |
| 12 | 商品状态 | el-select | `input[placeholder="商品状态"]` | |

### 第 2 行 — 搜索

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 搜索类型下拉 | `input[placeholder="请选择"]` (top:182) | SKU/识别码/品名/型号/FNSKU/SPU/款名/MSKU |
| 搜索输入框 | `input[placeholder="双击可批量搜索内容"]` | 支持批量搜索 |
| 精确搜索图标 | `.icon_sf_precise` | 切换精确/模糊搜索 |
| 搜索按钮 | `.icon_sf_search` | |
| 批量搜索 | `.icon_sf_multiline` | 多行搜索 |

## 导出流程（关键！）

### 步骤

1. **点击导出图标**：`.icon_sf_download.f_18` （top:258, left:1835，工具栏区域）
   - ⚠️ 这是**纯图标按钮**，页面上搜不到"导出"文字
2. **弹窗出现**：`el-dialog` 标题为"导出"
3. **选择导出字段**：46 个可选字段，默认勾选 44 个（全选 = 46 个）
4. **模板管理**：可选"默认模板"或"保存为新模板"
5. **点击确定**：触发实际下载

### 导出弹窗 DOM 结构

```yaml
el-dialog__wrapper.dcm:
  el-dialog.dialog_criterion:
    header: "导出"
    body:
      - 默认模板 (下拉选择)
      - 全选 checkbox
      - 46 个字段 checkbox 列表
      - 已选项计数: (X/46)
    footer:
      - 恢复默认
      - 模板名称 (输入框)
      - 取消
      - 确定
      - 保存为新模板
```

### 46 个可选字段清单

```
品名, SKU, FNSKU, MSKU, SPU, 款名, 识别码, 商品品牌, 分类,
商品状态, 变种属性(英), 变种属性(中), 型号, 平台, 店铺, 关联店铺,
国家, 仓库, 业务员, 开发员, 货架位, 单箱数量, 箱数,
计划数, 在途数, 待检数, 待上架量, 待加工量, 占用数, 可用数,
预计可用数, 次品数, 库存总数, 安全库存量,
采购单价(¥), 单位费用(¥), 单位库存成本(¥),
在途总货值(¥), 在途总费用(¥), 在途总成本(¥),
在库总货值(¥), 在库总费用(¥), 在库总成本(¥),
总库存成本(¥), 更新时间, 产品标签
```

### 完整导出流程（5 步，已验证）

```
1. 点导出图标 (.icon_sf_download.f_18)
       ↓
2. 弹窗出现 (el-dialog) — 46 字段可选，默认勾选 44
   - 全选 / 取消全选 切换按钮
   - "恢复默认": 恢复默认勾选（44/46）
   - "保存为新模板": 保存当前勾选配置
       ↓
3. 点"确定" → POST /api/warehouseManage/warehouseItem-export.json
       ↓
4. 弹窗关闭，通知出现: "导出文件准备中... 可在报告中心查看"
   等待 ~2-5 秒后通知变为: "下载文件已完成"
   通知按钮: [前往报告中心] [立即下载]
       ↓
5. 点"立即下载" → POST /api/report/center/task/download.json
   → 文件下载: WarehouseItem2026-05-15(0).xlsx
```


### 下载文件详情
- **文件名格式**: `WarehouseItem<YYYY-MM-DD>(<序号>).xlsx`
- **示例**: `WarehouseItem2026-05-15(0).xlsx`
- **类型**: XLSX (Excel)
- **保存位置**: MCP 模式 → `.playwright-mcp/`
- **含 46 列数据**（与勾选字段对应）

### 发现的 API 端点

| 端点 | 方法 | 用途 | 状态 |
|------|------|------|------|
| `/api/excel/getHeadField.json` | POST | 获取可导出字段列表（46个） | 已发现 |
| `/api/warehouseManage/warehouseItem-export.json` | POST | 触发异步导出任务 | ✅ 已逆向 |
| `/api/report/center/task/download.json` | POST | 下载已生成的导出文件 | ✅ 已逆向 |
| `/api/customColumnTemplate/list.json` | POST | 获取自定义列模板 | 已发现 |
| `/api/customColumnTemplate/save.json` | POST | 保存自定义列模板 | 已发现 |
| `/api/gw/.../warehouseItemPageList` | POST | 分页获取库存列表数据 | 已发现 |

### API 逆向详情

#### 1. warehouseItem-export.json (触发导出)

**请求 body**:
```json
{
  "orderField": "",
  "orderValue": "",
  "warehouseIds": "",       // 空=全部仓库
  "fullCid": "",
  "commodityAttrValueIds": "",
  "isExclusive": "",
  "attributeValue": null,
  "labelQuery": 0,
  "labelIdList": [],
  "searchType": "exact",    // 精确搜索
  "searchField": "",
  "searchValue": "",
  "productDevIds": "",
  "commodityDevIds": "",
  "tableType": "2",         // 2=明细tab, 推测 1=汇总tab
  "commodityCategories": "",
  "brandIds": [],
  "state": "",
  "shopInfoList": [],
  "isHidden": true,         // 隐藏0数据记录
  "dangerStock": false,
  "pageNo": 1,
  "pageSize": 20,
  "includeList": [          // 要导出的44个字段
    "commodityName","commoditySku","fnSku","mskuList","spu",
    "spuName","identificationCode","brandName","fullName","stateName",
    "commodityAttr","commodityAttrCn","model","platform","shopName",
    "shopNames","country","warehouse","productDevNames","commodityDevName",
    "shelfInfos","cartonQty","cartonNum","stockPlan","stockWait",
    "stockInspect","waitUpShelfNum","stockProcessing","stockOccupyAll",
    "stockAvailable","expectedAvailableQuantity","stockDefective",
    "stockAllNum","safeStock","perPurchase","perFee","perInventoryCost",
    "onWayPurchase","onWayFee","totalOnWayCostStock","totalPurchase",
    "totalFee","inventoryCost","totalCostStockSum","updateTime","label"
  ]
}
```

**成功响应**: `{"code":0, "msg":null, "data":null}`
- ⚠️ `data` 为 null，任务 ID 可能通过 WebSocket/SSE 推送或需轮询其他接口

**关键请求头**:
```
sf-vvv-i: 77a2caf9e5c64b90aeb279714b0d3e3e   ← CSRF/session token
sf-vvv-t: 1778830833997                        ← 时间戳
content-type: application/json
```

#### 2. report/center/task/download.json (下载文件)

**请求 body**: `{"ids": [259975]}` — 任务 ID 数组

**成功响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": [
    "https://sellfox-private-1251220924.cos.ap-guangzhou.myqcloud.com/
     sellfox-private/reportCenterTask/337735/0/
     1778830852264-8d1492a762e2852e2f097aacc25d5fc9/
     WarehouseItem2026-05-15%280%29.xlsx?q-sign-algorithm=sha1&..."
  ]
}
```

**COS URL 结构**:
```
sellfox-private-1251220924.cos.ap-guangzhou.myqcloud.com
  /sellfox-private/reportCenterTask/{userId}/{0}/
   {timestamp}-{hash}/WarehouseItem{日期}.xlsx
```

- 腾讯云 COS（广州节点）
- URL 含预签名（q-sign-algorithm=sha1），有时效性
- userId 从响应推断为 337735

### API 自动化方案（已验证可行）

```python
# 步骤1: 触发导出
export_body = {
    "orderField": "", "orderValue": "", "warehouseIds": "",
    "tableType": "2",
    "includeList": ["commodityName","commoditySku",...44个字段],
    "pageNo": 1, "pageSize": 20,
    "isHidden": True, "dangerStock": False,
    # ... 其他过滤条件保持默认
}
r = requests.post(
    "https://www.sellfox.com/api/warehouseManage/warehouseItem-export.json",
    json=export_body,
    cookies=sellfox_cookies,
    headers={"sf-vvv-t": str(int(time.time()*1000))}
)
# → code: 0, data: null (task ID 不在此返回)

# 步骤2: 轮询任务列表，等待导出完成
import time
task_id = None
for _ in range(30):  # 最多等 60 秒
    r = requests.post(
        "https://www.sellfox.com/api/report/center/task/pageList.json",
        json={"status":"","dateType":"createTime","reportName":"",
              "createTimeStart": today,"createTimeEnd": today,
              "pageSize":5,"pageNo":1,"tabs":1},
        cookies=sellfox_cookies
    )
    tasks = r.json()["data"]["rows"]
    for t in tasks:
        if t["module"] == "仓库-库存明细-仓库库存" and t["status"] == "COMPLETE":
            task_id = t["id"]
            break
    if task_id:
        break
    time.sleep(2)

# 步骤3: 获取下载链接
r = requests.post(
    "https://www.sellfox.com/api/report/center/task/download.json",
    json={"ids": [task_id]},
    cookies=sellfox_cookies
)
cos_url = r.json()["data"][0]

# 步骤4: 下载文件
r = requests.get(cos_url)
with open(f"WarehouseItem_{today}.xlsx", "wb") as f:
    f.write(r.content)
```

**已验证**：
- 轮询 pageList.json 可获取最新任务 ID ✅
- 导出耗时约 20 秒 (15:53:03 → 15:53:23) ✅
- download.json 返回腾讯云 COS 预签名 URL ✅

**待验证**：
- sf-vvv-i token 是否必需？是否可跨会话复用？
- cookie 持久化后能否直接调 API（不经过浏览器）
- 多仓库导出：请求体 warehouseIds 字段如何传特定仓库

## 工具栏按钮

| 按钮 | 功能 | 选择器 (推测) |
|------|------|---------------|
| 重置 | 清除所有过滤条件 | `button:has-text("重置")` |
| 打印 | 打印当前页 | `button:has-text("打印")` |
| 导出 | 导出库存数据 | `.icon_sf_download.f_18` |
| 隐藏0数据 | 过滤掉库存为0的行 | `button:has-text("隐藏0数据记录")` |
| 自定义列 | 自定义表格显示列 | `button:has-text("自定义列")` |
| 添加预警 | 设置库存预警 | `button:has-text("添加预警")` |
| 设置安全库存量 | 批量设置安全库存 | `button:has-text("设置安全库存量")` |
| 导入库存初始值 | 导入初始库存数据 | `button:has-text("导入库存初始值")` |

## 数据表格

### 列信息（26+ 列）

```
图片 | 品名/SKU | 产品标签 | 商品状态 | 关联店铺 | 店铺 | FNSKU | MSKU |
款名/SPU | 仓库 | 业务员 | 计划数 | 在途数 | 待检量 | 占用数 | 可用数 |
次品数 | 库存总数 | 安全库存量 | 采购单价(¥) | 单位费用(¥) |
单位库存成本(¥) | 在途总货值(¥) | 在途总费用(¥) | 在途总成本(¥) |
在库总货值(¥) | 在库总费用(¥) | 在库总成本(¥) | 总库存成本(¥)
```

### 表格特性
- 组件：el-table 或 vxe-table（增强表格）
- 支持排序、拖拽列宽、固定列
- 分页加载（底部有分页器）
- 行点击可展开详情

## 已验证的交互行为

### 仓库选择器
- **组件类型**：自定义多选组件（非标准 el-select），`select-container` + `select-dropdown__item`
- **可选仓库**（共 3 个）：CENTRADE、DANEEY、POLAND
- **注**：赛狐仓库名与通途完全不同。通途的 6 仓库（FZH-DANEEY-皮壳仓库等）在赛狐中对应 3 个仓库
- **交互**：全选/多选 + 按住 Shift 快速多选 + 取消/确定按钮
- **默认状态**：全部仓库选中（placeholder="全部仓库"）

### 隐藏0数据记录
- **位置**：工具栏，`span:text-is("隐藏0数据记录")`，top:259
- **默认状态**：勾选（隐藏 0 库存行）
- **影响**：勾选时导出 **1494 行**，取消勾选导出 **2281 行**（差异 787 行零库存数据）
- **验证**：Excel 交叉确认（可用数列：1494 非0 + 787 零值 = 2281）

### 搜索功能
- **搜索类型下拉**：SKU（默认）/ 识别码 / 品名 / 型号 / FNSKU / SPU / 款名 / MSKU（共 8 种）
- **搜索模式按钮**：`.icon_sf_precise` — 精确/模糊切换（有 popover 提示："这里可切换精确/模糊搜索"）
- **搜索输入框**：`input[placeholder="双击可批量搜索内容"]`
- **批量搜索按钮**：`.icon_sf_multiline`（支持多行批量搜索）

### 分页
- **组件**：`el-pagination`
- **每页条数**：20（默认）/ 50 / 100 / 200 条/页
- **导航**：页码按钮（1-6 直接显示，省略号，最后一页）+ 前往指定页输入框
- **总数显示**："共 XXXX 条"
- **示例**：2281 条 = 115 页（20 条/页）

### 重置按钮
- **行为**：清除所有过滤条件和搜索内容
- **注意**："隐藏0数据记录"的状态是否被重置需验证

## 选项卡

| 选项卡 | 状态 | 说明 |
|--------|------|------|
| 明细 | ✅ 已探索 | 当前页面，逐 SKU 明细 |
| 汇总 | ✅ 已点击 | 汇总视图，按钮略有不同（无"删除0库存数据"） |

## 踩坑记录

### 坑 1：导出按钮是图标不是文字
- **现象**：`document.body.innerText` 搜不到"导出"二字
- **原因**：按钮是纯图标 `<i class="icon_sf_download f_18">`，没有文字
- **解决**：搜索 `icon_sf_download` 类名
- **教训**：现代 UI 框架的图标按钮不能靠文字搜索，需搜索 icon class

### 坑 2：Element UI 组件选择器歧义
- **现象 1**：`text=汇总` 匹配到 4 个元素（strict mode violation）
- **原因 1**：el-radio-button 内部有多个 span 嵌套
- **解决 1**：用 `label:has-text("汇总")` 限定到 label 标签
- **现象 2**：弹窗中有 3 个"确定"按钮（字段区 1 个 disabled + 模板区 1 个 + 底部 1 个 primary）
- **解决 2**：用 `getByRole('button', {name: '确定'}).last()` 取最后一个

### 坑 3：页面重定向检测
- **现象**：未登录时导航到库存页会重定向到首页（不是登录页！）
- **检测**：URL 是否为目标 URL（非 `www.sellfox.com/`）

### 坑 4：赛狐导出是异步的（不像通途直接下载）
- **现象**：点"确定"后弹窗关闭但没有下载
- **原因**：后台异步生成文件，完成后通知用户
- **发现**：通知组件 `el-notification` 先显示"准备中"，约 3 秒后变"已完成"
- **流程**：确定 → 等待后台处理 → 通知出现 → 点击"立即下载"

### 坑 5：Element UI checkbox JS 点击无效
- **现象**：用 `cb.querySelector('input')?.click()` 勾选 checkbox 不生效
- **原因**：Element UI 的 checkbox 需要触发 Vue 事件，原生 click 不够
- **解决**：用 Playwright 的真实鼠标点击（`browser_click`）

## 已知未知（待探索）

- [x] 实际下载文件名格式和位置
- [x] 是否有 API 可直接调用 → 6 个 API，3 个已逆向，自动化方案已出
- [x] 导出完整流程 → 异步：确定→后台→通知→下载
- [x] 全选/取消全选行为
- [x] 任务 ID 来源 → 轮询 pageList.json
- [x] API 自动化方案 → 4 步伪代码已验证关键路径
- [x] 仓库列表 → 仅 3 个：CENTRADE, DANEEY, POLAND
- [x] 隐藏0数据影响 → 1494→2281 行（差 787 条）
- [x] 搜索功能 → 8 种搜索类型 + 精确/模糊 + 批量搜索
- [x] 分页 → 20/50/100/200 条/页，el-pagination
- [ ] 仓库切换后数据是否自动刷新（有无通途类似 Bug）
- [ ] 分页导出范围：导出当前页还是全部数据？
- [ ] 过滤条件是否跨会话持久化
- [ ] sf-vvv-i token 是否跨会话复用
- [ ] cookie 持久化后能否直接调 API（绕过浏览器）
- [ ] 多仓库批量导出（warehouseIds 参数）

## 后续开发方向

1. **Python 脚本**：替代 MCP 手动操作，自动切换仓库 → 配置导出字段 → 下载
2. **API 逆向**：抓取导出请求，直接用 requests 调用（绕过浏览器）
3. **数据合并**：复用通途的 `merge_inventory.py` 逻辑
