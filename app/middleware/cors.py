# app/middlewares/cors.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def add_cors_middleware(app: FastAPI) -> None:
    """
    Attach CORS middleware.
    Adjust origins, methods, headers to your needs.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production replace with your frontend domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )