from uuid import UUID
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.dependencies import CurrentUser, require_roles, resolve_tenant_id
from app.models.schemas import (
    PlanEstudiosCreate,
    PlanEstudiosResponse,
    CursoCreate,
    CursoResponse,
    CursoAsociarPlan,
    PrerrequisitoCreate,
    PrerrequisitoResponse,
    SeccionCreate,
    SeccionResponse,
    AsignacionDocenteCreate,
    AsignacionDocenteResponse,
    ComponenteEvaluacionCreate,
    ComponenteEvaluacionResponse,
)
from app.services.oferta_service import OfertaService

router = APIRouter(prefix="/oferta", tags=["Oferta Académica"])


def _oferta_service() -> OfertaService:
    return OfertaService(db.connection())


# --- Planes de Estudio ---
@router.post("/planes-estudio", response_model=PlanEstudiosResponse, status_code=201)
async def crear_plan_estudios(
    payload: PlanEstudiosCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> PlanEstudiosResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().crear_plan_estudios(tenant_id, payload, actor_id=current_user.id)


@router.get("/planes-estudio", response_model=list[PlanEstudiosResponse])
async def listar_planes_estudio(
    current_user: CurrentUser = Depends(require_roles("ADMIN", "DOCENTE", "ALUMNO")),
) -> list[PlanEstudiosResponse]:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().list_planes(tenant_id)


@router.put("/planes-estudio/{plan_id}/activar", response_model=PlanEstudiosResponse)
async def activar_plan_estudios(
    plan_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> PlanEstudiosResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().activar_plan_estudios(tenant_id, plan_id, actor_id=current_user.id)


# --- Cursos ---
@router.post("/cursos", response_model=CursoResponse, status_code=201)
async def crear_curso(
    payload: CursoCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> CursoResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().crear_curso(tenant_id, payload, actor_id=current_user.id)


@router.get("/cursos", response_model=list[CursoResponse])
async def listar_cursos(
    current_user: CurrentUser = Depends(require_roles("ADMIN", "DOCENTE", "ALUMNO")),
) -> list[CursoResponse]:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().list_cursos(tenant_id)


@router.post("/planes-estudio/{plan_id}/cursos", status_code=201)
async def asociar_curso_a_plan(
    plan_id: UUID,
    payload: CursoAsociarPlan,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().asociar_curso_a_plan(
        tenant_id, plan_id, payload, actor_id=current_user.id
    )


@router.get("/planes-estudio/{plan_id}/cursos")
async def listar_cursos_plan(
    plan_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "DOCENTE", "ALUMNO")),
) -> list[dict]:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().list_cursos_plan(tenant_id, plan_id)


@router.delete("/planes-estudio/{plan_id}/cursos/{curso_id}", status_code=204)
async def desasociar_curso_de_plan(
    plan_id: UUID,
    curso_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> None:
    tenant_id = resolve_tenant_id(current_user)
    await _oferta_service().desasociar_curso_de_plan(
        tenant_id, plan_id, curso_id, actor_id=current_user.id
    )


@router.post("/cursos/{curso_id}/prerrequisitos", response_model=PrerrequisitoResponse, status_code=201)
async def configurar_prerrequisito(
    curso_id: UUID,
    payload: PrerrequisitoCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> PrerrequisitoResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().configurar_prerrequisitos(
        tenant_id, curso_id, payload, actor_id=current_user.id
    )


# --- Secciones ---
@router.post("/secciones", response_model=SeccionResponse, status_code=201)
async def crear_seccion(
    payload: SeccionCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> SeccionResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().crear_seccion(tenant_id, payload, actor_id=current_user.id)


@router.get("/periodos/{periodo_id}/secciones")
async def listar_secciones_por_periodo(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "DOCENTE", "ALUMNO")),
) -> list[dict]:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().list_secciones(tenant_id, periodo_id)


# --- Asignaciones Docente ---
@router.post("/secciones/{seccion_id}/docentes", response_model=AsignacionDocenteResponse, status_code=201)
async def asignar_docente_a_seccion(
    seccion_id: UUID,
    payload: AsignacionDocenteCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> AsignacionDocenteResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().asignar_docente(
        tenant_id, seccion_id, payload, actor_id=current_user.id
    )


# --- Componentes Evaluacion ---
@router.post("/secciones/{seccion_id}/componentes", response_model=ComponenteEvaluacionResponse, status_code=201)
async def crear_componente_evaluacion(
    seccion_id: UUID,
    payload: ComponenteEvaluacionCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> ComponenteEvaluacionResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().crear_componente_evaluacion(
        tenant_id, seccion_id, payload, actor_id=current_user.id
    )


@router.get("/secciones/{seccion_id}/componentes", response_model=list[ComponenteEvaluacionResponse])
async def listar_componentes_evaluacion(
    seccion_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "DOCENTE", "ALUMNO")),
) -> list[ComponenteEvaluacionResponse]:
    tenant_id = resolve_tenant_id(current_user)
    return await _oferta_service().list_componentes(tenant_id, seccion_id)
