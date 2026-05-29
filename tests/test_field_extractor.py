"""测试字段提取器"""
import pytest
from app.field_extractor import extract_fields, _find_value_by_keyword, _find_insurance_company
from app.ocr_engine import OcrResult


class TestFindInsuranceCompany:
    def test_matched(self):
        results = [OcrResult("中国人寿保险股份有限公司", 0.95, [])]
        assert _find_insurance_company(results) == "中国人寿"

    def test_not_matched(self):
        results = [OcrResult("某保险公司", 0.9, [])]
        assert _find_insurance_company(results) == ""

    def test_multiple_companies_first_wins(self):
        results = [
            OcrResult("中国平安", 0.95, []),
            OcrResult("中国人寿", 0.95, []),
        ]
        # 遍历顺序是先匹配到的
        assert _find_insurance_company(results) == "中国平安"


class TestFindValueByKeyword:
    def test_next_word_value(self):
        """关键词后紧邻有效文字"""
        results = [OcrResult("投保人", 0.99, []), OcrResult("张三", 0.96, [])]
        assert _find_value_by_keyword(results, ["投保人"]) == "张三"

    def test_inline_value_with_colon(self):
        """关键词冒号后带值"""
        results = [OcrResult("保费：5000元", 0.95, [])]
        assert _find_value_by_keyword(results, ["保费"]) == "5000元"

    def test_inline_value_without_keyword_sep(self):
        """关键词后无冒号但有值"""
        results = [OcrResult("保费5000元", 0.95, [])]
        assert _find_value_by_keyword(results, ["保费"]) == "5000元"

    def test_no_value_found(self):
        """只有关键词，后面无值"""
        results = [OcrResult("投保人", 0.99, [])]
        assert _find_value_by_keyword(results, ["投保人"]) == ""

    def test_skip_empty_after_keyword(self):
        """关键词后有空文字，再下一个"""
        results = [OcrResult("投保人", 0.99, []), OcrResult("", 0.0, []), OcrResult("张三", 0.96, [])]
        assert _find_value_by_keyword(results, ["投保人"]) == "张三"

    def test_multiple_keywords_first_match(self):
        """多个关键词，匹配第一个"""
        results = [OcrResult("被保险人", 0.99, []), OcrResult("李四", 0.97, [])]
        assert _find_value_by_keyword(results, ["被保险人", "被保人"]) == "李四"


class TestExtractFields:
    def test_extract_all_fields(self):
        """完整保单页，提取所有字段"""
        results = [
            OcrResult("中国人寿", 0.95, []),
            OcrResult("保单号", 0.98, []),
            OcrResult("1234567890", 0.97, []),
            OcrResult("投保人", 0.99, []),
            OcrResult("张三", 0.96, []),
            OcrResult("被保险人", 0.99, []),
            OcrResult("李四", 0.97, []),
            OcrResult("受益人", 0.98, []),
            OcrResult("王五", 0.95, []),
            OcrResult("保费", 0.99, []),
            OcrResult("10000元", 0.96, []),
            OcrResult("交费方式", 0.98, []),
            OcrResult("年交", 0.97, []),
            OcrResult("生效日期", 0.99, []),
            OcrResult("2024-01-01", 0.98, []),
            OcrResult("保险期间", 0.98, []),
            OcrResult("终身", 0.97, []),
            OcrResult("销售经理", 0.97, []),
            OcrResult("赵六", 0.95, []),
        ]
        fields = extract_fields(results)
        assert fields.insurance_company == "中国人寿"
        assert fields.policy_number == "1234567890"
        assert fields.applicant == "张三"
        assert fields.insured == "李四"
        assert fields.beneficiary == "王五"
        assert fields.premium == "10000元"
        assert fields.payment_method == "年交"
        assert fields.effective_date == "2024-01-01"
        assert fields.insurance_period == "终身"
        assert fields.sales_manager == "赵六"

    def test_partial_fields(self):
        """部分字段缺失"""
        results = [
            OcrResult("中国人寿", 0.95, []),
            OcrResult("投保人", 0.99, []),
            OcrResult("张三", 0.96, []),
            OcrResult("保费", 0.99, []),
            OcrResult("5000元", 0.96, []),
        ]
        fields = extract_fields(results)
        assert fields.insurance_company == "中国人寿"
        assert fields.applicant == "张三"
        assert fields.premium == "5000元"
        assert fields.insured is None

    def test_keyword_inline_value(self):
        """关键词冒号后带值"""
        results = [
            OcrResult("保费：5000元", 0.95, []),
            OcrResult("被保险人:李四", 0.96, []),
        ]
        fields = extract_fields(results)
        assert fields.premium == "5000元"
        assert fields.insured == "李四"

    def test_empty_results(self):
        """空OCR结果"""
        fields = extract_fields([])
        assert fields.insurance_company == ""  # _find_insurance_company 返回空字符串
        assert fields.insured is None

    def test_insurance_company_not_in_list(self):
        """保险公司不在预设列表中"""
        results = [OcrResult("未知保险公司", 0.95, []), OcrResult("投保人", 0.99, []), OcrResult("张三", 0.96, [])]
        fields = extract_fields(results)
        assert fields.insurance_company == ""
        assert fields.applicant == "张三"
