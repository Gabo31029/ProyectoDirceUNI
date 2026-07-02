from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import engine
from app.models.base import Base

# Import all models so that Base.metadata registers all tables
import app.models.core_schemas   # noqa: F401
import app.models.calificacion    # noqa: F401
import app.models.cierre          # noqa: F401
import app.models.seguimiento     # noqa: F401

from app.api.calificaciones import router as calificaciones_router
from app.api.cierre import router as cierre_router
from app.api.historial import router as historial_router
from app.api.v1.router import api_router
from app.core.database import lifespan

app = FastAPI(
    title="SGA – Sistema de Gestión Académica",
    description=(
        "API REST del ciclo de vida académico: "
        "Gestión de Calificaciones, Cierre Académico e Historial Académico."
    ),
    version="1.0.0",
    contact={"name": "Grupo 4 – SW505 2026-1"},
    lifespan=lifespan
)

import os

# Read allowed origins from environment (comma-separated), default to "*" if not specified
origins_str = os.getenv("ALLOWED_ORIGINS", "*")
if origins_str == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup event: create all DB tables ───────────────────────────────────────
@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(calificaciones_router, prefix="/api/v1")
app.include_router(cierre_router, prefix="/api/v1")
app.include_router(historial_router, prefix="/api/v1")
app.include_router(api_router)

# ── Health-check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check() -> dict:
    return {
        "status": "online",
        "service": "SGA – Academic Lifecycle API",
        "docs": "/docs",
        "redoc": "/redoc"
    }
