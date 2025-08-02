"""FastAPI entrypoint"""
"""Marketplace Submission + Catalog API"""

from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="Retail Marketplace",
    version="1.0.0",
    description="Handles seller submissions and approved product responses"
)

app.include_router(router, prefix="/v1")
