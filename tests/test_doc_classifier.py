"""测试文档类型分类器"""
import pytest
from app.doc_classifier import classify_doc_type, get_doc_type_display


class TestClassifyDocType:
    """文档类型分类器测试"""

    def test_policy_by_text(self):
        """从文本识别保单"""
        text = "保险单\n投保人：张三\n被保人：李四"
        doc_type, is_insurance = classify_doc_type(text, "")
        assert doc_type == "policy"
        assert is_insurance is True

    def test_application_by_text(self):
        """从文本识别投保单"""
        text = "投保单\n申请人：张三\n投保申请"
        doc_type, is_insurance = classify_doc_type(text, "")
        assert doc_type == "application"
        assert is_insurance is True

    def test_endorsement_by_text(self):
        """从文本识别批单"""
        text = "批单\n批改申请\n变更内容"
        doc_type, is_insurance = classify_doc_type(text, "")
        assert doc_type == "endorsement"
        assert is_insurance is True

    def test_claim_by_text(self):
        """从文本识别理赔书"""
        text = "理赔决定书\n理赔申请\n赔款金额"
        doc_type, is_insurance = classify_doc_type(text, "")
        assert doc_type == "claim"
        assert is_insurance is True

    def test_policy_by_filename(self):
        """从文件名识别保单"""
        text = "一些内容"
        doc_type, is_insurance = classify_doc_type(text, "保险单_张三.pdf")
        assert doc_type == "policy"
        assert is_insurance is True

    def test_application_by_filename(self):
        """从文件名识别投保单"""
        text = "一些内容"
        doc_type, is_insurance = classify_doc_type(text, "投保单_李四.pdf")
        assert doc_type == "application"
        assert is_insurance is True

    def test_insurance_related_other(self):
        """保险相关但未匹配具体类型"""
        text = "保险相关信息\n包含保费信息\n保险责任范围\n保险公司条款"
        doc_type, is_insurance = classify_doc_type(text, "")
        assert doc_type == "other"
        assert is_insurance is True

    def test_not_insurance(self):
        """非保险文档"""
        text = "这是一份普通文档\n没有任何保险相关内容"
        doc_type, is_insurance = classify_doc_type(text, "")
        assert doc_type == "unknown"
        assert is_insurance is False

    def test_empty_input(self):
        """空输入"""
        doc_type, is_insurance = classify_doc_type("", "")
        assert doc_type == "unknown"
        assert is_insurance is False


class TestGetDocTypeDisplay:
    """文档类型显示名测试"""

    def test_policy_name(self):
        assert get_doc_type_display("policy") == "保单"

    def test_application_name(self):
        assert get_doc_type_display("application") == "投保单"

    def test_unknown_name(self):
        assert get_doc_type_display("unknown") == "未知"

    def test_nonexistent(self):
        assert get_doc_type_display("bogus") == "未知"
