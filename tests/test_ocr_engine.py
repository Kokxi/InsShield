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
