"""FastAPI app construction for Prisma."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import router


def create_app() -> FastAPI:
    """Create the Prisma FastAPI application."""

    app = FastAPI(title="Prisma", version="0.1.0")
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
