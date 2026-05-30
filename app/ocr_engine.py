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
        """识别单张图片，返回文字块列表

        rapidocr_onnxruntime.RapidOCR.__call__() 返回格式：
          ([[box, text, confidence_str], ...], [det_elapse, cls_elapse, rec_elapse])
          或 (None, None) 当无识别结果。

        box: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] 的 list
        text: str
        confidence_str: str 类型置信度
        """
        self.load()
        logger.info("OCR 识别: %s", image_path.name)
        result, _ = self._ocr(str(image_path))

        items: List[OcrResult] = []
        if result is None:
            logger.debug("  -> 未识别到文字")
            return items

        for box, text, conf_str in result:
            items.append(OcrResult(
                text=text,
                confidence=float(conf_str),
                bbox=box,
            ))

        logger.info("  -> 识别到 %d 个文字块", len(items))
        return items
