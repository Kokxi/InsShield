# OCR 原始内容查看详情 — 设计规格书

## 1. 概述

当前页面的「查看详情」抽屉以逐字段（label-value 列表）展示 OCR 提取结果（投保人、被保人、保费等 11 个字段）。由于字段提取依赖正则匹配，不同版式保单容易出现字段错位（如"保费"字段包含了"保险期间"的内容）。

改造目标：**抽屉主体改为展示 OCR 原始识别文本**，用户直接看到识别到的原文，消除字段拼接错误。顶部保留一行核心信息用于快速定位。

## 2. 用户界面

### 2.1 抽屉结构（由上到下）

| 区域 | 内容 | 说明 |
|------|------|------|
| **标题** | `保单详情 — {文件名}` | 不变 |
| **顶部信息行** | 文件名 · 险种类型（标签）· 识别状态 | 一行文本，pipe 分隔 |
| **分隔线** | `—` | 视觉分割 |
| **主体区域** | OCR 原始全文 | `<pre>` 标签，`white-space: pre-wrap`，等宽字体 |

### 2.2 主体区域样式

- 使用 `<pre class="ocr-raw-text">` 渲染
- `white-space: pre-wrap` — 保留 OCR 原生换行，同时自动换行避免水平滚动
- `font-family: 'Courier New', monospace` — 等宽字体，方便对齐识别
- `background: #fafafa`，`padding: 16px`，圆角边框
- 最大高度 `400px`，`overflow-y: auto` 可滚动

### 2.3 删除的内容

- 当前 `showDetailModal()` 中的 11 个 `modal-field` 行（文件名、识别状态、险种类型、保险公司、保单号、投保人、被保人、受益人、保费、交费方式、生效日期、保险期间、销售经理）
- 对应的 CSS `.modal-field`、`.modal-field-label`、`.modal-field-value` 样式可以移除

### 2.4 不变的部分

- 主页面表格 ✓
- 统计面板 ✓
- 文件上传 ✓
- 导出 Excel/JSON ✓
- `buildPolicyDetails()` 用于表格行内显示 ✓
- `showPdfPreview` PDF 预览 ✓

## 3. 后端改动

### 3.1 models.py

`PolicyResult` 增加字段：

```python
raw_text: str = Field(default="", description="OCR 原始全文（所有文字块按阅读顺序拼接）")
```

### 3.2 router.py

在构造 `PolicyResult` 时传入：

```python
raw_text = "\n".join(r.text for r in ocr_results)
```

原有字段提取 (`extract_fields`) 照常进行，表格和统计继续使用提取结果。

### 3.3 响应示例

```json
{
  "filename": "保单1.png",
  "is_policy": true,
  "status": "ok",
  "raw_text": "投保人：张三\n被保人：张三\n险种名称：美好生活·重大疾病保险\n保险单号：P2024XXXXXXXX\n保险费：¥12,800.00\n保险期间：至80周岁\n生效日期：2024年3月15日",
  "fields": { ... }
}
```

## 4. 前端改动

### 4.1 script.js — showDetailModal()

```javascript
function showDetailModal(result) {
  const category = result.fields?.insurance_category
    ? getCategory(result.fields.insurance_category) : '—';
  modalTitle.textContent = `保单详情 — ${result.filename}`;
  modalBody.innerHTML = `
    <div class="detail-summary">
      文件名: ${escapeHtml(result.filename)} |
      险种: ${escapeHtml(category)} |
      状态: <span class="status-${result.status}">${result.status}</span>
    </div>
    <hr>
    <pre class="ocr-raw-text">${escapeHtml(result.raw_text || '无识别结果')}</pre>
  `;
  detailModal.classList.add('open');
}
```

### 4.2 style.css 新增样式

```css
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
}
.detail-summary {
  font-size: 13px;
  color: #636e72;
  padding: 8px 0;
}
```

### 4.3 可移除的 CSS

`.modal-field`、`.modal-field-label`、`.modal-field-value`

## 5. 非功能要求

- `raw_text` 为空（OCR 未识别到文字）时显示"无识别结果"
- 应对任意长度的 OCR 文本（预置 `max-height` 滚动）
- 后端兼容：`raw_text` 新增字段有默认值 `""`，不影响已有前端（旧版前端只是忽略未知字段）
- 无需新增测试
