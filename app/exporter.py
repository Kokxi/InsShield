"""导出模块：支持 Excel 和 JSON 格式"""
import json
import io
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from app.models import PolicyResult, SensitiveStats


def export_to_excel(results: List[PolicyResult], stats: SensitiveStats) -> bytes:
    """生成Excel文件内容（内存），返回bytes"""
    wb = Workbook()

    # === Sheet 1: 明细 ===
    ws1 = wb.active
    ws1.title = "识别明细"
    headers = ["文件名", "状态", "保险公司", "险种", "保单号", "投保人",
               "被保人", "受益人", "保费", "交费方式", "生效日期",
               "保险期间", "销售经理", "错误信息"]
    # 表头样式
    header_font = Font(bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row_idx, r in enumerate(results, 2):
        ws1.cell(row=row_idx, column=1, value=r.filename)
        ws1.cell(row=row_idx, column=2, value=r.status)
        ws1.cell(row=row_idx, column=3, value=r.fields.insurance_company or "")
        ws1.cell(row=row_idx, column=4, value=r.fields.policy_type or "")
        ws1.cell(row=row_idx, column=5, value=r.fields.policy_number or "")
        ws1.cell(row=row_idx, column=6, value=r.fields.applicant or "")
        ws1.cell(row=row_idx, column=7, value=r.fields.insured or "")
        ws1.cell(row=row_idx, column=8, value=r.fields.beneficiary or "")
        ws1.cell(row=row_idx, column=9, value=r.fields.premium or "")
        ws1.cell(row=row_idx, column=10, value=r.fields.payment_method or "")
        ws1.cell(row=row_idx, column=11, value=r.fields.effective_date or "")
        ws1.cell(row=row_idx, column=12, value=r.fields.insurance_period or "")
        ws1.cell(row=row_idx, column=13, value=r.fields.sales_manager or "")
        ws1.cell(row=row_idx, column=14, value=r.error_message or "")

    # === Sheet 2: 统计 ===
    ws2 = wb.create_sheet("敏感信息统计")
    ws2.cell(row=1, column=1, value="去重后被保人数量").font = header_font
    ws2.cell(row=1, column=2, value=stats.total_unique_insured)
    ws2.cell(row=2, column=1, value="被保人列表").font = header_font
    ws2.cell(row=2, column=2, value="、".join(stats.insured_list))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def export_to_json(results: List[PolicyResult], stats: SensitiveStats) -> str:
    """生成JSON字符串（用于下载）"""
    data = {
        "sensitive_stats": {
            "total_unique_insured": stats.total_unique_insured,
            "insured_list": stats.insured_list,
        },
        "details": [
            {
                "filename": r.filename,
                "status": r.status,
                "fields": {
                    "insurance_company": r.fields.insurance_company,
                    "policy_type": r.fields.policy_type,
                    "policy_number": r.fields.policy_number,
                    "applicant": r.fields.applicant,
                    "insured": r.fields.insured,
                    "beneficiary": r.fields.beneficiary,
                    "premium": r.fields.premium,
                    "payment_method": r.fields.payment_method,
                    "effective_date": r.fields.effective_date,
                    "insurance_period": r.fields.insurance_period,
                    "sales_manager": r.fields.sales_manager,
                },
                "error_message": r.error_message,
            }
            for r in results
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
