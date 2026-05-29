"""测试敏感信息统计"""
import pytest
from app.statistics import compute_stats
from app.models import PolicyResult, PolicyFields


def make_result(insured: str, status: str = "ok") -> PolicyResult:
    return PolicyResult(
        filename=f"{insured}.pdf",
        is_policy=True,
        fields=PolicyFields(insured=insured),
        status=status,
    )


class TestComputeStats:
    def test_single_insured(self):
        """一个人一个保单"""
        results = [make_result("李四")]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 1
        assert stats.insured_list == ["李四"]

    def test_multiple_insured_different(self):
        """多个不同被保人"""
        results = [make_result("李四"), make_result("张三"), make_result("王五")]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 3
        assert stats.insured_list == ["张三", "李四", "王五"]

    def test_duplicate_insured(self):
        """同一人多个保单，去重后算1条"""
        results = [
            make_result("李四"),
            make_result("李四"),
            make_result("张三"),
        ]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 2
        assert stats.insured_list == ["张三", "李四"]

    def test_skip_non_ok_status(self):
        """非ok状态不统计"""
        results = [
            make_result("李四", status="ok"),
            make_result("张三", status="not_policy"),
            PolicyResult(
                filename="error.pdf",
                is_policy=False,
                fields=PolicyFields(insured="王五"),
                status="error",
                error_message="识别失败",
            ),
        ]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 1
        assert stats.insured_list == ["李四"]

    def test_empty_results(self):
        """空列表"""
        stats = compute_stats([])
        assert stats.total_unique_insured == 0
        assert stats.insured_list == []

    def test_all_not_policy(self):
        """全都不是保单"""
        results = [
            PolicyResult(
                filename="a.pdf", is_policy=False, fields=PolicyFields(), status="not_policy"
            )
        ]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 0

    def test_multiple_insured_in_one_policy(self):
        """一个保单多个被保人（顿号分隔）"""
        results = [make_result("张三、李四")]
        stats = compute_stats(results)
        assert stats.total_unique_insured == 2
        assert stats.insured_list == ["张三", "李四"]
