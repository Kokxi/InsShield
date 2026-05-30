# 运行时日志加强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为整个保单扫描系统添加结构化运行时日志，覆盖启动、上传、各处理阶段、导出、错误等全流程。

**Architecture:** 使用 Python 标准库 `logging` 模块，创建统一的日志配置模块 `app/logger.py`，各模块通过 `logging.getLogger(__name__)` 获取 logger。日志输出到 stderr + 可选文件，格式包含时间戳、日志级别、模块名。

**Tech Stack:** Python `logging` 标准库, FastAPI 事件钩子

---

### Task 1: 创建统一日志配置模块

**Files:**
- Create: `app/logger.py`

- [ ] **Step 1: 创建 `app/logger.py`**

```python
"""日志配置：统一的 logging 设置，供全项目使用"""
import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "jinrong-sdd",
    level: int = logging.INFO,
    log_file: str | None = None,
) -> logging.Logger:
    """配置并返回全局 Logger

    Args:
        name: logger 名称
        level: 日志级别，默认 INFO
        log_file: 可选日志文件路径，默认只输出到 stderr
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 Handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # stderr handler
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 可选文件 handler
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


# 全局默认 logger，模块通过 getLogger(__name__) 使用
default_logger = setup_logger()
```

- [ ] **Step 2: 验证文件创建**

Run: `python -c "from app.logger import default_logger; default_logger.info('test'); print('OK')"`
Expected: 输出 `[时间戳] INFO app.logger test` 并打印 OK

- [ ] **Step 3: Commit**

```bash
git add app/logger.py
git commit -m "feat: add unified logger module with console + file output"
```

---

### Task 2: 为 `main.py` 添加启动日志

**Files:**
- Modify: `main.py`

- [ ] **Step 1: 修改 `main.py` 添加启动日志**

```python
"""FastAPI 应用入口"""
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.router import router
from app.logger import default_logger

logger = default_logger

app = FastAPI(title="保单敏感信息扫描工具")

static_dir = Path(__file__).parent / "static"
index_html = static_dir / "index.html"

# API 路由优先
app.include_router(router)

# 静态文件（CSS/JS），不包含 index.html
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def serve_index():
    """返回前端主页面"""
    if index_html.exists():
        return FileResponse(str(index_html))
    return {"message": "Frontend not built yet"}


@app.on_event("startup")
async def on_startup():
    logger.info("服务启动 — http://127.0.0.1:8000")


if __name__ == "__main__":
    logger.info("正在启动 uvicorn server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
```

- [ ] **Step 2: 验证无语法错误**

Run: `python -c "import ast; ast.parse(open('main.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add startup logging in main.py"
```

---

### Task 3: 为上传模块添加日志

**Files:**
- Modify: `app/upload.py`

- [ ] **Step 1: 修改 `app/upload.py` 添加日志**

第 1 行后插入 import，`save_upload` 函数中添加日志：

```python
"""上传文件处理：校验、保存、清理"""
import os
import uuid
import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR

logger = logging.getLogger(__name__)


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
    basename = Path(file.filename or "upload").name
    safe_name = f"{uuid.uuid4().hex}_{basename}"
    dest = Path(UPLOAD_DIR) / safe_name
    content = await file.read()
    dest.write_bytes(content)
    logger.info("收到文件: %s (%s, %.1f KB)", basename, ext, len(content) / 1024)
    return dest


def cleanup_files():
    """清空上传目录"""
    import shutil
    if Path(UPLOAD_DIR).exists():
        shutil.rmtree(UPLOAD_DIR)
        logger.info("上传临时目录已清理")
```

- [ ] **Step 2: 验证语法**

Run: `python -c "import ast; ast.parse(open('app/upload.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/upload.py
git commit -m "feat: add logging for file upload and cleanup"
```

---

### Task 4: 为 PDF 处理器和 Word 处理器添加日志

**Files:**
- Modify: `app/pdf_processor.py`
- Modify: `app/word_processor.py`

- [ ] **Step 1: 修改 `app/pdf_processor.py`**

```python
"""PDF 转图片模块"""
import logging
from pathlib import Path
from typing import List
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def pdf_to_images(pdf_path: Path, dpi: int = 200, max_pages: int = 2) -> List[Path]:
    """将PDF每页转为JPEG图片，返回图片路径列表。max_pages 限制最多转换页数"""
    doc = fitz.open(pdf_path)
    images = []
    page_count = min(len(doc), max_pages)
    logger.info("PDF 转图片: %s (%d页, 取前%d页)", pdf_path.name, len(doc), page_count)
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        image_path = pdf_path.parent / f"{pdf_path.stem}_p{page_num + 1}.jpg"
        pix.save(str(image_path))
        images.append(image_path)
        logger.debug("  -> 第%d页已保存: %s", page_num + 1, image_path.name)
    doc.close()
    return images


def is_pdf_file(file_path: Path) -> bool:
    """判断是否为PDF文件"""
    return file_path.suffix.lower() == ".pdf"


def extract_text_from_pdf(file_path: Path, max_pages: int = 2) -> str:
    """尝试从文本型 PDF 直接提取文字层（不走 OCR），扫描型 PDF 返回空字符串"""
    doc = fitz.open(file_path)
    texts = []
    page_count = min(len(doc), max_pages)
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            texts.append(text)
    doc.close()
    total_chars = sum(len(t) for t in texts)
    logger.info("PDF 文本提取: %s (%d页, 提取%d字符)", file_path.name, page_count, total_chars)
    return '\n'.join(texts)
```

- [ ] **Step 2: 修改 `app/word_processor.py`**

```python
"""Word 文档文本提取"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def is_word_file(path: Path) -> bool:
    """判断是否为 Word 文档"""
    return path.suffix.lower() in [".docx", ".doc"]


def extract_text_from_docx(path: Path) -> str:
    """使用 python-docx 提取 Word 文档文本（段落 + 表格）"""
    from docx import Document

    doc = Document(str(path))
    texts = []

    for para in doc.paragraphs:
        if para.text.strip():
            texts.append(para.text)

    for table in doc.tables:
        for row in table.rows:
            row_text = " ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                texts.append(row_text)

    result = '\n'.join(texts)
    logger.info("Word 文档提取: %s (%d字符)", path.name, len(result))
    return result


def extract_text_from_doc(path: Path) -> str:
    """提取 .doc 格式文本（需要转换为 .docx 或使用其他库）"""
    msg = f"[.doc 格式暂不支持，请将文件转换为 .docx 格式: {path.name}]"
    logger.warning("%s", msg)
    return msg
```

- [ ] **Step 3: 验证语法**

Run: `cd D:\data\aatomcode\jinrong-sdd && python -c "import ast; ast.parse(open('app/pdf_processor.py').read()); ast.parse(open('app/word_processor.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/pdf_processor.py app/word_processor.py
git commit -m "feat: add logging for pdf_processor and word_processor"
```

---

### Task 5: 为 OCR 引擎添加日志

**Files:**
- Modify: `app/ocr_engine.py`

- [ ] **Step 1: 修改 `app/ocr_engine.py`**

```python
"""OCR 引擎封装（rapidocr_onnxruntime），全局单例"""
import logging
import threading
from pathlib import Path
from typing import List, Optional

from app.config import OCR_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)


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
    """全局OCR引擎（单例，线程安全），基于 rapidocr_onnxruntime"""

    _instance: Optional["OcrEngine"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._ocr = None
        return cls._instance

    def load(self):
        """加载 RapidOCR 模型（首次调用时初始化，线程安全）"""
        if self._ocr is None:
            with self._lock:
                if self._ocr is None:
                    from rapidocr_onnxruntime import RapidOCR
                    self._ocr = RapidOCR(print_verbose=False)
                    logger.info("OCR 引擎已加载 (rapidocr_onnxruntime)")

    def recognize(self, image_path: Path) -> List[OcrResult]:
        """识别单张图片，返回文字块列表"""
        self.load()
        logger.info("OCR 识别: %s", image_path.name)
        result, _ = self._ocr(str(image_path))

        items: List[OcrResult] = []
        if result is None:
            logger.info("  -> 未识别到文字")
            return items

        for box, text, conf_str in result:
            items.append(OcrResult(
                text=text,
                confidence=float(conf_str),
                bbox=box,
            ))

        logger.info("  -> 识别到 %d 个文字块", len(items))
        return items
```

- [ ] **Step 2: 验证语法**

Run: `python -c "import ast; ast.parse(open('app/ocr_engine.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/ocr_engine.py
git commit -m "feat: add logging for OCR engine"
```

---

### Task 6: 为分类器模块添加日志

**Files:**
- Modify: `app/doc_classifier.py`
- Modify: `app/classifier.py`

- [ ] **Step 1: 修改 `app/doc_classifier.py`**

在文件开头添加 `import logging` 和 `logger = logging.getLogger(__name__)`，在 `classify_doc_type` 函数中添加日志：

```diff
+import logging
 from typing import Tuple
 
+logger = logging.getLogger(__name__)
+
```

在 `classify_doc_type` 函数 return 前添加：

```python
    logger.info("文档分类: %s -> type=%s, is_insurance=%s", filename, doc_type, is_insurance)
    if is_insurance:
        logger.info("  -> 文档类型: %s", get_doc_type_display(doc_type))
```

完整的修改后的 `classify_doc_type`：

```python
def classify_doc_type(text: str, filename: str = "") -> Tuple[str, bool]:
    """识别文档类型，返回 (doc_type, is_insurance_related)"""
    is_insurance = _is_insurance_related(text, filename)

    for doc_type, keywords in DOC_TYPE_RULES:
        if any(kw in filename for kw in keywords):
            logger.info("文档分类: %s -> type=%s (文件名命中)", filename, doc_type)
            return doc_type, True

    title = text[:500]
    for doc_type, keywords in DOC_TYPE_RULES:
        if any(kw in title for kw in keywords):
            logger.info("文档分类: %s -> type=%s (文本命中)", filename, doc_type)
            return doc_type, True

    if is_insurance:
        logger.info("文档分类: %s -> type=other, is_insurance=True", filename)
        return "other", True

    logger.info("文档分类: %s -> type=unknown, is_insurance=False", filename)
    return "unknown", False
```

- [ ] **Step 2: 修改 `app/classifier.py`**

添加 `import logging` + `logger = logging.getLogger(__name__)`，在 `classify_from_full_text` 和 `check_anomaly` 中添加日志：

```python
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)
```

`classify_from_full_text` 函数中 return 前添加：

```python
    result = "unknown"
    for category, keywords in FALLBACK_CLASSIFIER_RULES:
        for kw in keywords:
            if kw in full_text:
                result = category
                break
        if result != "unknown":
            break

    logger.info("险种全文识别: %s -> %s", result, get_category_display_name(result))
    return result
```

- [ ] **Step 3: 验证语法**

Run: `python -c "import ast; ast.parse(open('app/doc_classifier.py').read()); ast.parse(open('app/classifier.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/doc_classifier.py app/classifier.py
git commit -m "feat: add logging for doc_classifier and classifier"
```

---

### Task 7: 为 PII 提取器添加日志

**Files:**
- Modify: `app/pii_extractor.py`

- [ ] **Step 1: 修改 `app/pii_extractor.py`**

文件开头添加：

```python
import logging

logger = logging.getLogger(__name__)
```

在 `extract_pii_from_text` 函数 return 前添加：

```python
    logger.info("PII 提取: %d 项 (身份证=%d, 手机号=%d, 银行卡=%d, 邮箱=%d)",
                len(items),
                sum(1 for i in items if i.type == "id_number"),
                sum(1 for i in items if i.type == "phone"),
                sum(1 for i in items if i.type == "bank_account"),
                sum(1 for i in items if i.type == "email"))
    return items
```

在 `extract_persons` 函数 return 前添加：

```python
    logger.info("人员提取: %d 人", len(persons))
    return persons
```

在 `group_pii_to_persons` 函数 return 前添加：

```python
    logger.info("PII 归属: %d 人, %d 项 PII (匿名=%d)",
                len(persons),
                len(pii_items),
                sum(1 for p in persons if not p.name))
    return persons
```

- [ ] **Step 2: 验证语法**

Run: `python -c "import ast; ast.parse(open('app/pii_extractor.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/pii_extractor.py
git commit -m "feat: add logging for PII extractor"
```

---

### Task 8: 为路由主流程添加总览日志

**Files:**
- Modify: `app/router.py`

- [ ] **Step 1: 修改 `app/router.py`**

`import` 区域中添加：

```python
import logging
from app.logger import default_logger

logger = default_logger
```

在 `upload_files` 函数中各个关键点添加日志：

1. 进入函数时：

```python
async def upload_files(files: List[UploadFile] = File(...)):
    """上传一个或多个文件，识别后返回结果"""
    results: List[FileResult] = []
    logger.info("===== 批量上传开始: %d 个文件 =====", len(files))
```

2. 每个文件开始处理时（第 40 行后）：

```python
    for file in files:
        try:
            file_path = await save_upload(file)
            filename = file.filename or "unknown"
            logger.info("--- 处理文件 [%d/%d]: %s ---", idx + 1, len(files), filename)
```

3. 各分支处理流程日志：

Word 分支处理后：

```python
    if is_word_file(file_path):
        ...
        raw_text = text
        logger.info("  [Word] 文本提取完成: %d 字符", len(raw_text))
```

PDF 文本型分支：

```python
    text = extract_text_from_pdf(file_path)
    if not text.strip():
        logger.info("  [PDF] 文本型提取为空, 切换 OCR")
        ...
    else:
        logger.info("  [PDF] 文本型提取: %d 字符", len(text))
```

图片 OCR 分支：

```python
    else:
        ocr_results = ocr.recognize(file_path)
        text = "\n".join(r.text for r in ocr_results)
        raw_text = text
        logger.info("  [图片] OCR 文本: %d 字符", len(raw_text))
```

4. 分类结果后：

```python
    doc_type, is_insurance = classify_doc_type(text, filename)

    if not is_insurance:
        logger.info("  -> 非保险文档, 跳过")
        results.append(...)
        continue
```

5. 识别完成后：

```python
    results.append(...)
    logger.info("  -> 完成: 险种=%s, 公司=%s, 人员=%d, 状态=%s",
                insurance_category, insurance_company, len(person_models), status)
```

6. 异常捕获：

```python
    except Exception as e:
        logger.error("处理文件失败: %s | %s", file.filename or "unknown", e, exc_info=True)
        results.append(...)
```

7. 返回前：

```python
    try:
        stats = compute_global_stats(results)
        logger.info("===== 批量上传完成: %d/%d 成功, %d 涉敏 =====",
                    sum(1 for r in results if r.status == "ok"),
                    len(results),
                    sum(1 for r in results if r.is_insurance_related))
        return UploadResponse(results=results, stats=stats)
    finally:
        cleanup_files()
```

8. 导出接口：

```python
@router.post("/api/export/excel")
async def export_excel(data: UploadResponse):
    logger.info("导出 Excel: %d 条记录", len(data.results))
    ...
    logger.info("Excel 导出完成")
    return StreamingResponse(...)


@router.post("/api/export/json")
async def export_json(data: UploadResponse):
    logger.info("导出 JSON: %d 条记录", len(data.results))
    ...
    logger.info("JSON 导出完成")
    return StreamingResponse(...)
```

完整修改后的 `router.py` 见实际文件编辑。

- [ ] **Step 2: 验证语法**

Run: `python -c "import ast; ast.parse(open('app/router.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/router.py
git commit -m "feat: add pipeline overview logging in router"
```

---

### Task 9: 为统计和导出模块添加日志

**Files:**
- Modify: `app/statistics.py`
- Modify: `app/exporter.py`

- [ ] **Step 1: 修改 `app/statistics.py`**

```python
"""以人为单位的涉敏统计"""
import logging
from typing import List
from app.models import FileResult, GlobalStats

logger = logging.getLogger(__name__)


def compute_global_stats(results: List[FileResult]) -> GlobalStats:
    """计算全局统计，含保险大类分支维度和异常检测"""
    stats = GlobalStats()
    ...
    logger.info("统计完成: 总涉敏文件=%d, 涉敏人数=%d, 异常=%d",
                stats.sensitive_files, stats.global_unique_persons, stats.anomaly_files)
    return stats
```

- [ ] **Step 2: 修改 `app/exporter.py`**

```python
"""导出模块：支持 Excel 和 JSON 格式"""
import json
import io
import logging
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from app.models import FileResult, GlobalStats

logger = logging.getLogger(__name__)
```

在 `export_to_excel` 和 `export_to_json` 中添加：

```python
def export_to_excel(results: List[FileResult], stats: GlobalStats) -> bytes:
    logger.info("正在生成 Excel (%d 条记录)", len(results))
    ...
    logger.info("Excel 生成完成 (%d bytes)", buf.tell())
    return buf.getvalue()


def export_to_json(results: List[FileResult], stats: GlobalStats) -> str:
    logger.info("正在生成 JSON (%d 条记录)", len(results))
    ...
    logger.info("JSON 生成完成 (%d 字符)", len(data))
    return json.dumps(data, ensure_ascii=False, indent=2)
```

- [ ] **Step 3: 验证语法**

Run: `python -c "import ast; ast.parse(open('app/statistics.py').read()); ast.parse(open('app/exporter.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/statistics.py app/exporter.py
git commit -m "feat: add logging for statistics and exporter"
```

---

### 执行手顺

计划保存到 `docs/superpowers/plans/2025-06-20-runtime-logging.md`。

**两种执行方式：**

1. **Subagent-Driven (推荐)** — 每个 Task 派发子 agent，任务间自动 review
2. **Inline Execution** — 在当前会话按 Task 顺序执行，中间带 checkpoint

选哪种？
