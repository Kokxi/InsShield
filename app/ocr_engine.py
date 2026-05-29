"""PaddleOCR 引擎封装，全局单例"""
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
            from paddleocr import PaddleOCR
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
