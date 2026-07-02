from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import lifespan
from app.core.exceptions import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

settings = get_settings()

app = FastAPI(
    title="SGA — Sistema de Gestion Academica",
    description=(
        "API SGA: Auth/Tenant/Usuarios, Periodos/Oferta, Matricula "
        "(Grupo 4 — Dirce)"
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    status_map = {
        ValidationError: 400,
        UnauthorizedError: 401,
        ForbiddenError: 403,
        NotFoundError: 404,
        ConflictError: 409,
    }
    status_code = status_map.get(type(exc), 400)
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


# Import all models so that Base.metadata registers all tables
from app.models import core_schemas, calificacion, cierre, seguimiento   # noqa: F401

from app.api.calificaciones import router as calificaciones_router
from app.api.cierre import router as cierre_router
from app.api.historial import router as historial_router

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(calificaciones_router, prefix="/api/v1")
app.include_router(cierre_router, prefix="/api/v1")
app.include_router(historial_router, prefix="/api/v1")
app.include_router(api_router)
