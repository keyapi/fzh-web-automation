# 赛狐 — 商品列表 — 导出商品

> 最后更新: 2026-05-19
> 探索状态: **初探完成** — 导出机制与库存明细页一致（icon_sf_download 触发）。

---

## 页面信息

| 属性 | 值 |
|------|-----|
| URL | `https://www.sellfox.com/amzup-web-main/web/commodity/index.html` |
| 导航路径 | 商品 → 商品列表 |
| UI 框架 | Element UI 2.x (Vue.js) |

## 导出按钮

商品列表页的导出按钮和库存明细页**完全一致**：

```python
# 点击导出图标
page.locator(".icon_sf_download.f_18").first.click()
```

**为什么可以复用**：赛狐全平台使用同一套导出组件（`icon_sf_download` + 异步导出 + 报告中心），
仓库页、商品页的导出逻辑完全相同。差异只在弹窗中可选的字段不同。

## 导出流程（5 步）

```
1. 点击导出图标 (.icon_sf_download.f_18)
       ↓
2. 弹窗出现 (el-dialog, 标题="导出")
   字段分区域: 基本信息 | 采购信息 | ... 
   底部按钮: [全选所有] [确定] [取消]
       ↓
3. 点"确定" → 触发后台异步导出
       ↓
4. 通知出现: "导出文件准备中..." → "下载文件已完成"
       ↓
5. 点"立即下载" → 下载文件
```

## 代码实现

```python
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

PAGE_URL = "https://www.sellfox.com/amzup-web-main/web/commodity/index.html"
DOWNLOADS_DIR = Path("downloads")

def export_commodities(page):
    """导出商品列表全部数据"""
    # 1. 点击导出图标
    page.locator(".icon_sf_download.f_18").first.click()
    page.wait_for_timeout(2000)

    # 2. 弹窗出现 → 点确定（默认字段）
    page.evaluate("""() => {
        const btns = document.querySelectorAll('.el-dialog__footer button, .dcm button');
        const ok = [...btns].find(
            b => b.textContent.trim() === '确定' && b.offsetParent
        );
        if (ok) ok.click();
    }""")
    page.wait_for_timeout(3000)

    # 3. 等通知 → 点立即下载
    for _ in range(60):
        try:
            dl_btn = page.locator('button:has-text("立即下载")')
            if dl_btn.count() > 0:
                with page.expect_download(timeout=30000) as dl_info:
                    page.evaluate("""() => {
                        const btns = document.querySelectorAll('button');
                        const dl = [...btns].find(b => b.textContent.includes('立即下载'));
                        if (dl) dl.click();
                    }""")
                download = dl_info.value
                path = DOWNLOADS_DIR / download.suggested_filename
                download.save_as(str(path))
                print(f"  [OK] 下载完成: {path.name} ({path.stat().st_size/1024:.0f} KB)")
                return path
        except:
            pass
        time.sleep(2)
    return None
```

## 导出的字段

### 默认导出字段（已确认）

导出弹窗勾选了默认字段（未全选），实际下载的 Excel 包含 18 列：

| # | 列名 | 说明 |
|---|------|------|
| 0 | SKU | |
| 1 | 品名 | |
| 2 | 商品重量 | |
| 3 | 商品重量单位 | |
| 4 | 商品规格长(cm) | |
| 5 | 商品规格宽(cm) | |
| 6 | 商品规格高(cm) | |
| 7 | 箱规长(cm) | |
| 8 | 箱规宽(cm) | |
| 9 | 箱规高(cm) | |
| 10 | Listing配对状态 | |
| 11 | 单箱重量(kg) | |
| 12 | 单箱数量(pcs) | |
| 13 | 商品包装规格长(cm) | |
| 14 | 商品包装规格宽(cm) | |
| 15 | 商品包装规格高(cm) | |
| 16 | 商品包装重量 | |
| 17 | 商品包装重量单位 | |

### 可选字段（弹窗中可见）

弹窗中可见的字段分组：

**基本信息**:
SKU, 品名, 商品编码, 图片链接, 分类, 识别码, 商品品牌, 材质, 型号, 用途, 单位, spu,
变种属性(中), 变种属性(英), 款名, 组合明细, 关联辅料数, 包含单品(品名), 包含单品(SKU),
Listing配对状态, 状态, 1688配对, 商品备注, 开发员, 查看人, 开启加工过程, 加工费(¥),
创建时间, 来源, 更新时间, 开发时间, 产品标签

**采购信息**:
(待探索具体字段)

## 导出文件信息

| 属性 | 值 |
|------|-----|
| 文件名 | `Commodities{日期}(序号).xlsx` |
| 行数 | ~2216 条（全量数据） |
| 大小 | ~217 KB（18列默认字段） |
| 数据结构 | 第1行=列标题，第2行起=数据 |

## 与库存明细导出的对比

| 维度 | 商品列表导出 | 库存明细导出 |
|------|-------------|-------------|
| 导出图标 | `icon_sf_download.f_18` | `icon_sf_download.f_18` |
| 弹窗标题 | "导出" | "导出" |
| 字段数 | ~30+ (默认18) | 46 (默认44) |
| 字段分组 | 基本信息, 采购信息 | 无分组(46个平铺) |
| 下载机制 | 异步 → 通知 → 立即下载 | 异步 → 通知 → 立即下载 |
| 可复用性 | **与仓库页完全相同** | |

## 后续探索

- [ ] 全量字段清单（通过"全选所有"导出确认）
- [ ] 采购信息的具体字段
- [ ] 搜索/筛选后导出是否只导出当前结果
- [ ] API 方式导出（参考仓库页的 warehouseItem-export.json 模式）
