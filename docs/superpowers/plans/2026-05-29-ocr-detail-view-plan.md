# OCR 原始内容查看详情 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 抽屉详情从逐字段展示改为展示 OCR 原始识别文本，让用户直接看到原始识别内容而非提取后的片段。

**Architecture:** 后端 `PolicyResult` 新增 `raw_text` 字段携带 OCR 全文；前端 `showDetailModal()` 改为渲染 `pre.ocr-raw-text` 展示原始文本，顶部保留一行核心摘要。

**Tech Stack:** Python FastAPI, Pydantic, Vanilla JS, CSS

---

### Task 1: 后端模型 — PolicyResult 增加 `raw_text` 字段

**Files:**
- Modify: `app/models.py:22-29`

- [ ] **Step 1: 添加 `raw_text` 字段**

编辑 `app/models.py`，在 `PolicyResult` 的 `error_message` 字段之后新增 `raw_text`：

```python
    error_message: Optional[str] = Field(None, description="错误信息")
    raw_text: str = Field(default="", description="OCR 原始全文（所有文字块按阅读顺序拼接）")
```

默认值 `""` 确保向后兼容，已有构造 `PolicyResult(...)` 的调用无需改动。

- [ ] **Step 2: 验证模型可用**

Run: `python -c "from app.models import PolicyResult; r = PolicyResult(filename='test.pdf', is_policy=True); print(repr(r.raw_text))"`
Expected: 输出 `''`（空字符串默认值）

- [ ] **Step 3: 提交**

```bash
git add app/models.py
git commit -m "feat: PolicyResult 新增 raw_text 字段携带 OCR 原始文本"
```

---

### Task 2: 后端路由 — 传入 OCR 全文

**Files:**
- Modify: `app/router.py:36-71`

需要在所有非错误路径构造 `PolicyResult` 时传入 `raw_text`。

关键点：`ocr_results` 在 `is_policy_page()` 判断前已经可用，需要提前拼接保存。`\n` 拼接保持阅读顺序，每个文字块一行。

- [ ] **Step 1: 在路由中拼接 OCR 全文并传入**

修改 `app/router.py`，在 OCR 识别完成后、分类之前拼接 raw_text。

在 `L36-49` 区域，于 `is_policy_page()` 调用之前插入拼接逻辑：

```python
            # 拼接 OCR 原始全文（每个文字块一行）
            raw_lines = [r.text for r in ocr_results if r.text.strip()]
            raw_text = "\n".join(raw_lines)
```

然后在三处 `PolicyResult(...)` 构造中添加 `raw_text`：

**① OCR 失败（L43-48）** — 已经有个返回，不需要改，`raw_text` 走默认 `""`
**② 非保单（L53-57）** — 传入 `raw_text=raw_text`

```python
            if not is_policy:
                results.append(PolicyResult(
                    filename=file.filename or "unknown",
                    is_policy=False,
                    status="not_policy",
                    raw_text=raw_text,
                ))
                continue
```

**③ 保单字段提取成功（L65-70）** — 传入 `raw_text=raw_text`

```python
            policy_result = PolicyResult(
                filename=file.filename or "unknown",
                is_policy=True,
                fields=fields,
                status="ok",
                raw_text=raw_text,
            )
```

- [ ] **Step 2: 验证路由不报错**

Run: `python -c "from app.router import router; print('OK:', type(router).__name__)"`
Expected: 输出 `OK: <class 'fastapi.routing.APIRouter'>`（无 ImportError）

- [ ] **Step 3: 提交**

```bash
git add app/router.py
git commit -m "feat: OCR 原始全文传入 PolicyResult 的 raw_text 字段"
```

---

### Task 3: 前端 JS — 抽屉改为展示 OCR 原始文本

**Files:**
- Modify: `static/script.js:264-292`

- [ ] **Step 1: 重写 `showDetailModal()`**

将原来 11 行的字段列表渲染替换为顶部摘要 + pre 原始文本：

```javascript
/** 展示保单详情弹窗 */
function showDetailModal(result) {
  const fields = result.fields;
  const category = fields?.insurance_category
    ? getCategory(fields.insurance_category) : '—';
  const statusLabel = result.status || 'ok';

  modalTitle.textContent = `保单详情 — ${result.filename}`;
  modalBody.innerHTML = `
    <div class="detail-summary">
      文件名: ${escapeHtml(result.filename)} |
      险种: ${escapeHtml(category)} |
      状态: <span class="status-${statusLabel}">${statusLabel}</span>
    </div>
    <hr>
    <pre class="ocr-raw-text">${escapeHtml(result.raw_text || '无识别结果')}</pre>
  `;

  detailModal.classList.add('open');
}
```

- [ ] **Step 2: 验证 JS 语法**

Run: `node -e "eval(require('fs').readFileSync('static/script.js','utf8').replace('document.addEventListener',''))"`
Expected: 无语法错误（注意 `document` 在 node 中未定义，但语法检查通过即可）

- [ ] **Step 3: 提交**

```bash
git add static/script.js
git commit -m "feat: 抽屉详情改为展示 OCR 原始文本"
```

---

### Task 4: 前端 CSS — 新增 OCR 文本样式，移除旧字段样式

**Files:**
- Modify: `static/style.css:108-118`

- [ ] **Step 1: 替换样式规则**

将 `.drawer-body` 之后的 `.modal-field` 系列样式（L109-118）替换为新的 OCR 样式和摘要样式：

```css
.drawer-body { padding: 16px 20px; overflow-y: auto; flex: 1; }

/* 详情抽屉内容 */
.detail-summary {
  font-size: 13px;
  color: #636e72;
  padding: 8px 0;
  line-height: 1.6;
}
.detail-summary .status-ok { color: #00b894; }
.detail-summary .status-not_policy { color: #fdcb6e; }
.detail-summary .status-error { color: #d63031; }

.ocr-raw-text {
  background: #fafafa;
  border: 1px solid #dfe6e9;
  border-radius: 8px;
  padding: 16px;
  font-family: 'Courier New', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
  margin-top: 12px;
}
```

注意：L108 `.drawer-body` 保持不变，只替换 L109-L118 及其后的空行。

- [ ] **Step 2: 验证 HTML 不被破坏**

Run: `python -c "
from app import create_app
import warnings
warnings.filterwarnings('ignore')
app = create_app()
with app.test_client() as c:
    r = c.get('/')
    print(f'Status: {r.status_code}')
    print(f'HTML: {len(r.data)} bytes')
"` (如果 app 有 test_client 方式；没有也无妨)

或者简单检查文件完整性：
Run: `python -c "open('static/style.css').read()" > nul || echo OK`

- [ ] **Step 3: 提交**

```bash
git add static/style.css
git commit -m "feat: 新增 OCR 原始文本样式，移除旧的 modal-field 样式"
```

---

### Task 5: 端到端验证

- [ ] **Step 1: 启动开发服务器**

Run: `cd /d D:\data\aatomcode\jinrong-sdd && python run.py`

预期：服务启动成功，无报错。

- [ ] **Step 2: 浏览器打开首页**

访问 `http://localhost:8000`，页面上传一个 PDF/图片保单文件。
预期：
- 上传后识别结果显示正常
- 点击任意保单的「查看详情」按钮
- 抽屉打开，顶部显示「文件名 | 险种 | 状态」摘要行
- 主体区域以等宽字体展示 OCR 原始文本，包含原始换行
- 无 JavaScript 控制台错误

- [ ] **Step 3: 边界情况 — 空文本**

构造一个 `raw_text=""` 的测试（可直接反向验证）。
预期：抽屉显示「无识别结果」

- [ ] **Step 4: 检查旧功能不被影响**

- 所有主表格（保单信息表、投保人表、被保人表）展示正常
- 统计卡片数据正确
- 导出 Excel/JSON 功能正常
