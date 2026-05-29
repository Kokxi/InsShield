"""从OCR结果中提取保单各字段值"""
from typing import List
from app.ocr_engine import OcrResult
from app.models import PolicyFields
from app.config import INSURANCE_COMPANIES


def _find_value_by_keyword(results: List[OcrResult], keywords: List[str]) -> str:
    """在OCR结果列表中查找关键词，取紧挨着的下一个有效文字作为值"""
    texts = [r.text.strip() for r in results]
    for i, text in enumerate(texts):
        for kw in keywords:
            # 关键词完全匹配或作为前缀
            if text == kw or text.startswith(kw):
                # 先检查关键词是否自带值（如"保费：10000元"）
                remaining = text[len(kw):].lstrip("：:")
                if remaining:
                    return remaining
                # 取下一个非空文字
                for j in range(i + 1, len(texts)):
                    if texts[j]:
                        return texts[j]
    return ""


def _find_insurance_company(results: List[OcrResult]) -> str:
    """从OCR结果中识别保险公司名称"""
    texts = [r.text.strip() for r in results]
    for text in texts:
        for company in INSURANCE_COMPANIES:
            if company in text:
                return company
    return ""


def extract_fields(results: List[OcrResult]) -> PolicyFields:
    """
    从OCR识别结果中提取所有保单字段。
    使用关键词+位置相邻策略提取。
    """
    fields = PolicyFields()

    fields.insurance_company = _find_insurance_company(results)

    # 各字段的关键词列表
    keyword_map = [
        ("policy_type", ["险种", "险种名称", "产品名称", "产品"]),
        ("policy_number", ["保单号", "保单号码", "保险单号"]),
        ("applicant", ["投保人"]),
        ("insured", ["被保险人", "被保人"]),
        ("beneficiary", ["受益人"]),
        ("premium", ["保险费", "保费", "保险金额"]),
        ("payment_method", ["交费方式", "缴费方式"]),
        ("effective_date", ["生效日期", "生效日", "合同生效日"]),
        ("insurance_period", ["保险期间", "保险期限", "保障期间"]),
        ("sales_manager", ["销售经理", "业务员", "营销员", "代理人", "客户经理"]),
    ]

    for field_name, keywords in keyword_map:
        value = _find_value_by_keyword(results, keywords)
        if value:
            setattr(fields, field_name, value)

    return fields
