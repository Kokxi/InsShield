"""FastAPI 路由：上传 → 识别 → 响应"""
import io
import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.upload import save_upload, cleanup_files
from app.pdf_processor import pdf_to_images, is_pdf_file
from app.ocr_engine import OcrEngine
from app.page_classifier import is_policy_page
from app.field_extractor import extract_fields
from app.classifier import classify_insurance, classify_from_full_text
from app.statistics import compute_stats
from app.exporter import export_to_excel, export_to_json
from app.models import PolicyResult, UploadResponse

router = APIRouter()
ocr = OcrEngine()


@router.post("/api/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """上传一个或多个文件，识别后返回结果"""
    results: List[PolicyResult] = []

    for file in files:
        try:
            file_path = await save_upload(file)

            if is_pdf_file(file_path):
                images = pdf_to_images(file_path, max_pages=2)
            else:
                images = [file_path]

            # 扫描前2页（PDF）或唯一页（图片），任一页命中即视为保单
            ocr_results = []
            for page_image in images:
                page_results = ocr.recognize(page_image)
                ocr_results.extend(page_results)

            if not ocr_results:
                results.append(PolicyResult(
                    filename=file.filename or "unknown",
                    is_policy=False,
                    status="error",
                    error_message="OCR未识别到任何文字",
                ))
                continue

            is_policy = is_policy_page(ocr_results)
            if not is_policy:
                results.append(PolicyResult(
                    filename=file.filename or "unknown",
                    is_policy=False,
                    status="not_policy",
                ))
                continue

            fields = extract_fields(ocr_results)
            fields.insurance_category = classify_insurance(fields.policy_type)
            if fields.insurance_category == "unknown":
                full_text = "".join(r.text for r in ocr_results)
                fields.insurance_category = classify_from_full_text(full_text)
            policy_result = PolicyResult(
                filename=file.filename or "unknown",
                is_policy=True,
                fields=fields,
                status="ok",
            )
            results.append(policy_result)

        except Exception as e:
            results.append(PolicyResult(
                filename=file.filename or "unknown",
                is_policy=False,
                status="error",
                error_message=str(e),
            ))

    try:
        stats = compute_stats(results)
        return UploadResponse(results=results, stats=stats)
    finally:
        # 确保即使异常也会清理上传文件
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
