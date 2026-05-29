"""测试导出模块"""
import json
import pytest
from app.exporter import export_to_excel, export_to_json
from app.models import PolicyResult, PolicyFields, SensitiveStats


def make_result(insured: str, premium: str = "10000") -> PolicyResult:
    return PolicyResult(
        filename=f"{insured}.pdf",
        is_policy=True,
        fields=PolicyFields(insured=insured, premium=premium, insurance_company="中国人寿"),
        status="ok",
    )


class TestExportToJson:
    def test_export_structure(self):
        results = [make_result("李四"), make_result("张三")]
        stats = SensitiveStats(total_unique_insured=2, insured_list=["张三", "李四"], details=results)
        output = export_to_json(results, stats)
        data = json.loads(output)
        assert data["sensitive_stats"]["total_unique_insured"] == 2
        assert len(data["details"]) == 2
        assert data["details"][0]["fields"]["insured"] == "李四"
        assert data["details"][1]["fields"]["insured"] == "张三"

    def test_empty_export(self):
        output = export_to_json([], SensitiveStats(total_unique_insured=0, insured_list=[], details=[]))
        data = json.loads(output)
        assert data["sensitive_stats"]["total_unique_insured"] == 0
        assert data["details"] == []

    def test_json_is_readable(self):
        results = [make_result("李四", "5000元")]
        stats = SensitiveStats(total_unique_insured=1, insured_list=["李四"], details=results)
        output = export_to_json(results, stats)
        assert "敏感" not in output  # ensure_ascii=False, output is Chinese
        assert "李四" in output


class TestExportToExcel:
    def test_export_creates_workbook(self):
        results = [make_result("李四", "10000元")]
        stats = SensitiveStats(total_unique_insured=1, insured_list=["李四"], details=results)
        data = export_to_excel(results, stats)
        assert isinstance(data, bytes)
        assert len(data) > 0  # Excel文件至少有一些字节

    def test_export_multiple_rows(self):
        results = [make_result("李四"), make_result("张三")]
        stats = SensitiveStats(total_unique_insured=2, insured_list=["张三", "李四"], details=results)
        data = export_to_excel(results, stats)
        assert isinstance(data, bytes)
        assert len(data) > 100

    def test_export_empty(self):
        data = export_to_excel([], SensitiveStats(total_unique_insured=0, insured_list=[], details=[]))
        assert isinstance(data, bytes)

    def test_has_two_sheets(self):
        """验证Excel有两个Sheet"""
        from openpyxl import load_workbook
        import io
        results = [make_result("李四")]
        stats = SensitiveStats(total_unique_insured=1, insured_list=["李四"], details=results)
        data = export_to_excel(results, stats)
        wb = load_workbook(io.BytesIO(data))
        assert "识别明细" in wb.sheetnames
        assert "敏感信息统计" in wb.sheetnames
