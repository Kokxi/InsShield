"""测试API路由"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_upload_no_files():
    """缺少files参数应返回422"""
    resp = client.post("/api/upload")
    assert resp.status_code == 422


def test_swagger_docs_accessible():
    """Swagger文档可访问"""
    resp = client.get("/docs")
    assert resp.status_code == 200
