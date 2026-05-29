"""测试导出模块"""
import io
import json
import pytest
from app.exporter import export_to_excel, export_to_json
from app.models import PolicyResult, PolicyFields, SensitiveStats


def make_result(insured: str, premium: str = "10000") -> PolicyResult:
    return PolicyResult(
        filename=f"{insured}.pdf",
        is_policy=True,
        fields=PolicyFields(
            insured=insured,
            premium=premium,
            insurance_category="life",
        ),
        status="ok",
    )


class TestExportToJson:
    def test_export_structure(self):
        results = [make_result("李四"), make_result("张三")]
        stats = SensitiveStats(
            life_insured_count=2,
            life_insured_list=["张三", "李四"],
        )
        output = export_to_json(results, stats)
        data = json.loads(output)
        assert data["insurance_stats"]["life_insured_count"] == 2
        assert len(data["details"]) == 2
        assert data["details"][0]["fields"]["insured"] == "李四"
        assert data["details"][1]["fields"]["insured"] == "张三"

    def test_empty_export(self):
        output = export_to_json([], SensitiveStats())
        data = json.loads(output)
        assert data["insurance_stats"]["life_insured_count"] == 0
        assert data["details"] == []

    def test_json_is_readable(self):
        results = [make_result("李四", "5000元")]
        stats = SensitiveStats(life_insured_count=1, life_insured_list=["李四"])
        output = export_to_json(results, stats)
        assert "李四" in output

    def test_insurance_category_in_detail(self):
        """detail中应包含insurance_category字段"""
        results = [make_result("李四")]
        stats = SensitiveStats(life_insured_count=1, life_insured_list=["李四"])
        output = export_to_json(results, stats)
        data = json.loads(output)
        assert data["details"][0]["insurance_category"] == "life"


class TestExportToExcel:
    def test_export_creates_workbook(self):
        results = [make_result("李四", "10000元")]
        stats = SensitiveStats(life_insured_count=1, life_insured_list=["李四"])
        data = export_to_excel(results, stats)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_export_multiple_rows(self):
        results = [make_result("李四"), make_result("张三")]
        stats = SensitiveStats(life_insured_count=2, life_insured_list=["张三", "李四"])
        data = export_to_excel(results, stats)
        assert isinstance(data, bytes)
        assert len(data) > 100

    def test_export_empty(self):
        data = export_to_excel([], SensitiveStats())
        assert isinstance(data, bytes)

    def test_has_two_sheets(self):
        from openpyxl import load_workbook
        import io
        results = [make_result("李四")]
        stats = SensitiveStats(life_insured_count=1, life_insured_list=["李四"])
        data = export_to_excel(results, stats)
        wb = load_workbook(io.BytesIO(data))
        assert "识别明细" in wb.sheetnames
        assert "敏感信息统计" in wb.sheetnames

    def test_insurance_category_column(self):
        """检查险种类型列存在且有值"""
        from openpyxl import load_workbook
        import io
        results = [make_result("李四")]
        stats = SensitiveStats(life_insured_count=1, life_insured_list=["李四"])
        data = export_to_excel(results, stats)
        wb = load_workbook(io.BytesIO(data))
        ws = wb["识别明细"]
        headers = [ws.cell(row=1, column=c).value for c in range(1, 16)]
        assert "险种类型" in headers
        # 数据行险种类型列应为人寿险
        type_col = headers.index("险种类型") + 1
        assert ws.cell(row=2, column=type_col).value == "人寿险"
