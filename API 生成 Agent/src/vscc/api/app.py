"""FastAPI 应用工厂."""

from fastapi import FastAPI

from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="VSCC API Agent",
        description="智能 API 接口定义与测试生成 Agent",
        version="0.1.0",
    )
    app.include_router(router, prefix="/api/v1")
    return app
