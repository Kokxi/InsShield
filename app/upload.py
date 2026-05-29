"""上传文件处理：校验、保存、清理"""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR


def ensure_upload_dir():
    """确保上传目录存在"""
    Path(UPLOAD_DIR).mkdir(exist_ok=True)


def validate_file(filename: str, content_length: int) -> str:
    """校验文件扩展名和大小，返回小写扩展名"""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，支持 PDF/JPG/PNG")
    if content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"文件超过大小限制 {MAX_FILE_SIZE_MB}MB")
    return ext


async def save_upload(file: UploadFile) -> Path:
    """保存上传文件到临时目录，返回文件路径"""
    ensure_upload_dir()
    ext = validate_file(file.filename or "upload", file.size or 0)
    # 保留原始文件名，加UUID前缀防冲突
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    dest = Path(UPLOAD_DIR) / safe_name
    content = await file.read()
    dest.write_bytes(content)
    return dest


def cleanup_files():
    """清空上传目录"""
    import shutil
    if Path(UPLOAD_DIR).exists():
        shutil.rmtree(UPLOAD_DIR)
