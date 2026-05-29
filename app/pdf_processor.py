"""PDF 转图片模块"""
from pathlib import Path
from typing import List
import fitz  # PyMuPDF


def pdf_to_images(pdf_path: Path, dpi: int = 200, max_pages: int = 2) -> List[Path]:
    """将PDF每页转为JPEG图片，返回图片路径列表。max_pages 限制最多转换页数"""
    doc = fitz.open(pdf_path)
    images = []
    page_count = min(len(doc), max_pages)
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        image_path = pdf_path.parent / f"{pdf_path.stem}_p{page_num + 1}.jpg"
        pix.save(str(image_path))
        images.append(image_path)
    doc.close()
    return images


def is_pdf_file(file_path: Path) -> bool:
    """判断是否为PDF文件"""
    return file_path.suffix.lower() == ".pdf"
