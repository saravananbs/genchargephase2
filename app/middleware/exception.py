# app/middlewares/exception.py
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("api.exception")


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global exception handling middleware for capturing unhandled exceptions.

    Catches all exceptions not handled by route-specific handlers, logs full traceback,
    and returns standardized 500 JSON error response to client.
    """
    async def dispatch(self, request: Request, call_next):
        """
        Intercept request/response to catch and handle exceptions.

        Args:
            request (Request): HTTP request object.
            call_next (Callable): Dependency to process request.

        Returns:
            Response: HTTP response or 500 error JSON.
        """
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
    """
    Attach global exception handling middleware to FastAPI application.

    Must be added last in middleware stack for proper error handling priority.

    Args:
        app (FastAPI): FastAPI application instance.

    Returns:
        None
    """
    app.add_middleware(ExceptionHandlingMiddleware)