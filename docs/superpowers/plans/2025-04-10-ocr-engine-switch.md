# OCR Engine Switch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace PaddleOCR with rapidocr_onnxruntime while keeping `OcrResult` / `OcrEngine` interface identical — zero downstream changes.

**Architecture:** Single-file swap inside `app/ocr_engine.py`. The `load()` method instantiates `RapidOCR()` instead of `PaddleOCR()`. The `recognize()` method maps rapidocr's return format (`[[box, text, conf], ...]`) into `List[OcrResult]` — then all downstream code (field extractor, classifier, router) stays untouched.

**Tech Stack:** Python 3.10+, rapidocr_onnxruntime, ONNX Runtime (bundled), pytest.

---
### File Structure

| File | Role |
|------|------|
| `app/ocr_engine.py` | **Modify** — replace PaddleOCR internals with RapidOCR |
| `requirements.txt` | **Modify** — comment out paddlepaddle/paddleocr |
| `tests/test_ocr_engine.py` | **Modify** — add real-image integration test |
| `doc/test1.png` | **Use** — existing test image in repo |

---

### Task 1: Replace ocr_engine.py internals

**Files:**
- Modify: `app/ocr_engine.py` (full file rewrite of inner impl)

- [ ] **Step 1: Read current file**

Read `app/ocr_engine.py` to confirm current state.

- [ ] **Step 2: Write new implementation**

Replace the entire content of `app/ocr_engine.py` with:

```python
"""OCR 引擎封装（rapidocr_onnxruntime），全局单例"""
import threading
from pathlib import Path
from typing import List, Optional

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

    def recognize(self, image_path: Path) -> List[OcrResult]:
        """识别单张图片，返回文字块列表

        rapidocr_onnxruntime.RapidOCR.__call__() 返回格式：
          ([[box, text, confidence_str], ...], [det_elapse, cls_elapse, rec_elapse])
          或 (None, None) 当无识别结果。

        box: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] 的 list
        text: str
        confidence_str: str 类型置信度
        """
        self.load()
        result, _ = self._ocr(str(image_path))

        items: List[OcrResult] = []
        if result is None:
            return items

        for box, text, conf_str in result:
            items.append(OcrResult(
                text=text,
                confidence=float(conf_str),
                bbox=box,
            ))
        return items
```

- [ ] **Step 3: Verify the file reads correctly**

Run: `python -c "from app.ocr_engine import OcrResult, OcrEngine; print('OK')"`
Expected: `OK` (no import errors)

- [ ] **Step 4: Run existing mock tests**

Run: `pytest tests/test_ocr_engine.py -v`
Expected: 4 passed (TestOcrResult × 3, TestOcrEngine singletons × 2) — these do NOT load the real model.

- [ ] **Step 5: Commit**

```bash
git add app/ocr_engine.py
git commit -m "refactor: replace PaddleOCR with rapidocr_onnxruntime

Co-Authored-By: AtomCode (deepseek-v4-flash) <noreply@atomgit.com>"
```

---

### Task 2: Update dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Edit requirements.txt**

Comment out paddlepaddle and paddleocr (keep for rollback reference):

```
fastapi==0.136.3
uvicorn[standard]==0.48.0
python-multipart==0.0.29
# paddlepaddle==3.3.1        # 已替换为 rapidocr_onnxruntime
# paddleocr==3.6.0           # 已替换为 rapidocr_onnxruntime
PyMuPDF==1.27.2
openpyxl==3.1.5
pytest==8.3.0
aiofiles==25.1.0
```

- [ ] **Step 2: Commit**

```bash
git add requirements.txt
git commit -m "chore: comment out paddlepaddle/paddleocr deps

Co-Authored-By: AtomCode (deepseek-v4-flash) <noreply@atomgit.com>"
```

---

### Task 3: Add real-image integration test

**Files:**
- Modify: `tests/test_ocr_engine.py`

- [ ] **Step 1: Add integration test class**

Append to `tests/test_ocr_engine.py`:

```python
class TestOcrEngineReal:
    """真实图片集成测试（需 doc/test1.png 存在）"""

    def test_real_image_recognize(self):
        img_path = Path(__file__).parent.parent / "doc" / "test1.png"
        if not img_path.exists():
            pytest.skip("test image not found: doc/test1.png")
        engine = OcrEngine()
        results = engine.recognize(img_path)
        assert len(results) > 50, f"Expected >50 text blocks, got {len(results)}"
        first = results[0]
        assert isinstance(first.text, str) and len(first.text) > 0
        assert 0.0 <= first.confidence <= 1.0
        assert len(first.bbox) == 4  # 4 corners
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_ocr_engine.py::TestOcrEngineReal -v`
Expected: PASS (may take 8-15s for model load + inference)

- [ ] **Step 3: Run all tests**

Run: `pytest tests/ -v`
Expected: all existing tests pass, plus the new real-image test passes

- [ ] **Step 4: Commit**

```bash
git add tests/test_ocr_engine.py
git commit -m "test: add real-image OCR integration test with rapidocr

Co-Authored-By: AtomCode (deepseek-v4-flash) <noreply@atomgit.com>"
```

---

### Task 4: End-to-end smoke test

**Files:**
- Use: `main.py`, `app/router.py`, `doc/test1.png` (running server)

- [ ] **Step 1: Start the server in background, upload test image, check response**

```bash
cd /d D:\data\aatomcode\jinrong-sdd
start /B python main.py
timeout /t 5 /nobreak >nul
curl -s -F "files=@doc/test1.png" http://127.0.0.1:8000/api/upload
```

Expected: HTTP 200, JSON with `results[0].status == "ok"`, `fields` populated with insurance category, policy number etc.

- [ ] **Step 2: Stop the server**

```bash
taskkill /F /IM python.exe 2>nul || true
```

- [ ] **Step 3: If the smoke test passes, commit a conclusion marker (optional)**

```bash
git tag smoke-test-passed 2>/dev/null || true
```
