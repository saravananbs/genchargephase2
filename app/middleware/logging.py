# app/middlewares/logging.py
import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Configure a dedicated logger
logger = logging.getLogger("api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"INCOMING | {request.method} {request.url} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"OUTGOING | {request.method} {request.url} | "
            f"Status: {response.status_code} | "
            f"Duration: {process_time:.2f}ms"
        )
        return response


def add_logging_middleware(app: FastAPI) -> None:
    """Attach the custom LoggingMiddleware."""
    app.add_middleware(LoggingMiddleware)