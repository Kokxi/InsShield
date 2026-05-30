"""测试敏感信息统计（按险种类型区分）"""
import pytest
from app.statistics import compute_global_stats
from app.models import FileResult, PersonModel


def make_result(
    name: str = "某人",
    category: str = "life",
    status: str = "ok",
    branch: str = "life",
    is_related: bool = True,
) -> FileResult:
    return FileResult(
        filename=f"{name}.pdf",
        is_insurance_related=is_related,
        insurance_category=category,
        insurance_category_display={"life": "人寿险", "health": "健康险", "accident": "意外险", "car": "车险", "property": "财产险"}.get(category, "未知"),
        insurance_branch=branch,
        insurance_branch_display={"life": "人身保险", "property": "财产保险"}.get(branch, "未知"),
        persons=[PersonModel(name=name, role="applicant", role_display="投保人")] if name else [],
        sensitive_count=1 if name else 0,
        status=status,
    )


class TestComputeStats:
    """统计引擎测试"""

    def test_life_single(self):
        """人身险：一个人一个文件"""
        results = [make_result(name="李四", category="life")]
        stats = compute_global_stats(results)
        assert stats.life_sensitive_files == 1
        assert stats.life_unique_persons == 1
        assert stats.property_files == 0

    def test_life_multiple(self):
        """人身险：多个不同人"""
        results = [
            make_result(name="李四", category="life"),
            make_result(name="张三", category="life"),
        ]
        stats = compute_global_stats(results)
        assert stats.life_sensitive_files == 2
        assert stats.life_unique_persons == 2

    def test_property_count(self):
        """财产险：按文件数统计"""
        results = [
            make_result(name="张三", category="car", branch="property"),
            make_result(name="张三", category="car", branch="property"),
        ]
        stats = compute_global_stats(results)
        assert stats.property_files == 2
        assert stats.property_sensitive_persons == 2
        assert stats.life_sensitive_files == 0

    def test_mixed_types(self):
        """混合类型统计"""
        results = [
            make_result(name="张三", category="life"),
            make_result(name="李四", category="life"),
            make_result(name="王五", category="car", branch="property"),
        ]
        stats = compute_global_stats(results)
        assert stats.life_sensitive_files == 2
        assert stats.life_unique_persons == 2
        assert stats.property_files == 1
        assert stats.property_sensitive_persons == 1

    def test_unknown_not_counted(self):
        """未知类型不计入分支统计"""
        results = [
            FileResult(
                filename="未知.pdf", is_insurance_related=True,
                insurance_category="unknown", insurance_category_display="未知",
                insurance_branch="unknown", insurance_branch_display="未知",
                status="ok", sensitive_count=0,
            ),
        ]
        stats = compute_global_stats(results)
        assert stats.total_files == 1
        assert stats.life_sensitive_files == 0
        assert stats.property_files == 0

    def test_skip_non_ok_status(self):
        """非ok状态不统计"""
        results = [
            make_result(name="李四", status="ok"),
            FileResult(
                filename="error.pdf",
                status="not_insurance",
                error_message="非保险文档",
            ),
            FileResult(
                filename="error2.pdf",
                status="error",
                error_message="识别失败",
            ),
        ]
        stats = compute_global_stats(results)
        assert stats.total_files == 1
        assert stats.life_sensitive_files == 1

    def test_empty_results(self):
        """空列表"""
        stats = compute_global_stats([])
        assert stats.total_files == 0

    def test_skip_not_insurance_related(self):
        """非保险相关的跳过"""
        results = [
            make_result(name="张三", is_related=False, status="not_insurance"),
        ]
        stats = compute_global_stats(results)
        assert stats.total_files == 0

    def test_health_and_accident(self):
        """健康险和意外险也归入人身险"""
        results = [
            make_result(name="张三", category="health"),
            make_result(name="李四", category="accident"),
        ]
        stats = compute_global_stats(results)
        assert stats.life_sensitive_files == 2
        assert stats.life_unique_persons == 2

    def test_anomaly_counted(self):
        """异常文件计数"""
        results = [
            FileResult(
                filename="异常.pdf", is_insurance_related=True,
                insurance_category="car", insurance_category_display="车险",
                insurance_branch="property", insurance_branch_display="财产保险",
                anomaly="财产险多人",
                persons=[PersonModel(name="张三"), PersonModel(name="李四")],
                sensitive_count=2, status="ok",
            ),
        ]
        stats = compute_global_stats(results)
        assert stats.anomaly_files == 1
        assert stats.property_files == 1

    def test_no_pii_file(self):
        """无PII文件不算涉敏"""
        results = [
            FileResult(
                filename="无敏.pdf", is_insurance_related=True,
                insurance_category="life", insurance_category_display="人寿险",
                insurance_branch="life", insurance_branch_display="人身保险",
                status="ok", sensitive_count=0,
            ),
        ]
        stats = compute_global_stats(results)
        assert stats.sensitive_files == 0
        assert stats.non_sensitive_files == 1
        assert stats.life_sensitive_files == 1  # 人身险文件数，非涉敏计数
        assert stats.life_unique_persons == 0
