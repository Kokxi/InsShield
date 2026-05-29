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
