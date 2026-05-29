# 金融保单敏感信息扫描工具 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个离线Web工具，用户上传PDF或图片保单，自动识别保单首页并提取被保人、险种、保费、销售经理等字段，按被保人去重统计敏感信息条数，支持导出Excel/JSON。

**Architecture:** FastAPI 提供 REST API，PaddleOCR 离线识别中文文字，规则引擎定位字段值。前端纯HTML/CSS/JS，无框架。结果存内存，刷新清空。

**Tech Stack:** Python 3.11+, FastAPI, PaddleOCR (paddlepaddle-cpu), PyMuPDF, openpyxl, 原生HTML/CSS/JS

---

## 文件结构

```
jinrong-sdd/
├── main.py                    # FastAPI 入口，uvicorn启动
├── requirements.txt           # 所有Python依赖
├── app/
│   ├── __init__.py            # 空包标记
│   ├── config.py              # 配置常量（关键词列表、保险公司列表等）
│   ├── upload.py              # 上传处理：校验、保存、清理
│   ├── pdf_processor.py       # PDF每页转JPEG图片
│   ├── ocr_engine.py          # PaddleOCR封装：加载模型、识别单图
│   ├── page_classifier.py     # 判断图片是否为保单首页
│   ├── field_extractor.py     # 从OCR结果提取各字段值
│   ├── statistics.py          # 按被保人去重统计敏感信息条数
│   ├── exporter.py            # 导出Excel（openpyxl）和JSON
│   ├── models.py              # Pydantic数据模型
│   └── router.py              # FastAPI路由挂载
├── static/
│   ├── index.html             # 主页面：上传区+表格+统计+导出
│   ├── style.css              # 样式
│   └── script.js              # 前端交互逻辑
├── uploads/                   # 上传文件临时存储（运行时自动创建）
└── tests/
    ├── __init__.py             # 空包标记
    ├── test_upload.py          # 上传校验测试
    ├── test_pdf_processor.py   # PDF转图片测试（需要mock）
    ├── test_ocr_engine.py      # OCR引擎测试（需要mock）
    ├── test_page_classifier.py # 首页判定测试
    ├── test_field_extractor.py # 字段提取测试
    ├── test_statistics.py      # 敏感信息统计测试
    └── test_exporter.py        # 导出测试
```

---

### Task 1: 项目初始化 + 配置层

**Files:**
- Create: `requirements.txt`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/models.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.17
paddlepaddle==2.6.1
paddleocr==2.8.1
PyMuPDF==1.24.0
openpyxl==3.1.5
pytest==8.3.0
aiofiles==24.1.0
```

- [ ] **Step 2: 创建 app/__init__.py 和 tests/__init__.py**

两个空文件，内容各一行 `# package`

- [ ] **Step 3: 创建 app/config.py**

```python
"""全局配置常量"""

# 保单首页关键词（出现N个以上即判定为首页）
POLICY_KEYWORDS = [
    "保险单", "保单号", "投保人", "被保险人", "被保人",
    "受益人", "保险费", "保费", "保险期间", "保险期限",
    "生效日期", "交费方式", "缴费方式",
]

# 保单首页判定阈值（关键词出现≥此数量即判定为首页）
POLICY_PAGE_THRESHOLD = 3

# 常见保险公司列表（用于提取保险公司字段）
INSURANCE_COMPANIES = [
    "中国人寿", "平安保险", "中国平安", "太平洋保险",
    "泰康保险", "新华保险", "人保寿险", "中国人民保险",
    "太平人寿", "友邦保险", "阳光保险", "华夏保险",
    "中意人寿", "中英人寿", "工银安盛", "招商信诺",
    "中信保诚", "光大永明", "长城人寿", "民生保险",
]

# OCR 置信度阈值（低于此值标记为"待确认"）
OCR_CONFIDENCE_THRESHOLD = 0.7

# 文件上传限制
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_MB = 50
UPLOAD_DIR = "uploads"
```

- [ ] **Step 4: 创建 app/models.py**

```python
"""Pydantic 数据模型"""
from pydantic import BaseModel, Field
from typing import Optional


class PolicyFields(BaseModel):
    """单个保单的提取字段"""
    insurance_company: Optional[str] = Field(None, description="保险公司")
    policy_type: Optional[str] = Field(None, description="险种")
    policy_number: Optional[str] = Field(None, description="保单号")
    applicant: Optional[str] = Field(None, description="投保人")
    insured: Optional[str] = Field(None, description="被保人")
    beneficiary: Optional[str] = Field(None, description="受益人")
    premium: Optional[str] = Field(None, description="保费")
    payment_method: Optional[str] = Field(None, description="交费方式")
    effective_date: Optional[str] = Field(None, description="生效日期")
    insurance_period: Optional[str] = Field(None, description="保险期间")
    sales_manager: Optional[str] = Field(None, description="销售经理")


class PolicyResult(BaseModel):
    """单个文件的识别结果"""
    filename: str = Field(description="原始文件名")
    is_policy: bool = Field(description="是否为保单首页")
    fields: PolicyFields = Field(default_factory=PolicyFields, description="提取字段")
    status: str = Field(default="ok", description="状态: ok / low_confidence / not_policy / error")
    error_message: Optional[str] = Field(None, description="错误信息")


class SensitiveStats(BaseModel):
    """敏感信息统计"""
    total_unique_insured: int = Field(description="去重后的被保人数量")
    insured_list: list[str] = Field(description="被保人姓名列表（去重后）")
    details: list[PolicyResult] = Field(description="所有识别结果明细")


class UploadResponse(BaseModel):
    """上传响应"""
    results: list[PolicyResult] = Field(description="识别结果列表")
    stats: SensitiveStats = Field(description="敏感信息统计")
```

- [ ] **Step 5: 提交**

```bash
git add requirements.txt app/__init__.py app/config.py app/models.py tests/__init__.py
git commit -m "feat: project init with config and models"
```

---

### Task 2: 上传处理模块

**Files:**
- Create: `app/upload.py`
- Create: `tests/test_upload.py`

- [ ] **Step 1: 创建 app/upload.py**

```python
"""上传文件处理：校验、保存、清理"""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR


def ensure_upload_dir():
    """确保上传目录存在"""
    Path(UPLOAD_DIR).mkdir(exist_ok=True)


def validate_file(filename: str, content_length: int) -> str:
    """校验文件扩展名和大小，返回小写扩展名"""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，支持 PDF/JPG/PNG")
    if content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"文件超过大小限制 {MAX_FILE_SIZE_MB}MB")
    return ext


async def save_upload(file: UploadFile) -> Path:
    """保存上传文件到临时目录，返回文件路径"""
    ensure_upload_dir()
    ext = validate_file(file.filename or "upload", file.size or 0)
    # 保留原始文件名，加UUID前缀防冲突
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    dest = Path(UPLOAD_DIR) / safe_name
    content = await file.read()
    dest.write_bytes(content)
    return dest


def cleanup_files():
    """清空上传目录"""
    import shutil
    if Path(UPLOAD_DIR).exists():
        shutil.rmtree(UPLOAD_DIR)
```

- [ ] **Step 2: 创建 tests/test_upload.py**

```python
"""测试上传模块"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from pathlib import Path
from app.upload import validate_file, save_upload, cleanup_files


class TestValidateFile:
    def test_valid_extensions(self):
        assert validate_file("test.pdf", 1000) == ".pdf"
        assert validate_file("test.jpg", 1000) == ".jpg"
        assert validate_file("test.jpeg", 1000) == ".jpeg"
        assert validate_file("test.png", 1000) == ".png"

    def test_invalid_extension(self):
        with pytest.raises(HTTPException) as exc:
            validate_file("test.exe", 1000)
        assert "不支持的文件格式" in str(exc.value.detail)

    def test_file_too_large(self):
        max_bytes = 50 * 1024 * 1024
        with pytest.raises(HTTPException) as exc:
            validate_file("test.pdf", max_bytes + 1)
        assert "超过大小限制" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_save_upload(self):
        mock_file = MagicMock()
        mock_file.filename = "保单.pdf"
        mock_file.size = 1000

        async def fake_read():
            return b"fake content"

        mock_file.read = fake_read

        path = await save_upload(mock_file)
        assert path.exists()
        assert "保单" in path.name
        path.unlink()
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/test_upload.py -v`
Expected: all PASS

- [ ] **Step 4: 提交**

```bash
git add app/upload.py tests/test_upload.py
git commit -m "feat: upload file handling module"
```

---

### Task 3: PDF 转图片模块

**Files:**
- Create: `app/pdf_processor.py`
- Create: `tests/test_pdf_processor.py`

- [ ] **Step 1: 创建 app/pdf_processor.py**

```python
"""PDF 转图片模块"""
from pathlib import Path
from typing import List
import fitz  # PyMuPDF


def pdf_to_images(pdf_path: Path, dpi: int = 200) -> List[Path]:
    """将PDF每页转为JPEG图片，返回图片路径列表"""
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # 设置缩放矩阵
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        # 保存为JPEG
        image_path = pdf_path.parent / f"{pdf_path.stem}_p{page_num + 1}.jpg"
        pix.save(str(image_path))
        images.append(image_path)
    doc.close()
    return images


def is_pdf_file(file_path: Path) -> bool:
    """判断是否为PDF文件"""
    return file_path.suffix.lower() == ".pdf"
```

- [ ] **Step 2: 创建 tests/test_pdf_processor.py**

```python
"""测试 PDF 转图片"""
import pytest
from pathlib import Path
from app.pdf_processor import is_pdf_file


def test_is_pdf_file():
    assert is_pdf_file(Path("test.pdf"))
    assert is_pdf_file(Path("test.PDF"))
    assert not is_pdf_file(Path("test.jpg"))
    assert not is_pdf_file(Path("test.png"))
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/test_pdf_processor.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add app/pdf_processor.py tests/test_pdf_processor.py
git commit -m "feat: pdf to image conversion"
```

---

### Task 4: OCR 引擎封装

**Files:**
- Create: `app/ocr_engine.py`
- Create: `tests/test_ocr_engine.py`

- [ ] **Step 1: 创建 app/ocr_engine.py**

```python
"""PaddleOCR 引擎封装，全局单例"""
from pathlib import Path
from typing import List, Optional
from paddleocr import PaddleOCR
from app.config import OCR_CONFIDENCE_THRESHOLD


class OcrResult:
    """单条OCR识别结果"""
    def __init__(self, text: str, confidence: float, bbox: list):
        self.text = text
        self.confidence = confidence
        self.bbox = bbox  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

    def is_confident(self) -> bool:
        return self.confidence >= OCR_CONFIDENCE_THRESHOLD

    def __repr__(self):
        return f"OcrResult(text={self.text!r}, conf={self.confidence:.2f})"


class OcrEngine:
    """全局OCR引擎（单例）"""

    _instance: Optional["OcrEngine"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ocr = None
        return cls._instance

    def load(self):
        """加载PaddleOCR模型（首次调用时）"""
        if self._ocr is None:
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="ch",
                use_gpu=False,
                show_log=False,
            )

    def recognize(self, image_path: Path) -> List[OcrResult]:
        """识别单张图片，返回文字块列表"""
        self.load()
        result = self._ocr.ocr(str(image_path), cls=True)
        if not result or not result[0]:
            return []
        return [
            OcrResult(text=item[1][0], confidence=item[1][1], bbox=item[0])
            for item in result[0]
        ]
```

- [ ] **Step 2: 创建 tests/test_ocr_engine.py**

```python
"""测试 OCR 引擎（mock模式，不加载真实模型）"""
import pytest
from pathlib import Path
from app.ocr_engine import OcrResult, OcrEngine


class TestOcrResult:
    def test_is_confident_above_threshold(self):
        result = OcrResult("测试", 0.85, [])
        assert result.is_confident() is True

    def test_is_confident_below_threshold(self):
        result = OcrResult("模糊文字", 0.5, [])
        assert result.is_confident() is False

    def test_is_confident_at_threshold(self):
        result = OcrResult("刚好", 0.7, [])
        assert result.is_confident() is True

    def test_repr(self):
        result = OcrResult("测试", 0.85, [])
        r = repr(result)
        assert "测试" in r
        assert "0.85" in r


class TestOcrEngine:
    def test_singleton(self):
        e1 = OcrEngine()
        e2 = OcrEngine()
        assert e1 is e2
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/test_ocr_engine.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add app/ocr_engine.py tests/test_ocr_engine.py
git commit -m "feat: OCR engine singleton wrapper"
```

---

### Task 5: 保单首页分类器

**Files:**
- Create: `app/page_classifier.py`
- Create: `tests/test_page_classifier.py`

- [ ] **Step 1: 创建 app/page_classifier.py**

```python
"""保单首页判定器：根据OCR结果中的关键词出现数量判断是否为保单首页"""
from typing import List
from app.ocr_engine import OcrResult
from app.config import POLICY_KEYWORDS, POLICY_PAGE_THRESHOLD


def is_policy_page(results: List[OcrResult]) -> bool:
    """
    判断OCR识别结果是否为保单首页。
    策略：保单相关关键词出现次数 ≥ 阈值则判定为首页。
    """
    text = "".join(r.text for r in results)
    hit_count = sum(1 for kw in POLICY_KEYWORDS if kw in text)
    return hit_count >= POLICY_PAGE_THRESHOLD
```

- [ ] **Step 2: 创建 tests/test_page_classifier.py**

```python
"""测试保单首页分类器"""
import pytest
from app.page_classifier import is_policy_page
from app.ocr_engine import OcrResult


def make_results(texts: list[str]) -> list:
    return [OcrResult(t, 0.9, []) for t in texts]


class TestIsPolicyPage:
    def test_policy_page_sufficient_keywords(self):
        """保单页：关键词足够多"""
        texts = ["保险单", "保单号", "投保人", "被保险人", "保费", "生效日期"]
        assert is_policy_page(make_results(texts)) is True

    def test_policy_page_exact_threshold(self):
        """刚好达到阈值（3个关键词）"""
        texts = ["保险单", "投保人", "保费"]
        assert is_policy_page(make_results(texts)) is True

    def test_not_policy_page_insufficient(self):
        """非保单页：关键词太少"""
        texts = ["保险", "重要提示"]
        assert is_policy_page(make_results(texts)) is False

    def test_not_policy_page_no_keywords(self):
        """非保单页：无关键词"""
        texts = ["第一章", "总则", "本合同"]
        assert is_policy_page(make_results(texts)) is False

    def test_empty_results(self):
        """空识别结果"""
        assert is_policy_page([]) is False
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/test_page_classifier.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add app/page_classifier.py tests/test_page_classifier.py
git commit -m "feat: policy page classifier"
```

---

### Task 6: 字段提取器

**Files:**
- Create: `app/field_extractor.py`
- Create: `tests/test_field_extractor.py`

- [ ] **Step 1: 创建 app/field_extractor.py**

```python
"""从OCR结果中提取保单各字段值"""
from typing import List
from app.ocr_engine import OcrResult
from app.models import PolicyFields
from app.config import INSURANCE_COMPANIES


def _find_value_by_keyword(results: List[OcrResult], keywords: List[str]) -> str:
    """在OCR结果列表中查找关键词，取紧挨着的下一个有效文字作为值"""
    texts = [r.text.strip() for r in results]
    for i, text in enumerate(texts):
        for kw in keywords:
            # 关键词完全匹配
            if text == kw or text.startswith(kw):
                # 取下一个非空文字
                for j in range(i + 1, len(texts)):
                    if texts[j] and texts[j] not in keywords:
                        return texts[j]
                # 如果关键词本身包含值（如"保费：10000元"），提取冒号后部分
                if "：" in text or ":" in text:
                    sep = "：" if "：" in text else ":"
                    after = text.split(sep, 1)[1].strip()
                    if after:
                        return after
    return ""


def _find_insurance_company(results: List[OcrResult]) -> str:
    """从OCR结果中识别保险公司名称"""
    texts = [r.text.strip() for r in results]
    for text in texts:
        for company in INSURANCE_COMPANIES:
            if company in text:
                return company
    return ""


def extract_fields(results: List[OcrResult]) -> PolicyFields:
    """
    从OCR识别结果中提取所有保单字段。
    使用关键词+位置相邻策略提取。
    """
    fields = PolicyFields()

    fields.insurance_company = _find_insurance_company(results)

    # 各字段的关键词列表
    keyword_map = [
        ("policy_type", ["险种", "险种名称", "产品名称", "产品"]),
        ("policy_number", ["保单号", "保单号码", "保险单号"]),
        ("applicant", ["投保人"]),
        ("insured", ["被保险人", "被保人"]),
        ("beneficiary", ["受益人"]),
        ("premium", ["保险费", "保费", "保险金额"]),
        ("payment_method", ["交费方式", "缴费方式"]),
        ("effective_date", ["生效日期", "生效日", "合同生效日"]),
        ("insurance_period", ["保险期间", "保险期限", "保障期间"]),
        ("sales_manager", ["销售经理", "业务员", "营销员", "代理人", "客户经理"]),
    ]

    for field_name, keywords in keyword_map:
        value = _find_value_by_keyword(results, keywords)
        if value:
            setattr(fields, field_name, value)

    return fields
```

- [ ] **Step 2: 创建 tests/test_field_extractor.py**

```python
"""测试字段提取器"""
import pytest
from app.field_extractor import extract_fields, _find_value_by_keyword, _find_insurance_company
from app.ocr_engine import OcrResult


def test_find_insurance_company_matched():
    results = [OcrResult("中国人寿保险股份有限公司", 0.95, [])]
    assert _find_insurance_company(results) == "中国人寿"


def test_find_insurance_company_not_matched():
    results = [OcrResult("某保险公司", 0.9, [])]
    assert _find_insurance_company(results) == ""


class TestExtractFields:
    def test_extract_all_fields(self):
        """完整保单页，提取所有字段"""
        results = [
            OcrResult("中国人寿", 0.95, []),
            OcrResult("保单号", 0.98, []),
            OcrResult("1234567890", 0.97, []),
            OcrResult("投保人", 0.99, []),
            OcrResult("张三", 0.96, []),
            OcrResult("被保险人", 0.99, []),
            OcrResult("李四", 0.97, []),
            OcrResult("受益人", 0.98, []),
            OcrResult("王五", 0.95, []),
            OcrResult("保费", 0.99, []),
            OcrResult("10000元", 0.96, []),
            OcrResult("交费方式", 0.98, []),
            OcrResult("年交", 0.97, []),
            OcrResult("生效日期", 0.99, []),
            OcrResult("2024-01-01", 0.98, []),
            OcrResult("保险期间", 0.98, []),
            OcrResult("终身", 0.97, []),
            OcrResult("销售经理", 0.97, []),
            OcrResult("赵六", 0.95, []),
        ]
        fields = extract_fields(results)
        assert fields.insurance_company == "中国人寿"
        assert fields.policy_number == "1234567890"
        assert fields.applicant == "张三"
        assert fields.insured == "李四"
        assert fields.beneficiary == "王五"
        assert fields.premium == "10000元"
        assert fields.payment_method == "年交"
        assert fields.effective_date == "2024-01-01"
        assert fields.insurance_period == "终身"
        assert fields.sales_manager == "赵六"

    def test_partial_fields(self):
        """部分字段缺失"""
        results = [
            OcrResult("中国人寿", 0.95, []),
            OcrResult("投保人", 0.99, []),
            OcrResult("张三", 0.96, []),
            OcrResult("保费", 0.99, []),
            OcrResult("5000元", 0.96, []),
        ]
        fields = extract_fields(results)
        assert fields.insurance_company == "中国人寿"
        assert fields.applicant == "张三"
        assert fields.premium == "5000元"
        assert fields.insured is None

    def test_keyword_inline_value(self):
        """关键词冒号后带值"""
        results = [
            OcrResult("保费：5000元", 0.95, []),
            OcrResult("被保险人:李四", 0.96, []),
        ]
        fields = extract_fields(results)
        assert fields.premium == "5000元"
        assert fields.insured == "李四"
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/test_field_extractor.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add app/field_extractor.py tests/test_field_extractor.py
git commit -m "feat: field extractor for policy fields"
```

---

### Task 7: 敏感信息统计 + 导出模块

**Files:**
- Create: `app/statistics.py`
- Create: `app/exporter.py`
- Create: `tests/test_statistics.py`
- Create: `tests/test_exporter.py`

- [ ] **Step 1: 创建 app/statistics.py**

```python
"""按照被保人姓名去重统计敏感信息条数"""
from typing import List
from app.models import PolicyResult, SensitiveStats


def compute_stats(results: List[PolicyResult]) -> SensitiveStats:
    """
    从所有识别结果中提取被保人姓名，去重后统计。
    只有状态为 'ok' 且被保人不为空的才算入统计。
    """
    insured_set: set[str] = set()
    for r in results:
        if r.status == "ok" and r.fields.insured:
            # 按顿号或逗号分割多个被保人
            names = [n.strip() for n in r.fields.insured.replace(",", "，").split("，") if n.strip()]
            insured_set.update(names)
    return SensitiveStats(
        total_unique_insured=len(insured_set),
        insured_list=sorted(insured_set),
        details=results,
    )
```

- [ ] **Step 2: 创建 tests/test_statistics.py**

```python
"""测试敏感信息统计"""
import pytest
from app.statistics import compute_stats
from app.models import PolicyResult, PolicyFields, SensitiveStats


def make_result(insured: str, status: str = "ok") -> PolicyResult:
    return PolicyResult(
        filename=f"{insured}.pdf",
        is_policy=True,
        fields=PolicyFields(insured=insured),
        status=status,
    )


class TestComputeStats:
    def test_single_insured(self):
        """一个人一个保单"""
        results = [make_result("李四")]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 1
        assert stats.insured_list == ["李四"]

    def test_multiple_insured_different(self):
        """多个不同被保人"""
        results = [make_result("李四"), make_result("张三"), make_result("王五")]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 3
        assert stats.insured_list == ["张三", "王五", "李四"]

    def test_duplicate_insured(self):
        """同一人多个保单，去重后算1条"""
        results = [
            make_result("李四"),
            make_result("李四"),
            make_result("张三"),
        ]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 2
        assert stats.insured_list == ["张三", "李四"]

    def test_skip_non_ok_status(self):
        """非ok状态不统计"""
        results = [
            make_result("李四", status="ok"),
            make_result("张三", status="not_policy"),
            PolicyResult(
                filename="error.pdf",
                is_policy=False,
                fields=PolicyFields(insured="王五"),
                status="error",
                error_message="识别失败",
            ),
        ]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 1
        assert stats.insured_list == ["李四"]

    def test_empty_results(self):
        """空列表"""
        stats = compute_stats([])
        assert stats.total_unique_insured == 0
        assert stats.insured_list == []

    def test_all_not_policy(self):
        """全都不是保单"""
        results = [
            PolicyResult(
                filename="a.pdf", is_policy=False, fields=PolicyFields(), status="not_policy"
            )
        ]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 0
```

- [ ] **Step 3: 创建 app/exporter.py**

```python
"""导出模块：支持 Excel 和 JSON 格式"""
import json
import io
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from app.models import PolicyResult, SensitiveStats


def export_to_excel(results: List[PolicyResult], stats: SensitiveStats) -> bytes:
    """生成Excel文件内容（内存），返回bytes"""
    wb = Workbook()

    # === Sheet 1: 明细 ===
    ws1 = wb.active
    ws1.title = "识别明细"
    headers = ["文件名", "状态", "保险公司", "险种", "保单号", "投保人",
               "被保人", "受益人", "保费", "交费方式", "生效日期",
               "保险期间", "销售经理", "错误信息"]
    # 表头样式
    header_font = Font(bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row_idx, r in enumerate(results, 2):
        ws1.cell(row=row_idx, column=1, value=r.filename)
        ws1.cell(row=row_idx, column=2, value=r.status)
        ws1.cell(row=row_idx, column=3, value=r.fields.insurance_company or "")
        ws1.cell(row=row_idx, column=4, value=r.fields.policy_type or "")
        ws1.cell(row=row_idx, column=5, value=r.fields.policy_number or "")
        ws1.cell(row=row_idx, column=6, value=r.fields.applicant or "")
        ws1.cell(row=row_idx, column=7, value=r.fields.insured or "")
        ws1.cell(row=row_idx, column=8, value=r.fields.beneficiary or "")
        ws1.cell(row=row_idx, column=9, value=r.fields.premium or "")
        ws1.cell(row=row_idx, column=10, value=r.fields.payment_method or "")
        ws1.cell(row=row_idx, column=11, value=r.fields.effective_date or "")
        ws1.cell(row=row_idx, column=12, value=r.fields.insurance_period or "")
        ws1.cell(row=row_idx, column=13, value=r.fields.sales_manager or "")
        ws1.cell(row=row_idx, column=14, value=r.error_message or "")

    # === Sheet 2: 统计 ===
    ws2 = wb.create_sheet("敏感信息统计")
    ws2.cell(row=1, column=1, value="去重后被保人数量").font = header_font
    ws2.cell(row=1, column=2, value=stats.total_unique_insured)
    ws2.cell(row=2, column=1, value="被保人列表").font = header_font
    ws2.cell(row=2, column=2, value="、".join(stats.insured_list))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def export_to_json(results: List[PolicyResult], stats: SensitiveStats) -> str:
    """生成JSON字符串（用于下载）"""
    data = {
        "sensitive_stats": {
            "total_unique_insured": stats.total_unique_insured,
            "insured_list": stats.insured_list,
        },
        "details": [
            {
                "filename": r.filename,
                "status": r.status,
                "fields": {
                    "insurance_company": r.fields.insurance_company,
                    "policy_type": r.fields.policy_type,
                    "policy_number": r.fields.policy_number,
                    "applicant": r.fields.applicant,
                    "insured": r.fields.insured,
                    "beneficiary": r.fields.beneficiary,
                    "premium": r.fields.premium,
                    "payment_method": r.fields.payment_method,
                    "effective_date": r.fields.effective_date,
                    "insurance_period": r.fields.insurance_period,
                    "sales_manager": r.fields.sales_manager,
                },
                "error_message": r.error_message,
            }
            for r in results
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 创建 tests/test_exporter.py**

```python
"""测试导出模块"""
import json
import pytest
from app.exporter import export_to_excel, export_to_json
from app.models import PolicyResult, PolicyFields, SensitiveStats


def make_result(insured: str, premium: str = "10000") -> PolicyResult:
    return PolicyResult(
        filename=f"{insured}.pdf",
        is_policy=True,
        fields=PolicyFields(insured=insured, premium=premium, insurance_company="中国人寿"),
        status="ok",
    )


class TestExportToJson:
    def test_export_structure(self):
        results = [make_result("李四"), make_result("张三")]
        stats = SensitiveStats(total_unique_insured=2, insured_list=["张三", "李四"], details=results)
        output = export_to_json(results, stats)
        data = json.loads(output)
        assert data["sensitive_stats"]["total_unique_insured"] == 2
        assert len(data["details"]) == 2
        assert data["details"][0]["fields"]["insured"] == "李四"

    def test_empty_export(self):
        output = export_to_json([], SensitiveStats(total_unique_insured=0, insured_list=[], details=[]))
        data = json.loads(output)
        assert data["sensitive_stats"]["total_unique_insured"] == 0


class TestExportToExcel:
    def test_export_creates_workbook(self):
        results = [make_result("李四", "10000元")]
        stats = SensitiveStats(total_unique_insured=1, insured_list=["李四"], details=results)
        data = export_to_excel(results, stats)
        assert isinstance(data, bytes)
        assert len(data) > 0  # Excel文件至少有一些字节
```

- [ ] **Step 5: 运行测试**

Run: `pytest tests/test_statistics.py tests/test_exporter.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add app/statistics.py app/exporter.py tests/test_statistics.py tests/test_exporter.py
git commit -m "feat: statistics and export modules"
```

---

### Task 8: API 路由 + 主处理流程

**Files:**
- Create: `app/router.py`
- Create: `main.py`
- Create: `tests/test_router.py`

- [ ] **Step 1: 创建 app/router.py**

```python
"""FastAPI 路由：上传 → 识别 → 响应"""
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File
from app.upload import save_upload, cleanup_files
from app.pdf_processor import pdf_to_images, is_pdf_file
from app.ocr_engine import OcrEngine
from app.page_classifier import is_policy_page
from app.field_extractor import extract_fields
from app.statistics import compute_stats
from app.exporter import export_to_excel, export_to_json
from app.models import PolicyResult, UploadResponse
from fastapi.responses import StreamingResponse, JSONResponse
import io

router = APIRouter()
ocr = OcrEngine()


@router.post("/api/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """上传一个或多个文件，识别后返回结果"""
    results: List[PolicyResult] = []

    for file in files:
        try:
            file_path = await save_upload(file)

            if is_pdf_file(file_path):
                images = pdf_to_images(file_path)
            else:
                images = [file_path]

            # 只取第一页作判断（保单首页）
            first_image = images[0] if images else file_path
            ocr_results = ocr.recognize(first_image)

            if not ocr_results:
                results.append(PolicyResult(
                    filename=file.filename or "unknown",
                    is_policy=False,
                    status="error",
                    error_message="OCR未识别到任何文字",
                ))
                continue

            is_policy = is_policy_page(ocr_results)
            if not is_policy:
                results.append(PolicyResult(
                    filename=file.filename or "unknown",
                    is_policy=False,
                    status="not_policy",
                ))
                continue

            fields = extract_fields(ocr_results)
            policy_result = PolicyResult(
                filename=file.filename or "unknown",
                is_policy=True,
                fields=fields,
                status="ok",
            )
            results.append(policy_result)

        except Exception as e:
            results.append(PolicyResult(
                filename=file.filename or "unknown",
                is_policy=False,
                status="error",
                error_message=str(e),
            ))

    stats = compute_stats(results)
    return UploadResponse(results=results, stats=stats)


@router.get("/api/export/excel")
async def export_excel():
    """导出Excel文件（使用session中最后的结果）"""
    # 注意：因为没有持久化，导出需要前端在upload后保留结果再请求
    # 这里由前端通过POST body传递结果列表来导出
    pass


@router.post("/api/export/excel")
async def export_excel_post(data: UploadResponse):
    """接收识别结果并导出为Excel"""
    excel_bytes = export_to_excel(data.results, data.stats)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=policy_export.xlsx"},
    )


@router.post("/api/export/json")
async def export_json_post(data: UploadResponse):
    """接收识别结果并导出为JSON"""
    json_str = export_to_json(data.results, data.stats)
    return StreamingResponse(
        io.BytesIO(json_str.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=policy_export.json"},
    )
```

- [ ] **Step 2: 创建 main.py**

```python
"""FastAPI 应用入口"""
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.router import router

app = FastAPI(title="保单敏感信息扫描工具")

# 静态文件（前端页面）
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
```

- [ ] **Step 3: 创建 tests/test_router.py**

```python
"""测试API路由"""
import pytest
from fastapi.testclient import TestClient
from main import app
from pathlib import Path
import tempfile

client = TestClient(app)


def test_upload_no_files():
    resp = client.post("/api/upload")
    assert resp.status_code == 422  # 缺少files参数


def test_health_check():
    resp = client.get("/docs")
    assert resp.status_code == 200
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/test_router.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/router.py main.py tests/test_router.py
git commit -m "feat: API router and main entry"
```

---

### Task 9: 前端页面

**Files:**
- Create: `static/index.html`
- Create: `static/style.css`
- Create: `static/script.js`

- [ ] **Step 1: 创建 static/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>保单敏感信息扫描工具</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
  <header>
    <h1>📄 保单敏感信息扫描工具</h1>
    <p class="subtitle">上传PDF或图片保单，自动识别提取关键字段并统计敏感信息</p>
  </header>

  <!-- 上传区域 -->
  <section class="upload-section">
    <div class="drop-zone" id="dropZone">
      <p class="drop-text">拖拽文件到此区域，或点击选择文件</p>
      <p class="drop-hint">支持 PDF、JPG、JPEG、PNG · 可一次选择多个文件</p>
      <input type="file" id="fileInput" multiple accept=".pdf,.jpg,.jpeg,.png" hidden>
      <button class="btn" id="selectBtn">选择文件</button>
    </div>
    <div id="fileList" class="file-list"></div>
    <button class="btn btn-primary" id="uploadBtn" disabled>开始识别</button>
  </section>

  <!-- 进度指示 -->
  <section id="progressSection" class="progress-section" hidden>
    <div class="progress-bar">
      <div class="progress-fill" id="progressFill"></div>
    </div>
    <p id="progressText" class="progress-text">正在识别...</p>
  </section>

  <!-- 统计概览 -->
  <section id="statsSection" class="stats-section" hidden>
    <div class="stats-card">
      <span class="stats-number" id="statsCount">0</span>
      <span class="stats-label">敏感信息条数（去重后被保人）</span>
    </div>
  </section>

  <!-- 结果表格 -->
  <section id="resultSection" class="result-section" hidden>
    <div class="result-toolbar">
      <h2>识别结果</h2>
      <div class="toolbar-buttons">
        <button class="btn" id="exportExcelBtn">导出 Excel</button>
        <button class="btn" id="exportJsonBtn">导出 JSON</button>
        <button class="btn" id="clearBtn">清空</button>
      </div>
    </div>
    <div class="table-wrapper">
      <table id="resultTable">
        <thead>
          <tr>
            <th>文件名</th>
            <th>状态</th>
            <th>保险公司</th>
            <th>险种</th>
            <th>保单号</th>
            <th>投保人</th>
            <th>被保人</th>
            <th>受益人</th>
            <th>保费</th>
            <th>交费方式</th>
            <th>生效日期</th>
            <th>保险期间</th>
            <th>销售经理</th>
          </tr>
        </thead>
        <tbody id="resultBody">
        </tbody>
      </table>
    </div>
  </section>
</div>

<script src="script.js"></script>
</body>
</html>
```

- [ ] **Step 2: 创建 static/style.css**

```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f5f6fa; color: #2d3436; padding: 20px;
}
.container { max-width: 1400px; margin: 0 auto; }

header { margin-bottom: 24px; }
header h1 { font-size: 24px; color: #0984e3; }
.subtitle { color: #636e72; font-size: 14px; margin-top: 4px; }

/* 上传区域 */
.upload-section { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
.drop-zone {
  border: 2px dashed #b2bec3; border-radius: 12px; padding: 40px 20px;
  text-align: center; cursor: pointer; transition: all 0.3s;
}
.drop-zone:hover, .drop-zone.dragover { border-color: #0984e3; background: #dfe6e9; }
.drop-text { font-size: 16px; color: #636e72; margin-bottom: 8px; }
.drop-hint { font-size: 12px; color: #b2bec3; margin-bottom: 16px; }
.file-list { margin-top: 12px; font-size: 13px; color: #636e72; }
.file-list .file-item { padding: 4px 0; }

.btn {
  display: inline-block; padding: 8px 20px; border-radius: 6px;
  border: 1px solid #b2bec3; background: white; cursor: pointer;
  font-size: 14px; color: #2d3436; transition: all 0.2s;
}
.btn:hover { background: #dfe6e9; }
.btn-primary { background: #0984e3; color: white; border-color: #0984e3; }
.btn-primary:hover { background: #0770c4; }
.btn-primary:disabled { background: #b2bec3; border-color: #b2bec3; cursor: not-allowed; }

/* 进度 */
.progress-section { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
.progress-bar { height: 8px; background: #dfe6e9; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: #0984e3; border-radius: 4px; transition: width 0.3s; }
.progress-text { font-size: 13px; color: #636e72; margin-top: 8px; text-align: center; }

/* 统计 */
.stats-section { margin-bottom: 20px; }
.stats-card {
  background: white; border-radius: 12px; padding: 24px; text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: inline-block; min-width: 280px;
}
.stats-number { font-size: 48px; font-weight: bold; color: #0984e3; display: block; }
.stats-label { font-size: 14px; color: #636e72; margin-top: 4px; }

/* 结果表格 */
.result-section { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
.result-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.result-toolbar h2 { font-size: 16px; }
.toolbar-buttons { display: flex; gap: 8px; }
.table-wrapper { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; white-space: nowrap; }
th { background: #dfe6e9; padding: 10px 8px; text-align: left; font-weight: 600; position: sticky; top: 0; }
td { padding: 8px; border-bottom: 1px solid #dfe6e9; }
td[contenteditable="true"] { background: #fff9e6; cursor: text; }
tr:hover td { background: #f8f9fa; }
.status-ok { color: #00b894; }
.status-not_policy { color: #fdcb6e; }
.status-error { color: #d63031; }
.status-low_confidence { color: #e17055; }
```

- [ ] **Step 3: 创建 static/script.js**

```javascript
// 全局存储当前识别结果
let currentResults = [];
let currentStats = null;

// DOM引用
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.getElementById('selectBtn');
const fileList = document.getElementById('fileList');
const uploadBtn = document.getElementById('uploadBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statsSection = document.getElementById('statsSection');
const statsCount = document.getElementById('statsCount');
const resultSection = document.getElementById('resultSection');
const resultBody = document.getElementById('resultBody');
const exportExcelBtn = document.getElementById('exportExcelBtn');
const exportJsonBtn = document.getElementById('exportJsonBtn');
const clearBtn = document.getElementById('clearBtn');

let selectedFiles = [];

// 点击选择文件
selectBtn.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('click', () => fileInput.click());

// 拖拽上传
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});

// 文件选择
fileInput.addEventListener('change', () => { handleFiles(fileInput.files); });

function handleFiles(files) {
  selectedFiles = Array.from(files);
  updateFileList();
  uploadBtn.disabled = selectedFiles.length === 0;
}

function updateFileList() {
  fileList.innerHTML = selectedFiles.map(f =>
    `<div class="file-item">📎 ${f.name} (${(f.size / 1024).toFixed(1)} KB)</div>`
  ).join('');
}

// 识别主流程
uploadBtn.addEventListener('click', async () => {
  if (selectedFiles.length === 0) return;

  progressSection.hidden = false;
  uploadBtn.disabled = true;
  resultSection.hidden = true;
  statsSection.hidden = true;

  const formData = new FormData();
  selectedFiles.forEach(f => formData.append('files', f));

  try {
    // 模拟进度（PaddleOCR无法提供真实进度）
    progressFill.style.width = '30%';
    progressText.textContent = '正在上传文件...';

    const resp = await fetch('/api/upload', { method: 'POST', body: formData });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || `服务器错误: ${resp.status}`);
    }

    progressFill.style.width = '80%';
    progressText.textContent = '识别完成，渲染结果...';

    const data = await resp.json();
    currentResults = data.results;
    currentStats = data.stats;

    // 渲染统计
    statsSection.hidden = false;
    statsCount.textContent = data.stats.total_unique_insured;

    // 渲染表格
    renderTable(data.results);
    resultSection.hidden = false;

    progressFill.style.width = '100%';
    progressText.textContent = `识别完成！共处理 ${data.results.length} 个文件`;
  } catch (err) {
    progressText.textContent = `❌ 错误：${err.message}`;
    progressText.style.color = '#d63031';
  } finally {
    uploadBtn.disabled = false;
    setTimeout(() => { progressSection.hidden = true; }, 3000);
  }
});

function renderTable(results) {
  const statusMap = {
    'ok': '✅ 正常',
    'not_policy': '⚠️ 非保单',
    'error': '❌ 错误',
    'low_confidence': '⚡ 低置信度'
  };

  resultBody.innerHTML = results.map(r => `
    <tr>
      <td>${escapeHtml(r.filename)}</td>
      <td class="status-${r.status}">${statusMap[r.status] || r.status}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.insurance_company || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.policy_type || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.policy_number || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.applicant || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.insured || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.beneficiary || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.premium || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.payment_method || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.effective_date || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.insurance_period || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.sales_manager || '')}</td>
    </tr>
  `).join('');

  // 监听编辑事件，同步回内存数据
  document.querySelectorAll('td[contenteditable="true"]').forEach((td, index) => {
    td.addEventListener('blur', () => {
      // 简单映射：找到对应行和列
      const row = td.closest('tr');
      const rowIdx = Array.from(resultBody.children).indexOf(row);
      const colIdx = Array.from(row.children).indexOf(td) - 1; // 减去文件名列
      const fieldNames = ['insurance_company', 'policy_type', 'policy_number', 'applicant',
        'insured', 'beneficiary', 'premium', 'payment_method', 'effective_date',
        'insurance_period', 'sales_manager'];
      if (rowIdx >= 0 && colIdx >= 0 && colIdx < fieldNames.length) {
        currentResults[rowIdx].fields[fieldNames[colIdx]] = td.textContent.trim() || null;
      }
    });
  });
}

// 导出Excel
exportExcelBtn.addEventListener('click', async () => {
  if (!currentResults.length) return;
  try {
    const resp = await fetch('/api/export/excel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results: currentResults, stats: currentStats }),
    });
    if (!resp.ok) throw new Error('导出失败');
    const blob = await resp.blob();
    downloadBlob(blob, '保单识别结果.xlsx');
  } catch (err) {
    alert('导出Excel失败：' + err.message);
  }
});

// 导出JSON
exportJsonBtn.addEventListener('click', async () => {
  if (!currentResults.length) return;
  try {
    const resp = await fetch('/api/export/json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results: currentResults, stats: currentStats }),
    });
    if (!resp.ok) throw new Error('导出失败');
    const blob = await resp.blob();
    downloadBlob(blob, '保单识别结果.json');
  } catch (err) {
    alert('导出JSON失败：' + err.message);
  }
});

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// 清空
clearBtn.addEventListener('click', () => {
  currentResults = [];
  currentStats = null;
  selectedFiles = [];
  fileInput.value = '';
  updateFileList();
  uploadBtn.disabled = true;
  resultSection.hidden = true;
  statsSection.hidden = true;
  progressSection.hidden = true;
  resultBody.innerHTML = '';
});

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
```

- [ ] **Step 4: 提交**

```bash
git add static/index.html static/style.css static/script.js
git commit -m "feat: frontend UI for upload, results and export"
```

---

### Task 10: 集成验证

**Files:** （无新增文件）

- [ ] **Step 1: 安装依赖并启动服务**

```bash
cd /path/to/project
pip install -r requirements.txt
python main.py
```

验证：浏览器访问 `http://127.0.0.1:8000` 看到上传页面

- [ ] **Step 2: 上传一张保单图片测试**

拿 `需求/参考.png` 或任意PDF保单上传，确认：
- 上传成功，显示进度
- 识别结果显示表格
- 敏感信息统计数字正确
- 可编辑修正字段
- 导出Excel/JSON成功

- [ ] **Step 3: 上传非保单页测试**

上传普通文档或合同页，确认显示"非保单"状态

- [ ] **Step 4: 提交最终版本**

```bash
git add -A
git commit -m "feat: complete policy scanner with frontend"
```

---

## 自检清单

1. **Spec coverage:** 所有设计文档中的模块都被覆盖（上传、PDF转图、OCR、分类、字段提取、统计、导出、前端）
2. **Placeholder check:** 所有步骤包含完整代码，无 TBD/TODO
3. **Type consistency:** `PolicyFields` / `PolicyResult` / `SensitiveStats` / `UploadResponse` 在前后端和导出中保持一致
4. **Test coverage:** 每个业务模块都有单元测试，共 8 个测试文件
