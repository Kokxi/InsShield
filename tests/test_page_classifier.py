"""测试保单首页分类器"""
import pytest
from app.page_classifier import is_policy_page
from app.ocr_engine import OcrResult


def make_results(texts: list[str]) -> list:
    return [OcrResult(t, 0.9, []) for t in texts]


class TestIsPolicyPage:
    def test_policy_page_sufficient_keywords(self):
        """保单页：关键词足够多"""
        texts = ["保险单", "保单号", "投保人", "被保险人", "保费", "生效日期"]
        assert is_policy_page(make_results(texts)) is True

    def test_policy_page_exact_threshold(self):
        """刚好达到阈值（3个关键词）"""
        texts = ["保险单", "投保人", "保费"]
        assert is_policy_page(make_results(texts)) is True

    def test_not_policy_page_insufficient(self):
        """非保单页：关键词太少"""
        texts = ["保险", "重要提示"]
        assert is_policy_page(make_results(texts)) is False

    def test_not_policy_page_no_keywords(self):
        """非保单页：无关键词"""
        texts = ["第一章", "总则", "本合同"]
        assert is_policy_page(make_results(texts)) is False

    def test_empty_results(self):
        """空识别结果"""
        assert is_policy_page([]) is False

    def test_keywords_in_long_text(self):
        """关键词嵌在长文本中"""
        texts = [
            "中国平安人寿保险股份有限公司",
            "保险单号码：P20230001",
            "投保人：张三",
            "保险费：10000元",
            "如为无民事行为能力人",
        ]
        # "保险单", "投保人", "保费" (在"保险费"中) 均应匹配，达到3个
        assert is_policy_page(make_results(texts)) is True
