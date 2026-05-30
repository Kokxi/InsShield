# 金融文档涉敏信息扫描工具 — 需求规格书

## 1. 概述

面向安全合规人员的 Web 应用。上传金融文档（PDF/图片/Word），自动提取文件中的个人敏感信息（姓名、身份证号、手机号、银行卡号等），以"人"为单位组织和呈现结果。不限文件类型，从所有文件中检出涉密信息。

**核心目标**：检出哪些人出现在哪些文件中，涉及哪些类型的敏感信息。

---

## 2. 处理流程

```
[文件上传]
    ↓
[文本提取] ─ PDF → OCR | 图片 → OCR | Word → python-docx 解析
    ↓
[文档分类] → doc_type（保单/理赔/批单/投保单/未知）
    ↓                                       ↓
[PII 提取引擎]                      [辅助信息提取]
    ├─ 身份证号匹配                    ├─ 保险公司
    ├─ 角色关键词+姓名                  ├─ 险种
    ├─ 手机号/银行卡/地址               ├─ 保单号
    ├─ 人员组装与去重                   └─ 保费
    └─ 敏感类型归类
    ↓
[人员合并] → 每个文件的 Persons 列表
    ↓
[销售经理提取] → 仅提取姓名，不参与人员计数，单独列出
    ↓
[险种分类器] → insurance_category（life/health/accident/car/property/unknown）
    ↓
[险种大类判定] → insurance_branch（life/property/social/unknown）
    ↓
[异常检测] → 财产险多人 → anomaly 标记
    ↓
[全局统计]
    ├─ total_files / sensitive_files / non_sensitive_files
    ├─ life_sensitive_files / life_unique_persons
    ├─ property_files / property_sensitive_persons
    └─ anomaly_files
    ↓
[前端渲染 / 导出]
```

> **人员 vs 销售经理**：投保人/被保人通过角色关键词+身份证号/手机号等定位，构成完整的 Person 实体并参与去重计数；销售经理仅通过姓名关键词提取，既不入 Persons 列表也不参与人员统计。二者在后续统计、导出和前端卡片中严格区分。

---

## 3. 核心原则

1. **PII 提取不依赖文档类型** — 文档类型分类仅用于辅助信息提取精度，不影响人员检出
2. **有就提取，没有就留空，不猜测** — 辅助信息（保险公司、险种、保单号、保费等）提不到不影响核心目标
3. **以人为计数单位** — 最终交付口径是一个人涉及多少条信息，而不是一个文件有多少条信息
4. **非涉敏文件也展示** — 安全人员需要知道哪些文件已确认安全，消除信息黑洞
5. **销售经理与人员分离** — 销售经理仅提取姓名，不构成 Person 实体、不参与去重、不纳入任何人员计数，仅在辅助信息中单独列出

---

## 4. OCR 引擎

### 4.1 引擎选择

| 项目 | 选择 |
|------|------|
| 引擎 | rapidocr_onnxruntime（替代 PaddleOCR） |
| 模型 | ch_PP-OCRv4_mobile（默认随 pip 安装） |
| 接口 | `OcrResult(text, confidence, bbox)` / `OcrEngine` 单例 |
| 性能 | 单页平均 8-9 秒（200dpi PDF 转图） |

### 4.2 回退方案

如 rapidocr_onnxruntime 出现质量问题：
1. `requirements.txt` 保留注释掉的 paddleocr 依赖
2. `app/ocr_engine.py` 保留旧版初始化代码分支，通过环境变量 `OCR_ENGINE=rapidocr|paddleocr` 切换

---

## 5. 文档分类

### 5.1 保险相关判断

文件全文（含文件名）中出现以下关键词 ≥ 2 个即视为保险相关文档：

```
保险, 保单, 投保, 被保, 理赔, 保费, 险种,
保险公司, 保险合同, 保险责任, 保险期间, 保额
```

### 5.2 文档类型（优先级匹配，先命中先归谁）

| 类型 | 触发关键词 |
|------|-----------|
| 批单 endorsement | 批单, 批改, 批注, 变更申请 |
| 理赔书 claim | 理赔, 给付通知, 赔款, 理赔决定 |
| 投保单 application | 投保单, 投保申请, 投保书 |
| 保险证 certificate | 保险证, 保险凭证, 电子凭证 |
| 续保通知 renewal | 续保, 续期, 续保通知 |
| 保单 policy | 保险单, 电子保单, 保险合同 |
| 其他保险文档 other | 仅命中保险关键词但未匹配上述类型 |
| 未知 unknown | 未命中保险关键词 |

### 5.3 险种分类（关键字匹配，不依赖字段提取器结果）

| 优先级 | 类别 | 触发关键字 |
|--------|------|-----------|
| 1 | 人寿险 | 寿险, 人寿, 终身寿, 定期寿 |
| 2 | 健康险 | 医疗, 健康, 重疾, 大病, 医保 |
| 3 | 意外险 | 意外, 驾意 |
| 4 | 车险 | 车险, 车损, 三者, 交强, 机动车 |
| 5 | 财产险 | 财产, 责任, 家财, 企财, 责任险 |
| 6 | 未知 | 无匹配 |

依据《中华人民共和国保险法》第 95 条及分业经营原则，细分类通过以下层级关系聚合为险种大类（insurance_branch）：

```
中国保险
├── 人身保险 (life branch)
│   ├── 人寿保险 (life)
│   ├── 健康保险 (health)
│   └── 意外伤害保险 (accident)
│
├── 财产保险 (property branch)
│   ├── 财产损失保险 (property)
│   ├── 车险 (car)
│   └── 责任保险 (property)
│
└── 社会保险 (social) — 非本项目主要范围
```

细分类到分支的映射（在 `classifier.py` 中定义）：

```
life/health/accident → life（人身保险）
car/property → property（财产保险）
social → social（社会保险）
unknown → unknown（未知）
```

---

## 6. PII 提取引擎

### 6.1 三层提取策略

| 层级 | 方法 | 产出 |
|------|------|------|
| 第一层 | 身份证号正则匹配 `\d{17}[\dXx]` | 定位具体的人，关联附近行姓名 |
| 第二层 | 角色关键词 + 相邻姓名 | 确定人的角色 |
| 第三层 | 通用姓名扫描 + PII 就近归属 | 捕捉无明确角色但有敏感信息关联的人 |

### 6.2 PII 类型

| 类型 | 检测方式 |
|------|----------|
| 身份证号 | `\d{17}[\dXx]` 正则 |
| 手机号 | `1[3-9]\d{9}` 正则 |
| 银行卡号 | `\d{16,19}` 正则 |
| 邮箱 | 标准邮箱格式正则 |
| 地址 | 关键词"联系地址/住址/地址/住所"+ 后续文本 |
| 健康信息 | 关键词"既往病史/健康状况/疾病/住院/手术/体检" |
| 出生日期 | 关键词"出生日期/出生年月/生日"+ 后续文本 |

### 6.3 人员去重规则

- **同一身份证号 → 严格为同一个人**
- **同名同角色 → 疑似同一人，标注提示**
- **同名不同角色 → 视为不同人**
- **无身份证号仅姓名 → 全局统计级按姓名聚合**

### 6.4 角色定义

| 角色 key | 显示名 |
|----------|--------|
| applicant | 投保人 |
| insured | 被保人 |
| beneficiary | 受益人 |
| reporter | 报案人 |
| accident_person | 出险人 |
| legal_heir | 法定继承人 |
| applicant_person | 申请人 |
| handler | 经办人 |
| anonymous | 匿名 |

---

## 7. 异常检测

### 7.1 检测规则

| 条件 | 异常标记 | 说明 |
|------|----------|------|
| property 分支中 `sensitive_count > 1` | `财产险多人` | 财产险保的是财产，人员不应超过投保人本人 |
| 其他情况 | 无 | 人身险不限人数（含团体险大量被保人） |

### 7.2 异常标记的影响

- 表格行标记 `.row-anomaly`（粉色背景）
- 单元格显示 `.anomaly-badge` 标记
- 统计卡片显示异常文件数
- 导出 Excel 中增加异常标记列

---

## 8. 数据模型

### 8.1 Person

```python
class PIIItem:
    type: str        # id_number/phone/bank_account/address/health/email/birth_date
    value: str       # PII 值
    raw_label: str   # 原文标签（如"联系电话"）
    line_number: int # 文本中行号

class Person:
    name: str              # 姓名
    role: str              # applicant/insured/beneficiary/reporter/.../anonymous
    role_display: str      # 角色中文名
    details: list[PIIItem] # 关联的 PII 列表
```

### 8.2 FileResult

```python
class FileResult:
    filename: str
    is_insurance_related: bool
    document_type: str             # endorsement/claim/application/.../unknown
    document_type_display: str
    insurance_category: str        # life/health/accident/car/property/social/unknown
    insurance_category_display: str
    insurance_branch: str          # life/property/social/unknown       ← 险种大类
    insurance_branch_display: str  # 人身保险/财产保险/社会保险/未知
    insurance_company: str
    policy_number: str
    persons: list[Person]
    sensitive_count: int           # 本文件涉敏人数
    status: str                    # ok/not_insurance/no_pii/error
    error_message: str | None
    anomaly: str                   # 异常标记，空串表示无异常           ← 新增
    raw_text: str                  # OCR 原始全文
```

### 8.3 GlobalStats

```python
class GlobalStats:
    total_files: int               # 总文件数
    sensitive_files: int           # 涉敏文件数
    non_sensitive_files: int       # 非涉敏文件数
    global_unique_persons: int     # 全局去重涉敏人数（按姓名）

    # 人身险统计（life branch）
    life_sensitive_files: int      # 人身险涉敏文件数
    life_unique_persons: int       # 人身险涉敏人数（文件内去重后全局）

    # 财产险统计（property branch）
    property_files: int            # 财产险文件数
    property_sensitive_persons: int # 财产险涉敏人数

    # 异常统计
    anomaly_files: int             # 标记为异常的文件数
```

---

## 9. API 接口

### 9.1 POST /api/upload

上传一个或多个文件。返回 `UploadResponse`。

请求：`multipart/form-data`，`files` 字段
响应：

```json
{
  "results": [
    {
      "filename": "xxx.pdf",
      "is_insurance_related": true,
      "document_type": "policy",
      "document_type_display": "保单",
      "insurance_category": "life",
      "insurance_category_display": "人寿险",
      "insurance_branch": "life",
      "insurance_branch_display": "人身保险",
      "insurance_company": "中国人寿",
      "policy_number": "P2024XXXXXXXX",
      "anomaly": "",
      "sensitive_count": 2,
      "status": "ok",
      "error_message": null,
      "raw_text": "投保人：张三\n被保人：张三\n险种名称：美好生活·重大疾病保险\n...",
      "persons": [
        {
          "name": "张三",
          "role": "applicant",
          "role_display": "投保人",
          "details": [
            { "type": "id_number", "value": "110101199001011234", ... }
          ]
        }
      ]
    }
  ],
  "stats": {
    "total_files": 10,
    "sensitive_files": 5,
    "non_sensitive_files": 3,
    "global_unique_persons": 8,
    "life_sensitive_files": 4,
    "life_unique_persons": 7,
    "property_files": 3,
    "property_sensitive_persons": 1,
    "anomaly_files": 1
  }
}
```

### 9.2 POST /api/export/excel

接收 `UploadResponse` 结构，导出 Excel，包含两个 Sheet：
- **涉敏人员明细**：文件名 | 险种类别 | 险种大类 | 异常标记 | 姓名 | 身份证号 | 手机号 | 角色 | 银行卡号 | 地址 | 保险公司
- **统计汇总**：总文件数 / 涉敏文件数 / 无敏文件数 / 涉敏总人数 / 人身险涉敏文件 / 人身险涉敏人数 / 财产险文件 / 财产险涉敏人数 / 异常文件数

### 9.3 POST /api/export/json

接收 `UploadResponse` 结构，导出 JSON，结构与 `/api/upload` 响应一致。

---

## 10. 前端展示

页面从上到下：

### 10.1 统计卡片行（7 张卡片）

| 卡片 | 数据来源 | 颜色 |
|------|----------|------|
| 总文件数 | `stats.total_files` | 蓝色 |
| 涉敏文件数 | `stats.sensitive_files` | 橙色 |
| 涉敏总人数 | `stats.global_unique_persons` | 蓝色 |
| 人身险涉敏 | `life_sensitive_files / life_unique_persons` | 绿色 |
| 财产险 | `property_files / property_sensitive_persons` | 紫色 |
| 异常文件数 | `stats.anomaly_files` | 红色 |

### 10.2 文件清单表（所有文件）

| 列 | 来源 |
|----|------|
| 文件名 | `FileResult.filename` |
| 文档类型 | `FileResult.document_type_display` |
| 险种类别 | `FileResult.insurance_category_display` |
| 险种大类 | `FileResult.insurance_branch_display` |
| 异常标记 | `FileResult.anomaly`（有值则显示 badge） |
| 涉敏人数 | `FileResult.sensitive_count` |
| 涉敏人员 | persons 列表摘要 |
| 详情 | 查看详情按钮 |

### 10.3 详情抽屉

| 区域 | 内容 |
|------|------|
| 标题 | 保单详情 — {文件名} |
| 摘要行 | 文件名 · 险种 · 险种大类 · 状态 · 异常（若有） |
| 人员卡片 | 每个 Person 一张卡片，展示姓名、角色、关联 PII |
| OCR 原文 | `<pre class="ocr-raw-text">` 展示 OCR 原始全文 |

### 10.4 统计卡片配色

```css
.stats-card-primary .stats-number  → #0984e3 (蓝色, 总文件)
.stats-card-sensitive              → #e17055 (橙色, 涉敏文件)
.stats-card-life                   → #00b894 (绿色, 人身险)
.stats-card-property               → #6c5ce7 (紫色, 财产险)
.stats-card-anomaly                → #d63031 (红色, 异常)
```

---

## 11. 导出格式

### 11.1 Excel 导出

**Sheet 1: 涉敏人员明细**

| 列 | 说明 |
|----|------|
| 文件名 | FileResult.filename |
| 险种类别 | insurance_category_display |
| 险种大类 | insurance_branch_display |
| 异常标记 | anomaly 或空 |
| 姓名 | Person.name |
| 身份证号 | PIIItem.type=id_number |
| 手机号 | PIIItem.type=phone |
| 角色 | Person.role_display |
| 银行卡号 | PIIItem.type=bank_account |
| 地址 | PIIItem.type=address |
| 保险公司 | insurance_company |
| 销售经理 | 辅助提取 |
| 保单号 | policy_number |

**Sheet 2: 统计汇总**

| 指标 | 值 |
|------|-----|
| 总文件数 | N |
| 涉敏文件数 | N |
| 无敏文件数 | N |
| 涉敏总人数 | N |
| 人身险涉敏文件 | N |
| 人身险涉敏人数 | N |
| 财产险文件数 | N |
| 财产险涉敏人数 | N |
| 异常文件数 | N |

### 11.2 JSON 导出

与 `/api/upload` 响应结构一致。

---

## 12. 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI (Python 3.10+) |
| OCR 引擎 | rapidocr_onnxruntime (ch_PP-OCRv4_mobile) |
| PDF 解析 | PyMuPDF |
| Word 解析 | python-docx |
| 前端 | 原生 HTML + CSS + Vanilla JS |
| 导出 | openpyxl (Excel) |
| 测试 | pytest |
| 部署 | uvicorn |
| 信创适配 | 麒麟/统信等国产系统兼容 |

---

## 13. 文件结构

```
app/
├── __init__.py
├── main.py             # FastAPI 应用入口
├── router.py           # API 路由（上传/导出/保存）
├── models.py           # Pydantic 数据模型
├── config.py           # 配置常量
├── ocr_engine.py       # OCR 引擎封装（rapidocr_onnxruntime 单例）
├── pdf_processor.py    # PDF → 图片 转换
├── word_processor.py   # Word 文档解析
├── classifier.py       # 文档分类 + 险种分类 + 险种大类 + 异常检测
├── pii_extractor.py    # PII 提取引擎（身份证/手机/姓名/角色）
├── field_extractor.py  # 保单字段提取（向后兼容）
├── exporter.py         # Excel/JSON 导出
└── statistics.py       # 全局统计计算

static/
├── index.html          # 主页面
├── script.js           # 前端逻辑
└── style.css           # 样式

tests/
├── test_exporter.py
├── test_router.py
├── test_statistics.py
├── test_ocr_engine.py
├── test_doc_classifier.py
└── test_pii_extractor.py

```

## 14. 非功能要求

- 所有处理本地执行，不调用外部 API
- OCR 低置信度（< 0.6）结果标黄提醒
- 支持批量上传多个文件同时处理
- 分类器纯本地关键字匹配，不做外部 API 调用
- `raw_text` 为空时显示"无识别结果"
- 应对任意长度的 OCR 文本（`max-height` 滚动）
- 兼容信创环境（麒麟/统信等国产系统）
- 测试覆盖分类器的 5 个类别 + 未知 + 空文本 + 多类别优先级
- 测试覆盖异常检测规则
