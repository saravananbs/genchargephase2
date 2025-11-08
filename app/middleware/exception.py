# app/middlewares/exception.py
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("api.exception")


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Log the full traceback
            logger.exception(
                f"UNHANDLED EXCEPTION | {request.method} {request.url} | {exc}"
            )
            # Return a clean JSON error to the client
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal Server Error",
                    "path": str(request.url),
                },
            )


def add_exception_middleware(app: FastAPI) -> None:
    """Attach global exception handler (must be added **last**)."""
    app.add_middleware(ExceptionHandlingMiddleware)