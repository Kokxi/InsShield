"""测试 PDF 转图片"""
import pytest
from pathlib import Path
from app.pdf_processor import is_pdf_file


class TestIsPdfFile:
    def test_pdf_extension(self):
        assert is_pdf_file(Path("test.pdf")) is True

    def test_pdf_uppercase(self):
        assert is_pdf_file(Path("test.PDF")) is True

    def test_jpg_not_pdf(self):
        assert is_pdf_file(Path("test.jpg")) is False

    def test_png_not_pdf(self):
        assert is_pdf_file(Path("test.png")) is False

    def test_no_ext(self):
        assert is_pdf_file(Path("test")) is False
