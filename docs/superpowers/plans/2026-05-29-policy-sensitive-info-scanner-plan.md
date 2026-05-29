# 金融保单敏感信息扫描工具 — 实施计划（增量）

> 基于已有代码库进行以下增量改造：
> 1. 新增险种分类器模块
> 2. 拆分投保人/被保人双表展示
> 3. 按险种类型区分统计规则

---

## 文件改动清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models.py` | 修改 | PolicyFields 新增 insurance_category；SensitiveStats 拆分为双统计结构 |
| `app/classifier.py` | 新增 | 险种分类器，关键字匹配规则 |
| `app/statistics.py` | 重写 | 按险种类型区分统计规则 |
| `app/router.py` | 修改 | 在 extract_fields 后调用 classifier，更新响应结构 |
| `app/exporter.py` | 修改 | Excel/JSON 导出适配新结构 |
| `app/config.py` | 修改 | 可选：新增险种分类相关常量 |
| `static/index.html` | 重写 | 双表格布局：投保人信息表 + 被保人信息表 |
| `static/style.css` | 修改 | 双表格样式 |
| `static/script.js` | 重写 | 双表格数据渲染、编辑、条件显示 |
| `tests/test_classifier.py` | 新增 | 险种分类器单元测试 |
| `tests/test_statistics.py` | 重写 | 适配新统计规则的测试 |
| `tests/test_exporter.py` | 修改 | 适配新导出格式 |

---

## Task 1: models.py — 数据模型变更

**改动内容：**

PolicyFields 新增字段：
- `insurance_category: Optional[str] = None` — 险种分类结果，取值: `life` / `health` / `accident` / `car` / `property` / `unknown`

SensitiveStats 重构为：
```python
class SensitiveStats(BaseModel):
    """敏感信息统计（按险种类型区分）"""
    # 人身险统计
    life_insured_count: int = 0          # 人身险被保人去重数
    life_insured_list: list[str] = []    # 人身险被保人姓名列表
    
    # 财产险统计
    property_count: int = 0              # 财产险保单数
    property_applicant_list: list[str] = []
    
    # 未知分类
    unknown_count: int = 0
    
    # 总览
    total_applicant_count: int = 0       # 所有保单去重投保人数
    total_insured_count: int = 0         # 仅人身险被保人去重数
```

测试文件 `tests/test_models.py`：
- 验证新增字段默认值
- 验证 SensitiveStats 新结构

---

## Task 2: classifier.py — 险种分类器（新增）

**路径：** `app/classifier.py`

**接口：**
```python
from app.models import PolicyFields
from typing import Optional

def classify_insurance(policy_type: Optional[str]) -> str:
    """
    根据险种名称识别保险大类。
    返回: life / health / accident / car / property / unknown
    """
```

**分类规则（按优先级从上到下匹配，先命中归谁）：**
1. 人寿险关键字：寿险、人寿、终身、定期寿、两全、年金、万能、投连、分红
2. 健康险关键字：健康、医疗、重疾、疾病、防癌、护理、医保
3. 意外险关键字：意外、意外伤害、人身意外、交通意外、旅游意外、驾意
4. 车险关键字：车险、机动车、交强、三者险、车损、商业车险
5. 财产险关键字：财产保险、企财、家财、责任保险、责任险、货运、工程保险、保证保险、信用保险、农业保险
6. 未命中任何 → unknown

**测试文件 `tests/test_classifier.py`：**
```python
# 各分类正向测试
def test_classify_life():
    assert classify_insurance("国寿鑫享至尊年金保险") == "life"

def test_classify_health():
    assert classify_insurance("百万医疗险") == "health"

def test_classify_accident():
    assert classify_insurance("驾意险") == "accident"

def test_classify_car():
    assert classify_insurance("交强险") == "car"

def test_classify_property():
    assert classify_insurance("企业财产保险") == "property"

def test_classify_unknown():
    assert classify_insurance("某自定义产品") == "unknown"

def test_classify_empty():
    assert classify_insurance(None) == "unknown"

def test_classify_priority():
    """人寿险优先于财产险"""
    assert classify_insurance("人寿险") == "life"

def test_jiayi_not_car():
    """驾意归意外险，不归车险"""
    assert classify_insurance("驾意险") == "accident"
```

---

## Task 3: statistics.py — 统计引擎重写

**路径：** `app/statistics.py`

**新逻辑：**
```python
def compute_stats(results: List[PolicyResult]) -> SensitiveStats:
    """
    按险种类型区分统计规则：
    - 人身险（life/health/accident）：按被保人去重统计
    - 财产险（car/property）：按保单数+投保人统计
    - unknown：计数但不纳统
    """
```

**详细规则：**
1. 只处理 `status == "ok"` 的结果
2. 人身险（`insurance_category` 为 life/health/accident）：
   - 提取被保人姓名（支持顿号/逗号多人拆分）
   - 去重后计入 `life_insured_count` 和 `life_insured_list`
3. 财产险（`insurance_category` 为 car/property）：
   - 每张保单计数 +1
   - 记录投保人姓名
   - 计入 `property_count` 和 `property_applicant_list`
4. 未知（`insurance_category` 为 unknown/None）：
   - `unknown_count` +1
5. 合并统计：
   - `total_insured_count` = life_insured_count
   - `total_applicant_count` = 所有保单去重投保人总数

**测试文件重写 `tests/test_statistics.py`：**
```python
def test_life_insurance_insured_count():
    """人身险：按被保人去重"""
    results = [
        make_result("张三", insurance_category="life"),
        make_result("李四", insurance_category="life"),
        make_result("张三", insurance_category="life"),  # 重复
    ]
    stats = compute_stats(results)
    assert stats.life_insured_count == 2

def test_property_insurance_count():
    """财产险：按保单数统计"""
    results = [
        make_result("张三", insurance_category="car"),
        make_result("张三", insurance_category="car"),  # 同人两单
    ]
    stats = compute_stats(results)
    assert stats.property_count == 2

def test_mixed_types():
    """混合类型统计"""
    results = [
        make_result("张三", insurance_category="life", insured="张三"),
        make_result("李四", insurance_category="life", insured="李四"),
        make_result("王五", insurance_category="car", applicant="王五"),
    ]
    stats = compute_stats(results)
    assert stats.life_insured_count == 2
    assert stats.property_count == 1

def test_unknown_not_counted():
    """未知类型不计入统计"""
    results = [
        make_result("张三", insurance_category="unknown"),
    ]
    stats = compute_stats(results)
    assert stats.unknown_count == 1
    assert stats.life_insured_count == 0
    assert stats.property_count == 0

def test_skip_non_ok():
    """非ok状态不统计"""
    ...
```

---

## Task 4: router.py — 整合险种分类器

**改动点（3处）：**

1. 新增 import：
```python
from app.classifier import classify_insurance
```

2. 在字段提取后、构造 PolicyResult 前，调用分类器：
```python
fields = extract_fields(ocr_results)
# 新增：险种分类
fields.insurance_category = classify_insurance(fields.policy_type)
```

3. 响应结构不变（UploadResponse 的 stats 类型变为新 SensitiveStats）

---

## Task 5: exporter.py — 导出适配

**Excel 改动：**

Sheet1 "识别明细"：
- 表头新增第4列"险种类型"（在"险种"和"保单号"之间）
- 列顺序调整为：文件名、状态、保险公司、险种、**险种类型**、保单号、投保人、被保人、受益人、保费、交费方式、生效日期、保险期间、销售经理、错误信息

Sheet2 "敏感信息统计" 重构：
```
行1: 人身险被保人数量（去重） = N
行2: 被保人列表 = 张三、李四
行3: 财产险保单数量 = N
行4: 财产险投保人 = 王五、赵六
行5: 未分类保单数 = N
行6: 投保人总数（去重） = N
```

**JSON 改动：**
```json
{
  "insurance_stats": {
    "life_insured_count": 2,
    "life_insured_list": ["张三", "李四"],
    "property_count": 1,
    "property_applicant_list": ["王五"],
    "unknown_count": 0,
    "total_applicant_count": 3,
    "total_insured_count": 2
  },
  "details": [
    {
      "filename": "...",
      "status": "ok",
      "insurance_category": "life",
      "fields": { ... }
    }
  ]
}
```

**测试更新 `tests/test_exporter.py`：**
- 验证新增的险种类型列
- 验证统计sheet新格式

---

## Task 6: index.html — 双表格前端布局

**页面结构调整为：**

```html
<!-- 统计概览 - 拆分为两个卡片 -->
<section id="statsSection" hidden>
  <div class="stats-row">
    <div class="stats-card">
      <span id="lifeStatsCount">0</span>
      <span>人身险被保人（去重）</span>
    </div>
    <div class="stats-card">
      <span id="propertyStatsCount">0</span>
      <span>财产险保单数</span>
    </div>
    <div class="stats-card">
      <span id="unknownStatsCount">0</span>
      <span>未分类保单</span>
    </div>
  </div>
</section>

<!-- 表格1: 投保人信息表（所有保单） -->
<section id="applicantSection" hidden>
  <h2>投保人信息</h2>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>文件名</th>
          <th>状态</th>
          <th>险种类型</th>
          <th>保险公司</th>
          <th>投保人</th>
          <th>保单号</th>
          <th>保费</th>
          <th>交费方式</th>
          <th>生效日期</th>
          <th>保险期间</th>
          <th>销售经理</th>
        </tr>
      </thead>
      <tbody id="applicantBody"></tbody>
    </table>
  </div>
</section>

<!-- 表格2: 被保人信息表（仅人身险） -->
<section id="insuredSection" hidden>
  <h2>被保人信息 <span class="section-hint">（仅人身险）</span></h2>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>投保人</th>
          <th>被保人</th>
          <th>受益人</th>
          <th>险种类型</th>
          <th>保险公司</th>
          <th>保单号</th>
        </tr>
      </thead>
      <tbody id="insuredBody"></tbody>
    </table>
  </div>
</section>
```

**区分逻辑：**
- **投保人信息表**：所有状态为 ok 的保单都展示，每文件一行
- **被保人信息表**：仅人身险（life/health/accident）展示，每被保人一行（多人拆分）
- 财产险行：被保人信息表不显示

---

## Task 7: style.css — 双表格样式

新增样式：
```css
/* 统计行 - 多卡片横排 */
.stats-row {
  display: flex; gap: 16px; flex-wrap: wrap;
}

/* 被保人表格提示 */
.section-hint {
  font-size: 12px; color: #636e72; font-weight: normal;
}
```

---

## Task 8: script.js — 双表格渲染

**核心变化：**

```javascript
// 渲染两个表格
function renderTables(results, stats) {
  renderStats(stats);
  renderApplicantTable(results);
  renderInsuredTable(results);
}

// 渲染投保人信息表（所有保单）
function renderApplicantTable(results) {
  // 只显示 status === 'ok' 的保单
  // 列：文件名、状态、险种类型、保险公司、投保人、保单号、保费、交费方式、生效日期、保险期间、销售经理
  // 单元格可编辑
}

// 渲染被保人信息表（仅人身险）
function renderInsuredTable(results) {
  // 只显示 insurance_category 为 life/health/accident 的保单
  // 被保人多人时拆成多行
  // 列：投保人、被保人、受益人、险种类型、保险公司、保单号
  // 不可编辑（作为摘要视图）
}
```

---

## Task 9: 测试 + 集成验证

**执行完整的测试套件：**
```bash
cd D:\data\aatomcode\jinrong-sdd
pytest -v
```

**手动验证功能路径：**
1. 上传一张人身险保单 → 验证两表格都出现，统计正确
2. 上传一张车险保单 → 验证投保人表有、被保人表无，统计正确
3. 上传混合类型 → 验证两表格各自展示，统计合计正确
4. 导出Excel → 验证险种类型列、统计sheet格式
5. 导出JSON → 验证新结构
6. 未知类型 → 验证标记为"待确认"

---

## 提交

```bash
git add -A
git commit -m "feat: add insurance classifier, split applicant/insured dual-table display

- New InsuranceClassifier module with keyword-based classification
- Statistics engine now handles life/property/unknown separately
- Frontend shows applicant table (all policies) + insured table (life only)
- Excel/JSON export adapted to new structure

Co-Authored-By: AtomCode (deepseek-v4-flash) <noreply@atomgit.com>
```
