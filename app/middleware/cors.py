# app/middlewares/cors.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def add_cors_middleware(app: FastAPI) -> None:
    """
    Attach CORS (Cross-Origin Resource Sharing) middleware to FastAPI application.

    Configures cross-origin requests from browser-based clients. Currently allows all origins
    in development; should be restricted to specific frontend domains in production.

    Args:
        app (FastAPI): FastAPI application instance to attach middleware to.

    Returns:
        None
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production replace with your frontend domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )