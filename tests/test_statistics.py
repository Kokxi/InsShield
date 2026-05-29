"""测试敏感信息统计（按险种类型区分）"""
import pytest
from app.statistics import compute_stats
from app.models import PolicyResult, PolicyFields


def make_result(
    applicant: str = "某人",
    insured: str = "",
    insurance_category: str = "life",
    status: str = "ok",
) -> PolicyResult:
    return PolicyResult(
        filename=f"{applicant}.pdf",
        is_policy=True,
        fields=PolicyFields(
            applicant=applicant,
            insured=insured,
            insurance_category=insurance_category,
        ),
        status=status,
    )


class TestComputeStats:
    """统计引擎测试"""

    def test_life_single_insured(self):
        """人身险：一个人一个保单"""
        results = [make_result(insured="李四", insurance_category="life")]
        stats = compute_stats(results)
        assert stats.life_insured_count == 1
        assert stats.life_insured_list == ["李四"]
        assert stats.property_count == 0

    def test_life_multiple_insured(self):
        """人身险：多个不同被保人"""
        results = [
            make_result(insured="李四", insurance_category="life"),
            make_result(insured="张三", insurance_category="life"),
        ]
        stats = compute_stats(results)
        assert stats.life_insured_count == 2
        assert stats.life_insured_list == ["张三", "李四"]

    def test_life_duplicate_insured(self):
        """人身险：同一被保人多张保单，去重后算1条"""
        results = [
            make_result(insured="李四", insurance_category="life"),
            make_result(insured="李四", insurance_category="life"),
        ]
        stats = compute_stats(results)
        assert stats.life_insured_count == 1
        assert stats.life_insured_list == ["李四"]

    def test_property_count(self):
        """财产险：按保单数统计"""
        results = [
            make_result(applicant="张三", insurance_category="car"),
            make_result(applicant="张三", insurance_category="car"),
        ]
        stats = compute_stats(results)
        assert stats.property_count == 2
        assert stats.life_insured_count == 0

    def test_mixed_types(self):
        """混合类型统计"""
        results = [
            make_result(applicant="张三", insured="张三", insurance_category="life"),
            make_result(applicant="李四", insured="李四", insurance_category="life"),
            make_result(applicant="王五", insurance_category="car"),
        ]
        stats = compute_stats(results)
        assert stats.life_insured_count == 2
        assert stats.property_count == 1
        assert stats.total_applicant_count == 3

    def test_unknown_not_counted(self):
        """未知类型不计入人身险/财产险统计"""
        results = [
            make_result(applicant="张三", insurance_category="unknown"),
        ]
        stats = compute_stats(results)
        assert stats.unknown_count == 1
        assert stats.life_insured_count == 0
        assert stats.property_count == 0

    def test_skip_non_ok_status(self):
        """非ok状态不统计"""
        results = [
            make_result(insured="李四", status="ok"),
            make_result(insured="张三", status="not_policy"),
            PolicyResult(
                filename="error.pdf",
                is_policy=False,
                fields=PolicyFields(insured="王五", insurance_category="life"),
                status="error",
                error_message="识别失败",
            ),
        ]
        stats = compute_stats(results)
        assert stats.life_insured_count == 1
        assert stats.life_insured_list == ["李四"]

    def test_empty_results(self):
        """空列表"""
        stats = compute_stats([])
        assert stats.life_insured_count == 0
        assert stats.life_insured_list == []
        assert stats.property_count == 0
        assert stats.unknown_count == 0
        assert stats.total_applicant_count == 0

    def test_all_not_policy(self):
        """全都不是保单"""
        results = [
            PolicyResult(
                filename="a.pdf", is_policy=False,
                fields=PolicyFields(), status="not_policy",
            )
        ]
        stats = compute_stats(results)
        assert stats.life_insured_count == 0

    def test_life_multiple_insured_in_one_policy(self):
        """人寿险：一个保单多个被保人（顿号分隔）"""
        results = [make_result(insured="张三、李四", insurance_category="life")]
        stats = compute_stats(results)
        assert stats.life_insured_count == 2
        assert stats.life_insured_list == ["张三", "李四"]

    def test_property_applicant_list(self):
        """财产险投保人列表"""
        results = [
            make_result(applicant="张三", insurance_category="car"),
            make_result(applicant="李四", insurance_category="property"),
        ]
        stats = compute_stats(results)
        assert stats.property_count == 2
        assert "张三" in stats.property_applicant_list
        assert "李四" in stats.property_applicant_list

    def test_total_applicant_count(self):
        """所有保单去重投保人数"""
        results = [
            make_result(applicant="张三", insurance_category="life"),
            make_result(applicant="张三", insurance_category="car"),
            make_result(applicant="李四", insurance_category="life"),
        ]
        stats = compute_stats(results)
        assert stats.total_applicant_count == 2

    def test_health_and_accident(self):
        """健康险和意外险也归入人身险"""
        results = [
            make_result(insured="张三", insurance_category="health"),
            make_result(insured="李四", insurance_category="accident"),
        ]
        stats = compute_stats(results)
        assert stats.life_insured_count == 2
