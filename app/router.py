"""FastAPI 路由：上传 → 识别 → 响应"""
import io
import re
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse

from app.upload import save_upload, cleanup_files
from app.pdf_processor import pdf_to_images, is_pdf_file, extract_text_from_pdf
from app.word_processor import is_word_file, extract_text_from_docx, extract_text_from_doc
from app.ocr_engine import OcrEngine
from app.doc_classifier import classify_doc_type, get_doc_type_display
from app.pii_extractor import extract_pii_from_text, extract_persons, group_pii_to_persons
from app.classifier import classify_from_full_text, get_category_display_name, get_insurance_branch, get_branch_display, check_anomaly
from app.statistics import compute_global_stats
from app.exporter import export_to_excel, export_to_json
from app.models import FileResult, UploadResponse, PersonModel, PIIItemModel
from app.config import INSURANCE_COMPANIES

router = APIRouter()
ocr = OcrEngine()

ROLE_DISPLAY = {
    "applicant": "投保人",
    "insured": "被保人",
    "beneficiary": "受益人",
    "reporter": "报案人",
    "anonymous": "未关联",
}


@router.post("/api/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """上传一个或多个文件，识别后返回结果"""
    results: List[FileResult] = []

    for file in files:
        try:
            file_path = await save_upload(file)
            filename = file.filename or "unknown"

            # 1. 提取文本
            if is_word_file(file_path):
                if file_path.suffix.lower() == ".docx":
                    text = extract_text_from_docx(file_path)
                else:
                    text = extract_text_from_doc(file_path)
                raw_text = text
            elif is_pdf_file(file_path):
                # 尝试文本型 PDF
                text = extract_text_from_pdf(file_path)
                if not text.strip():
                    # 扫描型 PDF，走 OCR
                    images = pdf_to_images(file_path, max_pages=2)
                    ocr_results = []
                    for img in images:
                        ocr_results.extend(ocr.recognize(img))
                    text = "\n".join(r.text for r in ocr_results)
                raw_text = text
            else:
                # 图片，走 OCR
                ocr_results = ocr.recognize(file_path)
                text = "\n".join(r.text for r in ocr_results)
                raw_text = text

            # 2. 文档类型分类
            doc_type, is_insurance = classify_doc_type(text, filename)

            if not is_insurance:
                results.append(FileResult(
                    filename=filename,
                    is_insurance_related=False,
                    status="not_insurance",
                    raw_text=raw_text,
                ))
                continue

            # 3. 险种识别（从文件名和全文推断）
            insurance_category = "unknown"
            # 从文件名推断
            for cat, keywords in [("life", ["寿险", "年金"]), ("health", ["重疾", "医疗", "健康"]),
                                   ("accident", ["意外", "驾意"]), ("car", ["车险", "交强", "车损"]),
                                   ("property", ["财产", "责任"])]:
                if any(kw in filename for kw in keywords):
                    insurance_category = cat
                    break

            # 从全文推断
            if insurance_category == "unknown":
                insurance_category = classify_from_full_text(text)

            # 4. 提取保险公司
            insurance_company = ""
            for company in INSURANCE_COMPANIES:
                if company in text:
                    insurance_company = company
                    break

            # 5. 提取保单号（如有）
            policy_number = ""
            for line in text.split('\n'):
                if "保单号" in line or "保单号码" in line:
                    match = re.search(r'\b[A-Za-z0-9]{10,20}\b', line)
                    if match:
                        policy_number = match.group()
                    break

            # 6. PII 提取
            pii_items = extract_pii_from_text(text)
            persons = extract_persons(text)
            persons = group_pii_to_persons(persons, pii_items, text)

            # 转换为 Model
            person_models = []
            for p in persons:
                person_models.append(PersonModel(
                    name=p.name,
                    role=p.role,
                    role_display=ROLE_DISPLAY.get(p.role, "未知"),
                    details=[PIIItemModel(type=d.type, value=d.value, raw_label=d.raw_label) for d in p.details],
                ))

            # 7. 判断状态
            if not person_models:
                status = "no_pii"
            else:
                status = "ok"

            results.append(FileResult(
                filename=filename,
                is_insurance_related=True,
                document_type=doc_type,
                document_type_display=get_doc_type_display(doc_type),
                insurance_category=insurance_category,
                insurance_category_display=get_category_display_name(insurance_category),
                insurance_branch=get_insurance_branch(insurance_category),
                insurance_branch_display=get_branch_display(get_insurance_branch(insurance_category)),
                anomaly=check_anomaly(get_insurance_branch(insurance_category), person_models),
                insurance_company=insurance_company,
                policy_number=policy_number,
                persons=person_models,
                sensitive_count=len(person_models),
                status=status,
                raw_text=raw_text,
            ))

        except Exception as e:
            results.append(FileResult(
                filename=file.filename or "unknown",
                status="error",
                error_message=str(e),
            ))

    try:
        stats = compute_global_stats(results)
        return UploadResponse(results=results, stats=stats)
    finally:
        cleanup_files()


@router.post("/api/export/excel")
async def export_excel(data: UploadResponse):
    """接收识别结果并导出为Excel"""
    excel_bytes = export_to_excel(data.results, data.stats)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=policy_export.xlsx"},
    )


@router.post("/api/export/json")
async def export_json(data: UploadResponse):
    """接收识别结果并导出为JSON"""
    json_str = export_to_json(data.results, data.stats)
    return StreamingResponse(
        io.BytesIO(json_str.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=policy_export.json"},
    )
