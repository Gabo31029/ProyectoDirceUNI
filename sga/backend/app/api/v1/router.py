from fastapi import APIRouter

from app.api.v1 import auth, matricula, tenants, users, periodos, oferta

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(tenants.router)
api_router.include_router(users.router)
api_router.include_router(periodos.router)
api_router.include_router(oferta.router)
api_router.include_router(matricula.router)
api_router.include_router(matricula.inscripciones_router)
