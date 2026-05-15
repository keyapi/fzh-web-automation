# 赛狐 — Python Playwright 代码片段

> 给 Agent 看的：每个 MCP 验证过的选择器对应的 Python 代码。可直接复制使用。

---

## 1. 登录 + Cookie 持久化

```python
from playwright.sync_api import sync_playwright
from pathlib import Path

PROFILE_DIR = Path("sellfox-profile")  # cookies 自动保存到这里
LOGIN_URL = "https://www.sellfox.com/amzup-web-main/login.html"
PAGE_URL = "https://www.sellfox.com/amzup-web-main/web/warehouse/detailed/index.html"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,     # True=后台, False=可见演示
        accept_downloads=True,
        viewport={"width": 1280, "height": 800},
    )
    page = context.pages[0] if context.pages else context.new_page()

    # 首次：跳到登录页 → 用户手动登录
    page.goto(PAGE_URL, timeout=60000)
    page.wait_for_timeout(5000)

    if "login" in page.url or "sellfox.com/" == page.url.rstrip("/"):
        page.goto(LOGIN_URL, timeout=30000)
        # 等待登录（双重检测）
        for _ in range(150):
            time.sleep(2)
            url = page.url
            if "login" not in url and "sellfox" in url:
                break  # 登录成功
        # 登录后跳仓库页
        page.goto(PAGE_URL, timeout=60000)

    # 等待 SPA 渲染
    page.wait_for_timeout(8000)
    page.keyboard.press("Escape")  # 关闭残留弹窗
```

**陷阱**: Sellfox 登录后跳转 dashboard（不是仓库页），需手动 `page.goto(PAGE_URL)`。

---

## 2. 仓库操作

### 获取全部仓库（API，绕过 UI）
```python
warehouses = page.evaluate("""
  async () => {
    const r = await fetch(
      '/api/gw/sellfox/sellfox-warehouse/sellfox/warehouse/warehouseThirdList',
      { method: 'POST', headers: {'content-type': 'application/json'}, body: '{}' }
    );
    return await r.json();
  }
""")
# 返回: [{id: 279814, name: "CENTRADE"}, {id: 279833, name: "DANEEY"}, ...]
# 排除 type=-1 的虚拟仓库
real_warehouses = [w for w in warehouses["data"] if w["type"] != -1]
```

### UI 打开仓库下拉
```python
# ⚠️ 仓库选择器是自定义组件，非标准 el-select
# 点 input[placeholder="全部仓库"] 打开下拉
page.locator('input[placeholder="全部仓库"]').click()
page.wait_for_timeout(500)

# 可见的仓库选项: .select-dropdown__item
# CENTRADE, DANEEY, POLAND 各一个
```

### API 过滤单仓
```python
# warehouseIds 参数
""                          # 全部仓库
"279814"                    # CENTRADE
"279814,279833"             # CENTRADE + DANEEY
"279814,279833,279841"      # 3 仓全部
```

---

## 3. 搜索操作

### 读取当前搜索类型和模式
```python
# 搜索类型: SKU / 品名 / 识别码 / 型号 / FNSKU / SPU / 款名 / MSKU
search_type = page.evaluate("""
  (() => {
    for (const inp of document.querySelectorAll('input.el-input__inner')) {
      if (['SKU','识别码','品名','型号','FNSKU','SPU','款名','MSKU'].includes(inp.value))
        return inp.value;
    }
    return '?';
  })()
""")

# 搜索模式: fuzzy(模) / exact(精)
mode = page.evaluate(
    "() => document.querySelector('.icon_sf_fuzzy') ? 'fuzzy' : 'exact'"
)
```

### 切换搜索类型 (SKU→品名)
```python
# Step 1: 关残留弹窗
page.keyboard.press("Escape")
page.wait_for_timeout(300)

# Step 2: evaluate 点击 el-select（绕过 Playwright visible check）
page.evaluate("""
  (() => {
    for (const inp of document.querySelectorAll('input.el-input__inner')) {
      if (['SKU','识别码','品名','型号','FNSKU','SPU','款名','MSKU'].includes(inp.value)) {
        const sel = inp.closest('.el-select');
        if (sel) { sel.click(); return; }
      }
    }
  })()
""")
page.wait_for_timeout(500)

# Step 3: 点击可见的下拉选项
target = "品名"  # 或 SKU, 识别码, 型号...
page.evaluate(f"""
  (() => {{
    const items = [...document.querySelectorAll('.el-select-dropdown__item')]
      .filter(i => i.getBoundingClientRect().width > 0);
    const m = items.find(i => i.textContent.trim() === '{target}');
    if (m) m.click();
  }})()
""")
page.wait_for_timeout(500)
```

### 切换精/模
```python
# MCP 验证: 必须点 .search_type_btn (外层容器)，不能直接点 icon
page.locator(".search_type_btn").first.click()
page.wait_for_timeout(300)
```

### 输入关键词搜索
```python
# 搜索框的 placeholder 会动态变化（"搜索内容" ↔ "双击可批量搜索内容"）
# 用两个 placeholder 同时匹配
inp = page.locator(
    "input[placeholder='双击可批量搜索内容'], input[placeholder='搜索内容']"
).first
inp.click()
inp.fill("")       # 清空
inp.fill(keyword)  # 填入关键词
page.keyboard.press("Enter")
page.wait_for_timeout(3000)

# 读取结果数
total = page.evaluate(
    "() => { const p = document.querySelector('.el-pagination');"
    " return p ? p.textContent.match(/共\\s*(\\d+)\\s*条/)?.[1] : '0'; }"
)
```

---

## 4. 导出操作（浏览器点击）

```python
# Step 1: 点击导出图标
page.locator(".icon_sf_download.f_18").first.click()
page.wait_for_timeout(2000)

# Step 2: 弹窗 → 点确定
page.evaluate("""
  (() => {
    const btns = document.querySelectorAll('.el-dialog__footer button, .dcm button');
    const ok = [...btns].find(
      b => b.textContent.trim() === '确定' && b.offsetParent
    );
    if (ok) ok.click();
  })()
""")
page.wait_for_timeout(3000)

# Step 3: 等通知 → 点立即下载
for _ in range(60):
    try:
        dl_btn = page.locator('button:has-text("立即下载")')
        if dl_btn.count() > 0:
            with page.expect_download(timeout=30000) as dl_info:
                page.evaluate("""
                  (() => {
                    const btns = document.querySelectorAll('button');
                    const dl = [...btns].find(b => b.textContent.includes('立即下载'));
                    if (dl) dl.click();
                  })()
                """)
            download = dl_info.value
            download.save_as(f"downloads/{download.suggested_filename}")
            break
    except:
        pass
    time.sleep(2)
```

---

## 5. "隐藏0数据记录" 切换

```python
# ⚠️ 每次新 session 打开页面，此选项默认 ON（1494条）
# 导出前必须检查并切换

# 读取当前总条数
total = int(page.evaluate(
    "() => { const p = document.querySelector('.el-pagination');"
    " return p.textContent.match(/共\\s*(\\d+)\\s*条/)?.[1]; }"
))

# 如果 ~1500 条 → 隐藏0数据打开 → 需要关闭
if total < 2000:
    print("检测到隐藏0数据已启用 → 关闭")
    page.locator('span:text-is("隐藏0数据记录")').first.click()
    page.wait_for_timeout(3000)
    # 验证
    total_after = int(page.evaluate(
        "() => document.querySelector('.el-pagination')"
        ".textContent.match(/共\\s*(\\d+)\\s*条/)?.[1]; }"
    ))
    print(f"  1494 → {total_after} 条")
```

---

## 6. 分页

```python
# 读数
total, page_size, pages = page.evaluate("""
  (() => {
    const p = document.querySelector('.el-pagination');
    if (!p) return [0, 20, 0];
    const t = p.textContent;
    const total = t.match(/共\\s*(\\d+)\\s*条/)?.[1] || '0';
    const m = t.match(/(\\d+)条\\/页/);
    const ps = m ? m[1] : '20';
    return [parseInt(total), parseInt(ps), Math.ceil(total/ps)];
  })()
""")
print(f"{total} 条, {page_size} 条/页, {pages} 页")

# 点第 N 页
page.locator(f".el-pager li:has-text('{page_num}')").first.click()

# 切换每页条数
page.locator('input[placeholder="请选择"]').last.click()
page.locator(f'.el-select-dropdown__item:has-text("{size}条/页")').first.click()
```

---

## 7. API 模式（不打开浏览器）

```python
import requests
from playwright.sync_api import sync_playwright

# 从 profile 提取 cookie
def get_cookies(profile_dir="sellfox-profile"):
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir, headless=True
        )
        cookies = ctx.cookies()
        ctx.close()
    return {c["name"]: c["value"] for c in cookies if "sellfox" in c.get("domain","")}

# 调 API 导出
cookies = get_cookies()
session = requests.Session()
for n, v in cookies.items():
    session.cookies.set(n, v, domain="www.sellfox.com")

# 触发导出
export_body = {
    "warehouseIds": "",  # 空=全部
    "includeList": ["commodityName","commoditySku",...],  # 44 字段
    "tableType": "1", "isHidden": False,
    "searchType": "fuzzy", "searchField": "", "searchValue": "",
    "pageNo": 1, "pageSize": 20,
    "orderField": "", "orderValue": "", "shopInfoList": [],
    "brandIds": [], "state": "", "commodityCategories": "",
    "labelQuery": 0, "labelIdList": [], "dangerStock": False,
}
r = session.post(
    "https://www.sellfox.com/api/warehouseManage/warehouseItem-export.json",
    json=export_body,
    headers={"content-type": "application/json"}
)

# 轮询获取 task_id
today = datetime.now().strftime("%Y-%m-%d")
task_id = None
for _ in range(60):
    r = session.post(
        "https://www.sellfox.com/api/report/center/task/pageList.json",
        json={"status":"","dateType":"createTime","createTimeStart":today,
              "createTimeEnd":today,"pageSize":5,"pageNo":1,"tabs":1}
    )
    for t in r.json()["data"]["rows"]:
        if "仓库" in t["module"] and t["status"] == "COMPLETE":
            task_id = t["id"]; break
    if task_id: break
    time.sleep(2)

# 下载
r = session.post(
    "https://www.sellfox.com/api/report/center/task/download.json",
    json={"ids": [task_id]}
)
cos_url = r.json()["data"][0]
r = requests.get(cos_url)
with open("WarehouseItem.xlsx", "wb") as f:
    f.write(r.content)
```

---

## 8. 通用踩坑速查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Playwright click 超时 (element not visible) | el-select input 是 readonly 且被隐藏 | 用 `page.evaluate("el.closest('.el-select').click()")` |
| dropdown 打开后点不了其他元素 | el-popper 遮挡 | 先 `page.keyboard.press("Escape")` |
| 搜索框 placeholder 变了找不到 | 输入前="双击可批量搜索内容"，输入后="搜索内容" | 两个 selector 同时匹配 |
| 精/模切换无效 (点 icon 没用) | popover 拦截 | 必须点 `.search_type_btn` 外层容器 |
| 登录后停在 dashboard 不跳转 | Sellfox 默认跳 dashboard 而非仓库页 | `wait_for_login` 后手动 `page.goto(PAGE_URL)` |
| 隐藏0数据每次重置 | 赛狐不持久化此设置 | 每次导出前检查并切换 |
| export API 返回 data:null | 任务 ID 不在此返回 | 轮询 pageList.json 获取 |
