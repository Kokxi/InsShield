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

    def test_initial_state(self):
        e = OcrEngine()
        assert e._ocr is None


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
