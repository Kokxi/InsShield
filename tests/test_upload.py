"""测试上传模块"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from pathlib import Path
from app.upload import validate_file, save_upload, cleanup_files


class TestValidateFile:
    def test_valid_extensions(self):
        assert validate_file("test.pdf", 1000) == ".pdf"
        assert validate_file("test.jpg", 1000) == ".jpg"
        assert validate_file("test.jpeg", 1000) == ".jpeg"
        assert validate_file("test.png", 1000) == ".png"

    def test_invalid_extension(self):
        with pytest.raises(HTTPException) as exc:
            validate_file("test.exe", 1000)
        assert "不支持的文件格式" in str(exc.value.detail)

    def test_file_too_large(self):
        max_bytes = 50 * 1024 * 1024
        with pytest.raises(HTTPException) as exc:
            validate_file("test.pdf", max_bytes + 1)
        assert "超过大小限制" in str(exc.value.detail)


class TestSaveUpload:
    @pytest.mark.asyncio
    async def test_save_upload(self):
        mock_file = MagicMock()
        mock_file.filename = "保单.pdf"
        mock_file.size = 1000

        async def fake_read():
            return b"fake content"

        mock_file.read = fake_read

        path = await save_upload(mock_file)
        assert path.exists()
        assert "保单" in path.name
        path.unlink()
        # 清理父目录
        path.parent.rmdir()

    @pytest.mark.asyncio
    async def test_cleanup(self):
        mock_file = MagicMock()
        mock_file.filename = "test.pdf"
        mock_file.size = 100

        async def fake_read():
            return b"test"

        mock_file.read = fake_read

        path = await save_upload(mock_file)
        assert path.exists()
        cleanup_files()
        assert not Path("uploads").exists()
