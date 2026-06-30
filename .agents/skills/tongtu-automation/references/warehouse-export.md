# 通途 — 仓库导出页面 (Warehouse Goods Balance)

> 最后更新: 2026-05-19
> 页面: `https://erp102.tongtool.com/warehouse/goodsbalance/index.htm`

---

## 页面布局

```
┌─────────────────────────────────────────────────┐
│  顶部导航: 首页 仓储 采购 订单 物流 财务 ...    │
├─────────────────────────────────────────────────┤
│  子菜单: 货位库存 库存结存 库龄 收发明细 ...    │
├─────────────────────────────────────────────────┤
│  筛选区:                                        │
│  [全部(非FBA)▼] [已启用▼]                        │
│                                                   │
│  仓库列表 (togglebutton 组):                     │
│  [CENTRADE] [FZHPoland-covers] [皮壳仓库] ...     │
├─────────────────────────────────────────────────┤
│  工具栏: [导出Excel] [导出选中产品数据] [...]     │
├─────────────────────────────────────────────────┤
│  数据表格 (ExtJS grid, 19列):                    │
│  SKU | 品名 | 规格 | FNSKU | 库存 | 头程运费 |...│
├─────────────────────────────────────────────────┤
│  分页器 (底部)                                   │
└─────────────────────────────────────────────────┘
```

## DOM 结构

### 仓库选择器（ExtJS togglebutton）

```html
<div id="warehouseDisableDiv">
  <a class="toggle_btn_down">CENTRADE</a>      <!-- 已选中 -->
  <a class="toggle_btn">FZHPoland-covers</a>   <!-- 未选中 -->
  <a class="toggle_btn">FZH-DANEEY-皮壳仓库</a>
  ...
</div>
```

### 导出按钮

```html
<a onclick="exportExcelPage()" class="...">导出Excel</a>
```

⚠️ 页面有 **13 个** `text=导出Excel` 的同名按钮（FBA、FBF、Shein、Temu 等各平台的导出），
必须用 `onclick="exportExcelPage()"` 精确定位库存清单的导出按钮。

### 筛选条件（ExtJS togglebutton）

```html
<!-- 仓库类型: "全部(非FBA)" vs "FBA" -->
<div id="allWarehouseTypeBtn"><a class="toggle_btn_down">全部(非FBA)</a></div>

<!-- 仓库状态: "已启用" vs "已停用" -->
<div id="statusBtn"><a class="toggle_btn_down">已启用</a></div>
```

## 完整操作流程（MCP 实测）

```
1. 导航到库存结存 URL
       ↓
2. 检测 #warehouseDisableDiv 可见 = 已登录
   (否则跳转登录页等待手动登录)
       ↓
3. 选仓库
   a. 定位 #warehouseDisableDiv a.toggle_btn[has_text=仓库名]
   b. 如果已选中(toggle_btn_down): 先切到其他仓库再切回来
      (规避通途 Bug: ExtJS 数据表格不加载)
   c. 点击目标仓库 → 等 8 秒
       ↓
4. 确认筛选: "全部(非FBA)" + "已启用"
       ↓
5. 导出: a[onclick="exportExcelPage()"] → expect_download
       ↓
6. 文件保存到 downloads/
       ↓
7. 生成导入文件 (generate_tongtu_import.py)
```

## 踩坑

### 坑 1：通途 Bug — 数据表格不加载
- **现象**：仓库切换后 togglebutton 显示已选中，但 ExtJS grid 无数据
- **排查**：`page.evaluate("exportExcelPage()")` 报 `Cannot read properties of undefined (reading 'table')`
- **解决**：先切到其他仓库等 3s，再切回来等 8s

### 坑 2：13 个同名导出按钮
- 页面有 FBA、FBF、Shein、Temu 等各平台导出，全是 text="导出Excel"
- **必须**用 `a[onclick="exportExcelPage()"]` 精确定位

### 坑 3：下载超时
- `expect_download(timeout=60000)` 必须在 click 外包围
- 下载开始后立即 save_as（在 with 块内），否则超时
