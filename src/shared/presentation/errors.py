from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainValidationError(ValueError):
    """Raised when domain validation rules are violated."""


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainValidationError)
    async def handle_domain_validation_error(
        _: Request,
        exc: DomainValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                "code": "DOMAIN_VALIDATION_ERROR",
                "message": str(exc),
            },
        )
