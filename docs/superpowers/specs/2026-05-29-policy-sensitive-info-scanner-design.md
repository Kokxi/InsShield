# 保单敏感信息识别系统 — 设计规格书

## 1. 概述

一个 Web 应用，上传 PDF 保单文件，自动识别保单类型、保险公司名称，并提取投保人/被保人姓名等敏感信息。结果在页面上分层展示，支持导出 Excel / JSON。

## 2. 用户界面布局

页面从上到下分四个区域：

### 2.1 统计卡片行

四张卡片：

| 卡片 | 逻辑 |
|------|------|
| 人身险被保人数 | 险种为人寿/健康/意外险且状态 ok 的文件，被保人去重计数 |
| 财产险保单数 | 险种为车险/财产险且状态 ok 的文件计数 |
| 未知保单数 | 险种为 unknown 但 is_policy=true 的文件计数 |
| 总文件数 | 所有上传文件计数 |

### 2.2 表格①：保单信息表

展示"这份文件是什么"。只显示 `is_policy=true` 的文件。

| 列 | 来源 |
|----|------|
| 文件名 | PolicyResult.filename |
| 险种类型 | PolicyPolicyFields.insurance_category → `get_category_display_name()` |
| 保险公司 | PolicyPolicyFields.insurance_company |
| 是否有效 | `是`/`否`（是否 is_policy） |

### 2.3 表格②：投保人信息表

展示所有保单的投保人。支持行内编辑投保人字段。

| 列 | 来源 |
|----|------|
| 文件名 | PolicyResult.filename |
| 投保人 | PolicyFields.applicant（行内可编辑） |
| 保费 | PolicyFields.premium |
| 险种类型 | PolicyFields.insurance_category → display_name |

### 2.4 表格③：被保人信息表

展示人身险类（人寿/健康/意外）保单的被保人。支持行内编辑被保人字段。非人身险保单不在本表出现。

| 列 | 来源 |
|----|------|
| 文件名 | PolicyResult.filename |
| 被保人 | PolicyFields.insured（行内可编辑） |
| 保费 | PolicyFields.premium |
| 险种类型 | PolicyFields.insurance_category → display_name |

所有表格行内编辑后点击"保存按钮"触发后端保存。

## 3. 数据流程

每一步的结果决定下一步是否执行、如何执行：

```
[文件上传]
    ↓
[PDF OCR 提取文本]
    ↓
[页面分类器] → is_policy_page(text)
    ├── false → status="error"+reason="非保单", is_policy=false → 展示结果
    └── true  → status="ok", is_policy=true
                   ↓
              [字段提取器] → 投保人、被保人、保费、保险公司
                   ↓
              [险种分类器] → insurance_category = classify(text)
                                → life / health / accident / car / property / unknown
                   ↓
              [统计计算器] → SensitiveStats 双统计
                   ↓
              [前端渲染] → 四个区域的表格
```

### 3.1 非保单的处理

- `is_policy=false` 的文件不会出现在表格①（保单信息表）中
- 但会计入统计卡片"总文件数"
- 表格②③ 不受影响，仍然展示其提取到的字段（字段可能为空）

### 3.2 字段提取与分类的依赖

字段提取器原样输出 `insurance_company`（匹配到的原始文本）；`insurance_category` 由分类器单独填入，不依赖提取器的结果。提取到的投保人/被保人姓名作为统计输入。

## 4. 险种分类规则（`InsuranceClassifier`）

基于 OCR 文本中的关键字进行匹配，**不依赖字段提取器结果**。

优先级（高→低）：

| 优先级 | 类别 | 触发关键字 |
|--------|------|-----------|
| 1 | 人寿险 | `寿险`, `人寿`, `终身寿`, `定期寿` |
| 2 | 健康险 | `医疗`, `健康`, `重疾`, `大病`, `医保` |
| 3 | 意外险 | `意外`, `驾意` |
| 4 | 车险 | `车险`, `车损`, `三者`, `交强`, `机动车` |
| 5 | 财产险 | `财产`, `责任`, `家财`, `企财`, `责任险` |
| 6 | 未知 | 无匹配 |

结果调用 `get_category_display_name(cat)` 得到中文展示名。

## 5. 统计模型（`SensitiveStats`）

```python
class SensitiveStats(BaseModel):
    # 人身险（人寿/健康/意外）
    life_insured_count: int = 0           # 被保人去重数
    life_insured_list: list[str] = []     # 被保人姓名列表

    # 财产险（车险/财产险）
    property_count: int = 0               # 保单数
    property_applicant_list: list[str] = []  # 投保人列表（去重）

    # 未知
    unknown_count: int = 0

    # 所有投保人
    total_applicant_count: int = 0
    total_applicant_list: list[str] = []
```

统计时只处理 `status="ok"` 且 `is_policy=true` 的记录。被保人去重按姓名+文件名联合去重（同一姓名不同投保单视为不同人）。

## 6. API 接口

### POST /api/upload
上传 PDF 文件。返回结果列表（`list[PolicyResult]`）+ 统计信息（`SensitiveStats`）。

### POST /api/save
保存前端编辑后的结果（投保人/被保人修改）。

## 7. 导出格式

### Excel 输出

两个 Sheet：

1. **识别明细** — 所有文件每一行，包含：文件名、险种类型、保险公司、投保人、保费、被保人（自由文本）、状态
2. **敏感信息统计** — 统计汇总表

### JSON 输出

```json
{
  "insurance_stats": {
    "life_insured_count": 5,
    "life_insured_list": ["张三", "李四"],
    "property_count": 3,
    "property_applicant_list": ["王五"],
    "unknown_count": 1,
    "total_applicant_count": 9,
    "total_applicant_list": ["张三", "李四", "王五"]
  },
  "details": [
    {
      "filename": "保单.pdf",
      "is_policy": true,
      "status": "ok",
      "insurance_category": "life",
      "fields": { "insured": "张三", "applicant": "李四", ... }
    }
  ]
}
```

## 8. 模型定义

### PolicyFields
```python
insured: str = ""
applicant: str = ""
premium: str = ""
insurance_company: str = ""
insurance_category: str = ""   # 枚举值：life/health/accident/car/property/unknown
```

### PolicyResult
```python
filename: str
is_policy: bool = True
fields: PolicyFields
status: str = "ok"
```

## 9. 非功能要求

- 分类器不做外部 API 调用，纯本地关键字匹配
- OCR 结果低置信度（< 0.6）在页面上标黄提醒
- 所有测试应覆盖分类器的 5 个类别 + 未知 + 空文本 + 多类别优先级
- 历史 uploads 数据删除，不兼容迁移
