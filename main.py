"""FastAPI 应用入口"""
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.router import router
from app.logger import default_logger

logger = default_logger

app = FastAPI(title="保单敏感信息扫描工具")

static_dir = Path(__file__).parent / "static"
index_html = static_dir / "index.html"

# API 路由优先
app.include_router(router)

# 静态文件（CSS/JS），不包含 index.html
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def serve_index():
    """返回前端主页面"""
    if index_html.exists():
        return FileResponse(str(index_html))
    return {"message": "Frontend not built yet"}


@app.on_event("startup")
async def on_startup():
    logger.info("服务启动 — http://127.0.0.1:8000")


if __name__ == "__main__":
    logger.info("正在启动 uvicorn server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
