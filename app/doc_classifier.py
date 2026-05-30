"""文档类型分类器：识别保险业务文档类型 + 判断是否保险相关"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# 文档类型关键词（按优先级从高到低，先命中先归谁）
DOC_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("endorsement", ["批单", "批改", "批注", "变更申请"]),
    ("claim", ["理赔", "给付通知", "赔款", "理赔决定"]),
    ("application", ["投保单", "投保申请", "投保书"]),
    ("certificate", ["保险证", "保险凭证", "电子凭证"]),
    ("renewal", ["续保", "续期", "续保通知"]),
    ("policy", ["保险单", "电子保单", "保险合同"]),
]

DOC_TYPE_NAMES = {
    "policy": "保单",
    "application": "投保单",
    "endorsement": "批单",
    "certificate": "保险证",
    "claim": "理赔书",
    "renewal": "续保通知",
    "other": "其他保险文档",
    "unknown": "未知",
}

# 保险相关关键词（用于判断是否保险文档）
INSURANCE_KEYWORDS = [
    "保险", "保单", "投保", "被保", "理赔", "保费", "险种",
    "保险公司", "保险合同", "保险责任", "保险期间", "保额",
]


def classify_doc_type(text: str, filename: str = "") -> Tuple[str, bool]:
    """识别文档类型，返回 (doc_type, is_insurance_related)"""
    is_insurance = _is_insurance_related(text, filename)

    # 从文件名推断
    for doc_type, keywords in DOC_TYPE_RULES:
        if any(kw in filename for kw in keywords):
            logger.info("文档分类: %s -> %s (文件名命中)", filename or "(无文件名)", doc_type)
            return doc_type, True

    # 从文本前 500 字推断（标题区域）
    title = text[:500]
    for doc_type, keywords in DOC_TYPE_RULES:
        if any(kw in title for kw in keywords):
            logger.info("文档分类: %s -> %s (文本命中)", filename or "(无文件名)", doc_type)
            return doc_type, True

    if is_insurance:
        logger.info("文档分类: %s -> other (保险相关但未匹配到具体类型)", filename or "(无文件名)")
        return "other", True

    logger.info("文档分类: %s -> unknown (非保险文档)", filename or "(无文件名)")
    return "unknown", False


def _is_insurance_related(text: str, filename: str) -> bool:
    """判断是否保险相关文档"""
    full = filename + text
    hits = sum(1 for kw in INSURANCE_KEYWORDS if kw in full)
    return hits >= 2


def get_doc_type_display(doc_type: str) -> str:
    return DOC_TYPE_NAMES.get(doc_type, "未知")
