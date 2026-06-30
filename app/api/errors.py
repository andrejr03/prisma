"""Structured API error mapping."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.generation.service import CitationValidationError, InvalidQueryError, NoContextError
from app.models.rag import ErrorBody, ErrorResponse
from app.providers.generation import UnsupportedGenerationBackendError
from app.retrieval.search import IndexNotReadyError


def register_exception_handlers(app: FastAPI) -> None:
    """Register structured JSON exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            status_code=422,
            code="validation_error",
            message="Request validation failed.",
            details={"errors": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(InvalidQueryError)
    async def invalid_query_exception_handler(
        _request: Request,
        exc: InvalidQueryError,
    ) -> JSONResponse:
        return error_response(
            status_code=422,
            code="invalid_request",
            message=str(exc),
            details=exc.details,
        )

    @app.exception_handler(IndexNotReadyError)
    async def index_not_ready_exception_handler(
        _request: Request,
        _exc: IndexNotReadyError,
    ) -> JSONResponse:
        return error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="index_not_ready",
            message="Local index is missing. Run python -m app.retrieval.index.",
        )

    @app.exception_handler(NoContextError)
    async def no_context_exception_handler(
        _request: Request,
        exc: NoContextError,
    ) -> JSONResponse:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="no_context",
            message=str(exc),
        )

    @app.exception_handler(UnsupportedGenerationBackendError)
    async def unsupported_generation_backend_exception_handler(
        _request: Request,
        exc: UnsupportedGenerationBackendError,
    ) -> JSONResponse:
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="unsupported_generation_backend",
            message=str(exc),
        )

    @app.exception_handler(CitationValidationError)
    async def citation_validation_exception_handler(
        _request: Request,
        exc: CitationValidationError,
    ) -> JSONResponse:
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="invalid_citations",
            message=str(exc),
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            message="Unexpected application failure.",
        )


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build a structured JSON error response."""

    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or {},
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())
