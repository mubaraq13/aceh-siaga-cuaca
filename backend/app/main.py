"""
FastAPI Main Application Entrypoint - ACEH SIAGA CUACA
File: backend/app/main.py
Jalankan server dengan: uvicorn backend.app.main:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router as api_v1_router
from backend.app.core.config import PROJECT_ROOT, settings

app = FastAPI(
    title=settings.app_name,
    description=settings.app_tagline,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)

# Sajikan grafik hasil EDA Phase 2 sebagai file statis di /static/figures
figures_dir: Path = PROJECT_ROOT / "data" / "processed" / "figures"
figures_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/figures", StaticFiles(directory=str(figures_dir)), name="figures")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": settings.app_name,
        "tagline": settings.app_tagline,
        "docs": "/api/docs",
        "health": "/api/v1/health",
    }
