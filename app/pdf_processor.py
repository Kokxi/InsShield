"""PDF 转图片模块"""
import logging
from pathlib import Path
from typing import List
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def pdf_to_images(pdf_path: Path, dpi: int = 200, max_pages: int = 2) -> List[Path]:
    """将PDF每页转为JPEG图片，返回图片路径列表。max_pages 限制最多转换页数"""
    doc = fitz.open(pdf_path)
    images = []
    page_count = min(len(doc), max_pages)
    logger.info("pdf_to_images: file=%s total_pages=%d max_pages=%d", pdf_path.name, len(doc), max_pages)
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        image_path = pdf_path.parent / f"{pdf_path.stem}_p{page_num + 1}.jpg"
        pix.save(str(image_path))
        logger.debug("pdf_to_images: saved page %d to %s", page_num + 1, image_path.name)
        images.append(image_path)
    doc.close()
    return images


def is_pdf_file(file_path: Path) -> bool:
    """判断是否为PDF文件"""
    return file_path.suffix.lower() == ".pdf"


def extract_text_from_pdf(file_path: Path, max_pages: int = 2) -> str:
    """尝试从文本型 PDF 直接提取文字层（不走 OCR），扫描型 PDF 返回空字符串"""
    doc = fitz.open(file_path)
    texts = []
    page_count = min(len(doc), max_pages)
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            texts.append(text)
    doc.close()
    result = '\n'.join(texts)
    logger.info("extract_text_from_pdf: file=%s page_count=%d total_chars=%d", file_path.name, page_count, len(result))
    return result
