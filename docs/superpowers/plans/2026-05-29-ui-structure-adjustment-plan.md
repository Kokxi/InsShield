# 保单敏感信息识别系统 UI 结构调整 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有页面上新增"保单信息表"作为第一张表格（展示文件名、险种、保险公司、是否有效），新增"总文件数"统计卡片，删除历史 uploads 数据。

**Architecture:** 纯前端改动为主（HTML/CSS/JS），后端无需修改 API。前端新增一张只读表格，复用已有数据字段。后端只需清理历史文件。

**Tech Stack:** 纯前端 HTML/CSS/JS + Python FastAPI（仅清理操作）

**涉及文件（无新增文件）：**
- Modify: `static/index.html`
- Modify: `static/script.js`
- Modify: `static/style.css`
- Delete: `uploads/*` (历史数据)

---

### Task 1: 统计卡片增加"总文件数"

**文件:**
- Modify: `static/index.html`
- Modify: `static/script.js`
- Modify: `static/style.css`

- [ ] **Step 1: index.html — 添加第4张统计卡片**

在第 3 张卡片（未分类保单）后面添加总文件数卡片：

```html
      <div class="stats-card stats-card-total">
        <span class="stats-number" id="totalStatsCount">0</span>
        <span class="stats-label">总文件数</span>
      </div>
```

插入位置：`unknownStatsCount` 卡片 div 的 `</div>` 之后，`</div>`（stats-row 关闭）之前。

- [ ] **Step 2: style.css — 添加总文件数卡片颜色样式**

```css
.stats-card-total .stats-number { color: #636e72; }
```

插入位置：在 `.stats-card-unknown .stats-number` 规则之后。

- [ ] **Step 3: script.js — 添加 totalStatsCount DOM 引用**

在 `const unknownStatsCount = document.getElementById('unknownStatsCount');` 之后添加：

```javascript
const totalStatsCount = document.getElementById('totalStatsCount');
```

- [ ] **Step 4: script.js — 更新 renderStats 函数填充总文件数**

在 `renderStats` 函数末尾添加：

```javascript
  totalStatsCount.textContent = stats.total_file_count || results.length;
```

但 stats 对象还没有 `total_file_count` 字段。实际上所有文件数可以通过 `results.length` 获取，但 renderStats 只接收 `stats` 参数。需要把 `results` 也传进去，或者在调用处算。

更好的方式：修改 `uploadBtn` 的调用处，把 `data.results.length` 传给 renderStats。

修改 `renderStats` 函数签名，增加 `totalCount` 参数：

```javascript
function renderStats(stats, totalCount) {
  statsSection.hidden = false;
  lifeStatsCount.textContent = stats.life_insured_count;
  propertyStatsCount.textContent = stats.property_count;
  unknownStatsCount.textContent = stats.unknown_count;
  totalStatsCount.textContent = totalCount;
}
```

修改 `uploadBtn` 调用处：

```javascript
    renderStats(data.stats, data.results.length);
```

- [ ] **Step 5: 验证**

运行：`python -m pytest tests/test_statistics.py -v`
预期：全部通过

- [ ] **Step 6: 提交**

```bash
git add static/index.html static/script.js static/style.css
git commit -m "feat: add total file count stats card"
```

---

### Task 2: 保单信息表格（表格①）HTML 结构

**文件:**
- Modify: `static/index.html`

- [ ] **Step 1: index.html — 在统计区域之后、投保人表之前添加保单信息表**

在 `</section>`（statsSection 关闭）之后、`<h3 class="table-title">📋 投保人信息` 之前插入：

```html
    <!-- 表格1：保单信息表 -->
    <h3 class="table-title">📋 保单信息 <span class="section-hint">（所有保单）</span></h3>
    <div class="table-wrapper">
      <table id="policyInfoTable">
        <thead>
          <tr>
            <th>文件名</th>
            <th>险种类型</th>
            <th>保险公司</th>
            <th>是否有效</th>
          </tr>
        </thead>
        <tbody id="policyInfoBody"></tbody>
      </table>
    </div>
```

注意调整后面表格的注释：原"表格1：投保人信息表"改为"表格2：投保人信息表"，原"表格2：被保人信息表"改为"表格3：被保人信息表"。

- [ ] **Step 2: 验证**

运行：`python -m pytest`（加载页面不报错即可，本步骤不影响测试逻辑）
预期：全部通过

- [ ] **Step 3: 提交**

```bash
git add static/index.html
git commit -m "feat: add policy info table HTML structure"
```

---

### Task 3: 保单信息表渲染函数

**文件:**
- Modify: `static/script.js`

- [ ] **Step 1: script.js — 添加 policyInfoBody DOM 引用**

```javascript
const policyInfoBody = document.getElementById('policyInfoBody');
```

插入位置：在 `const insuredBody = document.getElementById('insuredBody');` 之后。

- [ ] **Step 2: script.js — 添加 renderPolicyInfoTable 函数**

```javascript
// 渲染保单信息表（所有 is_policy=true 的文件，每文件一行）
function renderPolicyInfoTable(results) {
  policyInfoBody.innerHTML = results
    .filter(r => r.is_policy)
    .map(r => `
      <tr>
        <td>${escapeHtml(r.filename)}</td>
        <td>${getCategory(r.fields.insurance_category)}</td>
        <td>${escapeHtml(r.fields.insurance_company || '')}</td>
        <td class="status-ok">✅ 有效</td>
      </tr>
    `).join('');
}
```

插入位置：在 `renderStats` 函数之后。

- [ ] **Step 3: script.js — uploadBtn 流程中调用新函数**

在 `renderApplicantTable(data.results);` 之前添加：

```javascript
    renderPolicyInfoTable(data.results);
```

- [ ] **Step 4: script.js — clearBtn 中清理新表格**

在 `insuredBody.innerHTML = '';` 之后添加：

```javascript
  policyInfoBody.innerHTML = '';
```

- [ ] **Step 5: 验证**

运行：`python -m pytest -v`
预期：全部通过

- [ ] **Step 6: 提交**

```bash
git add static/script.js
git commit -m "feat: add policy info table render function"
```

---

### Task 4: 清理历史 uploads 数据

**文件:**
- Delete: `uploads/` 目录下所有文件（保留目录本身）

- [ ] **Step 1: 清空 uploads 目录**

```bash
cd D:\data\aatomcode\jinrong-sdd
# 删除 uploads 下所有文件（保留目录）
if exist uploads\* (del /q uploads\* 2>nul) else (echo uploads already empty)
```

- [ ] **Step 2: 验证上传功能正常运行**

启动服务（如需要）并测试上传一个测试 PDF 文件。但更简单：运行测试确保上传相关测试通过。

```bash
python -m pytest tests/test_upload.py -v
```

预期：全部通过

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "chore: clear historical upload data"
```

---

### Task 5: 最终验证

- [ ] **Step 1: 运行全部测试**

```bash
cd D:\data\aatomcode\jinrong-sdd
python -m pytest -v
```

预期：全部 77 个测试通过，零失败。

- [ ] **Step 2: 手动验证页面结构（可选）**

启动应用并打开浏览器确认四区域正常展示：
1. 统计卡片行（人身险 N人 / 财产险 N单 / 未知 N / 总 N）
2. 保单信息表（文件名、险种类型、保险公司、是否有效）
3. 投保人信息表（行内可编辑）
4. 被保人信息表（行内可编辑，仅人身险）

- [ ] **Step 3: 提交最终批次**

```bash
git add -A && git status
```

确认无遗留未提交文件。
