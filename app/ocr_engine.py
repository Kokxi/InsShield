"""PaddleOCR 引擎封装，全局单例"""
import threading
from pathlib import Path
from typing import List, Optional
import numpy as np
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
    """全局OCR引擎（单例，线程安全）"""

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
        """加载PaddleOCR模型（首次调用时）
        
        PaddleOCR v3.6.0 API:
        - use_textline_orientation 替代已废弃的 use_angle_cls
        - device='cpu' 替代已移除的 use_gpu=False
        - show_log 参数已移除
        """
        if self._ocr is None:
            with self._lock:
                if self._ocr is None:
                    from paddleocr import PaddleOCR
                    self._ocr = PaddleOCR(
                        use_textline_orientation=True,
                        lang="ch",
                        device="cpu",
                    )

    def recognize(self, image_path: Path) -> List[OcrResult]:
        """识别单张图片，返回文字块列表
        
        PaddleOCR v3.6.0 使用 predict() 替代已废弃的 ocr()。
        predict() 返回 OCRResult（dict子类），字段：
          - rec_texts: List[str]  识别文本
          - rec_scores: np.ndarray  置信度
          - rec_polys: List[np.ndarray]  检测框 [[x,y],...]
        """
        self.load()
        items: List[OcrResult] = []
        for page in self._ocr.predict(str(image_path), use_textline_orientation=True):
            texts = page.get("rec_texts") or []
            scores = page.get("rec_scores") or []
            polys = page.get("rec_polys") or []
            if isinstance(scores, np.ndarray):
                scores = scores.tolist()
            for text, score, poly in zip(texts, scores, polys):
                bbox = poly.tolist() if isinstance(poly, np.ndarray) else poly
                items.append(OcrResult(text=text, confidence=float(score), bbox=bbox))
        return items
