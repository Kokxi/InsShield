"""保单首页判定器：根据OCR结果中的关键词组命中数判断是否为保单"""
from typing import List
from app.ocr_engine import OcrResult
from app.config import POLICY_KEYWORD_GROUPS, POLICY_PAGE_THRESHOLD


def is_policy_page(results: List[OcrResult]) -> bool:
    """
    判断OCR识别结果是否为保单页面。
    策略：按语义分组，同组内任一词命中即算该组命中，命中组数 ≥ 阈值则判定为保单。
    """
    text = "".join(r.text for r in results)
    hit_count = sum(
        1 for group in POLICY_KEYWORD_GROUPS
        if any(kw in text for kw in group)
    )
    return hit_count >= POLICY_PAGE_THRESHOLD
