# Skill: 浏览器自动化通用模式

> **给 Claude 看的**：用 Playwright MCP 操控任意网站的通用方法和踩坑经验。
> **前提**：用户已完成 `SKILL_quick_start.md` 的环境安装（uv + Node.js + Playwright MCP）。

---

## 核心 MCP 工具速查

| 工具 | 用途 | 示例 |
|------|------|------|
| `browser_tabs` | 列出/创建/切换标签页 | `action: "list"` |
| `browser_navigate` | 打开 URL | `url: "https://example.com"` |
| `browser_snapshot` | 获取页面元素树（比截图更好） | 直接调用 |
| `browser_click` | 点击元素 | `element: "登录按钮", target: "button.login"` |
| `browser_take_screenshot` | 截全页或元素 | `fullPage: true` |
| `browser_run_code` | 执行任意 JS | 适合复杂操作、调试 |
| `browser_wait_for` | 等待时间或文本 | `time: 5` |
| `browser_evaluate` | 执行 JS 并返回结果 | DOM 查询 |

**黄金法则**：优先用 `browser_snapshot` 看页面结构，不要一直截图。Snapshot 返回的是无障碍树（文本+角色），比 OCR 截图准确得多。

---

## 模式 1：登录处理

### 场景 A：网站有"记住我"功能（推荐）

当用户首次使用时：
1. `browser_navigate` 到目标页面
2. 检测是否被重定向到登录页
3. 如果是登录页，截图给用户，让用户**手动登录**（输入账号密码验证码）
4. 用户登录后，用 `browser_run_code` 提取 cookies：
   ```js
   async (page) => {
     const cookies = await page.context().cookies();
     return JSON.stringify(cookies);
   }
   ```
5. 把 cookies 保存到项目目录的 `mcp_cookies.json`
6. 后续使用时：先注入 cookies (`addCookies`)，再导航到目标页

### 场景 B：每次都需要登录

1. 导航到登录页
2. 用 `browser_snapshot` 找表单元素（textbox ref）
3. 用 `browser_type` 填入账号密码（让用户提供）
4. 如有验证码，截图给用户识别
5. 点击登录按钮

### 登录检测技巧

每个网站登录后会有特征元素（用户名显示、特定导航栏等）。找到一个**仅在登录后出现**的元素，用它判断登录状态：

```js
const loggedIn = await page.evaluate(() => {
  return !!document.querySelector('#user-menu');
});
```

---

## 模式 2：找对的选择器

### 优先级（从高到低）

1. **CSS 属性选择器**：`a[onclick="doExport()"]` — 最稳定（不会随文字改变）
2. **ID 限定范围 + 文字**：`#sidebar a:has-text("导出")` — 限定在特定区域内
3. **ref 引用**：snapshot 中每个元素有 `[ref=e123]`，可直接用 ref 点击
4. **纯文字**：`text=导出Excel` — 最不可靠（可能匹配到多处）

### 避免的坑

- **`text=` 可能歧义**：页面多个地方可能有相同文字（表格数据、导航栏、按钮）。始终用容器 ID 限定范围。
- **13 个同名按钮**：通途页面上有 FBA、FBF、Shein、Temu 等 13 个 `text=导出Excel`，必须用 `a[onclick="exportExcelPage()"]` 精确定位。
- **togglebutton 不是 select**：很多现代 UI（ExtJS、React）用自定义组件替代原生 `<select>`，需要 dump DOM 分析。

### 诊断方法：dump DOM

当不知道选择器时，用这个 JS 探路：

```js
// 找到所有包含关键词的可见元素
document.querySelectorAll('*').forEach(el => {
  if (el.innerText && el.innerText.includes('仓库') && el.offsetParent) {
    console.log(el.tagName, el.className, el.id, el.outerHTML.slice(0,200));
  }
});
```

通过 `browser_run_code` 执行，分析输出找到真正的选择器。

---

## 模式 3：处理下载

### MCP 模式

MCP 浏览器下载文件到 `.playwright-mcp/` 目录（在项目仓库根目录）。

触发下载后，文件自动保存。文件名通常是网站的默认导出名 + 时间戳。

**下载后处理**：
1. 用 `find` 或 `ls` 命令找到下载的文件
2. 按业务逻辑重命名（如加上仓库名）
3. 如需数据转换，调用 Python 脚本

### Python 脚本模式（uv 环境）

如果需要复杂的数据处理（如 Excel 转换），写一个 Python 脚本，用 uv 管理依赖：

```python
# pyproject.toml 中声明依赖
# [project]
# dependencies = ["pandas", "openpyxl"]
```

用户运行：
```bash
uv run python transform.py input.xlsx output.xlsx
```

---

## 模式 4：批量操作多个项目

通途案例：依次导出 6 个仓库的库存。

**流程**：
```
for each 仓库 in [仓库列表]:
  1. 点击仓库切换按钮
  2. 等待 5 秒（数据刷新）
  3. 点击导出按钮
  4. 等待下载完成
  5. 记录文件名
```

**关键细节**：
- 切换后等待时间要充足（测试值 5 秒，网络差时可能需要 8-10 秒）
- 每个操作后验证状态（检查切换是否生效）
- 下载文件名和仓库名建立映射关系

---

## 踩坑记录（来自实战）

### 坑 1：Cookie 加密
- **现象**：从 Chrome profile 的 SQLite 直接读 cookie 是加密的（Windows DPAPI）
- **解决**：用 Playwright Python 的 `launch_persistent_context` + `context.cookies()` 获取解密值

### 坑 2：Session Cookie 丢失
- **现象**：注入 cookies 后 JSESSIONID 等 session cookie 不存在
- **原因**：session cookie 没有 expires，浏览器关闭即清除
- **解决**：依赖"记住我"的长期 cookie（username + password hash）触发网站自动登录

### 坑 3：MCP 热加载限制
- **现象**：在当前对话中激活 MCP 后无法使用 MCP 工具
- **解决**：必须**新建对话**。MCP 只在 session 启动时加载

### 坑 4：中文路径编码
- **现象**：Windows 下 Python subprocess 遇到中文路径报 UnicodeDecodeError
- **解决**：`subprocess.run(..., encoding="utf-8", errors="replace")`

### 坑 5：下载路径不一致
- **Python 脚本模式**：`page.expect_download()` 直接控制保存位置
- **MCP 模式**：文件自动保存到 `.playwright-mcp/`，需要用桥接脚本整理

### 坑 6：仓库切换等待时间
- 3 秒有时不够（页面异步加载数据），建议 5 秒
- 可以轮询检测特定元素出现（更可靠但更复杂）

---

## 给 Claude 的行动指南

当用户说"帮我自动化 XX 网站"时：

1. **先了解需求**：问清楚具体想自动化什么操作
2. **打开网站**：`browser_navigate` 到目标 URL
3. **观察状态**：是否已登录？是否有目标元素？
4. **分析 DOM**：用 `browser_snapshot` 了解页面结构
5. **写 Python 脚本**：如果需要数据处理，用 uv + Python
6. **记录经验**：把这次发现的选择器、踩坑更新到项目文档
