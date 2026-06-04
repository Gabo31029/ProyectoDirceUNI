import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, date, UTC
from decimal import Decimal

from app.core.exceptions import ConflictError, NotFoundError, ValidationError, UnauthorizedError, ForbiddenError
from app.models.schemas import (
    LoginRequest, RolUsuario, PeriodoAcademicoCreate, PeriodoEstado,
    PlanEstudiosCreate, CursoCreate, SeccionCreate, ComponenteEvaluacionCreate
)
from app.services.auth_service import AuthService
from app.services.periodo_service import PeriodoService
from app.services.oferta_service import OfertaService

# Helper fixtures for mocks
@pytest.fixture
def mock_pool():
    pool = MagicMock()
    mock_conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = mock_conn
    return pool

# ─────────────────────────────────────────────────────────────────────────────
# AUTH SERVICE TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_login_success(mock_pool) -> None:
    service = AuthService(mock_pool)
    service.auth_repo = AsyncMock()
    service.audit_repo = AsyncMock()

    tenant_id = uuid4()
    user_id = uuid4()
    service.auth_repo.get_tenant_by_dominio.return_value = {"id": tenant_id}
    service.auth_repo.get_login_attempts.return_value = None
    service.auth_repo.get_user_for_login.return_value = {
        "id": user_id,
        "id_tenant": tenant_id,
        "email": "user@uni-demo.local",
        "rol": "ADMIN",
        "password_hash": "hashed_password"
    }

    payload = LoginRequest(
        email="user@uni-demo.local",
        password="ValidPassword123!",
        dominio_tenant="uni-demo"
    )

    with patch("app.services.auth_service.verify_password", return_value=True), \
         patch("app.services.auth_service.create_access_token", return_value=("fake_jwt_token", None, 3600)):
        
        response = await service.login(payload)
        
        assert response.access_token == "fake_jwt_token"
        assert response.rol == RolUsuario.ADMIN
        assert response.tenant_id == str(tenant_id)
        service.auth_repo.reset_login_attempts.assert_called_once_with(email="user@uni-demo.local", tenant_id=tenant_id)
        service.audit_repo.registrar.assert_called_once()

@pytest.mark.asyncio
async def test_auth_login_invalid_password(mock_pool) -> None:
    service = AuthService(mock_pool)
    service.auth_repo = AsyncMock()
    service.audit_repo = AsyncMock()

    tenant_id = uuid4()
    user_id = uuid4()
    service.auth_repo.get_tenant_by_dominio.return_value = {"id": tenant_id}
    service.auth_repo.get_login_attempts.return_value = None
    service.auth_repo.get_user_for_login.return_value = {
        "id": user_id,
        "id_tenant": tenant_id,
        "email": "user@uni-demo.local",
        "rol": "ADMIN",
        "password_hash": "hashed_password"
    }

    payload = LoginRequest(
        email="user@uni-demo.local",
        password="WrongPassword123!",
        dominio_tenant="uni-demo"
    )

    with patch("app.services.auth_service.verify_password", return_value=False), \
         patch.object(service, "_registrar_intento_fallido", new_callable=AsyncMock) as mock_registrar_fallido:
        
        with pytest.raises(UnauthorizedError, match="Credenciales invalidas."):
            await service.login(payload)
        
        mock_registrar_fallido.assert_called_once_with("user@uni-demo.local", tenant_id, user_id)

@pytest.mark.asyncio
async def test_auth_login_lockout(mock_pool) -> None:
    service = AuthService(mock_pool)
    service.auth_repo = AsyncMock()
    service.audit_repo = AsyncMock()

    tenant_id = uuid4()
    service.auth_repo.get_tenant_by_dominio.return_value = {"id": tenant_id}
    # Lockout in the future
    future_time = datetime(3000, 1, 1, tzinfo=UTC)
    service.auth_repo.get_login_attempts.return_value = {
        "intentos_fallidos": 5,
        "bloqueado_hasta": future_time
    }

    payload = LoginRequest(
        email="user@uni-demo.local",
        password="ValidPassword123!",
        dominio_tenant="uni-demo"
    )

    with pytest.raises(ForbiddenError, match="Cuenta bloqueada temporalmente."):
        await service.login(payload)

@pytest.mark.asyncio
async def test_auth_logout(mock_pool) -> None:
    service = AuthService(mock_pool)
    service.auth_repo = AsyncMock()
    service.audit_repo = AsyncMock()

    user_id = uuid4()
    jti = uuid4()
    exp = int(datetime.now(UTC).timestamp()) + 3600

    await service.logout(user_id=user_id, tenant_id=None, jti=jti, exp=exp)

    service.auth_repo.blacklist_token.assert_called_once()
    service.audit_repo.registrar.assert_called_once()

@pytest.mark.asyncio
async def test_auth_get_me_success(mock_pool) -> None:
    service = AuthService(mock_pool)
    service.auth_repo = AsyncMock()

    user_id = uuid4()
    tenant_id = uuid4()
    service.auth_repo.get_user_by_id.return_value = {
        "id": user_id,
        "email": "me@uni-demo.local",
        "nombre": "John",
        "apellido": "Doe",
        "rol": "ALUMNO",
        "id_tenant": tenant_id,
        "activo": True
    }

    user_public = await service.get_me(user_id)

    assert user_public.id == str(user_id)
    assert user_public.email == "me@uni-demo.local"
    assert user_public.rol == RolUsuario.ALUMNO
    assert user_public.tenant_id == str(tenant_id)
    assert user_public.activo is True

@pytest.mark.asyncio
async def test_auth_get_me_not_found(mock_pool) -> None:
    service = AuthService(mock_pool)
    service.auth_repo = AsyncMock()
    service.auth_repo.get_user_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Usuario no encontrado."):
        await service.get_me(uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# PERIODO SERVICE TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_periodo_crear_success(mock_pool) -> None:
    service = PeriodoService(mock_pool)
    service.repo = AsyncMock()
    service.audit_repo = AsyncMock()

    tenant_id = uuid4()
    actor_id = uuid4()
    periodo_id = uuid4()

    payload = PeriodoAcademicoCreate(
        nombre_periodo="2026-I",
        fecha_inicio=date(2026, 3, 15),
        fecha_fin=date(2026, 7, 20)
    )

    service.repo.list_by_tenant.return_value = []
    service.repo.create.return_value = {
        "id": periodo_id,
        "id_tenant": tenant_id,
        "nombre_periodo": "2026-I",
        "fecha_inicio": date(2026, 3, 15),
        "fecha_fin": date(2026, 7, 20),
        "estado": "CONFIGURACION",
        "fecha_estado_actual": datetime.now(UTC),
        "id_usuario_transicion": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    res = await service.crear_periodo(tenant_id, payload, actor_id=actor_id)

    assert res.nombre_periodo == "2026-I"
    assert res.estado == "CONFIGURACION"
    service.repo.create.assert_called_once_with(
        id_tenant=tenant_id,
        nombre_periodo="2026-I",
        fecha_inicio=date(2026, 3, 15),
        fecha_fin=date(2026, 7, 20)
    )
    service.audit_repo.registrar.assert_called_once()

@pytest.mark.asyncio
async def test_periodo_crear_invalid_dates(mock_pool) -> None:
    service = PeriodoService(mock_pool)

    payload = PeriodoAcademicoCreate(
        nombre_periodo="2026-I",
        fecha_inicio=date(2026, 7, 20),
        fecha_fin=date(2026, 3, 15)  # End before start
    )

    with pytest.raises(ValidationError, match="La fecha de inicio debe ser anterior"):
        await service.crear_periodo(uuid4(), payload, actor_id=uuid4())

@pytest.mark.asyncio
async def test_periodo_crear_conflict_name(mock_pool) -> None:
    service = PeriodoService(mock_pool)
    service.repo = AsyncMock()

    tenant_id = uuid4()
    payload = PeriodoAcademicoCreate(
        nombre_periodo="2026-I",
        fecha_inicio=date(2026, 3, 15),
        fecha_fin=date(2026, 7, 20)
    )

    service.repo.list_by_tenant.return_value = [
        {"nombre_periodo": "2026-I"}
    ]

    with pytest.raises(ConflictError, match="Ya existe un periodo con este nombre"):
        await service.crear_periodo(tenant_id, payload, actor_id=uuid4())

@pytest.mark.asyncio
async def test_periodo_transicionar_success(mock_pool) -> None:
    service = PeriodoService(mock_pool)
    service.repo = AsyncMock()
    service.audit_repo = AsyncMock()

    tenant_id = uuid4()
    periodo_id = uuid4()
    actor_id = uuid4()

    service.repo.get_by_id.return_value = {
        "id": periodo_id,
        "estado": "CONFIGURACION"
    }
    service.repo.get_activo_by_tenant.return_value = None
    service.repo.update_estado.return_value = {
        "id": periodo_id,
        "id_tenant": tenant_id,
        "nombre_periodo": "2026-I",
        "fecha_inicio": date(2026, 3, 15),
        "fecha_fin": date(2026, 7, 20),
        "estado": "MATRICULA",
        "fecha_estado_actual": datetime.now(UTC),
        "id_usuario_transicion": actor_id,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    res = await service.transicionar_periodo(tenant_id, periodo_id, PeriodoEstado.MATRICULA, actor_id=actor_id)

    assert res.estado == "MATRICULA"
    service.repo.update_estado.assert_called_once_with(periodo_id, tenant_id, "MATRICULA", actor_id)

@pytest.mark.asyncio
async def test_periodo_transicionar_conflict_active(mock_pool) -> None:
    service = PeriodoService(mock_pool)
    service.repo = AsyncMock()

    tenant_id = uuid4()
    periodo_id = uuid4()
    otro_periodo_id = uuid4()

    service.repo.get_by_id.return_value = {
        "id": periodo_id,
        "estado": "CONFIGURACION"
    }
    service.repo.get_activo_by_tenant.return_value = {
        "id": otro_periodo_id,
        "estado": "MATRICULA"
    }

    with pytest.raises(ConflictError, match="Ya existe un periodo activo"):
        await service.transicionar_periodo(tenant_id, periodo_id, PeriodoEstado.MATRICULA, actor_id=uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# OFERTA SERVICE TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_oferta_crear_plan_estudios_success(mock_pool) -> None:
    service = OfertaService(mock_pool)
    service.repo = AsyncMock()
    service.audit_repo = AsyncMock()

    tenant_id = uuid4()
    plan_id = uuid4()
    actor_id = uuid4()

    payload = PlanEstudiosCreate(
        carrera="Ingenieria de Sistemas",
        version_plan="2026",
        creditos_totales=200
    )

    service.repo.list_planes_estudio.return_value = []
    service.repo.create_plan_estudios.return_value = {
        "id": plan_id,
        "id_tenant": tenant_id,
        "carrera": "Ingenieria de Sistemas",
        "version_plan": "2026",
        "creditos_totales": 200,
        "estado": "BORRADOR",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    res = await service.crear_plan_estudios(tenant_id, payload, actor_id=actor_id)

    assert res.carrera == "Ingenieria de Sistemas"
    assert res.version_plan == "2026"
    assert res.estado == "BORRADOR"

@pytest.mark.asyncio
async def test_oferta_crear_plan_estudios_duplicate(mock_pool) -> None:
    service = OfertaService(mock_pool)
    service.repo = AsyncMock()

    tenant_id = uuid4()
    payload = PlanEstudiosCreate(
        carrera="Ingenieria de Sistemas",
        version_plan="2026",
        creditos_totales=200
    )

    service.repo.list_planes_estudio.return_value = [
        {"carrera": "Ingenieria de Sistemas", "version_plan": "2026"}
    ]

    with pytest.raises(ConflictError, match="Ya existe una version de este plan"):
        await service.crear_plan_estudios(tenant_id, payload, actor_id=uuid4())

@pytest.mark.asyncio
async def test_oferta_crear_curso_success(mock_pool) -> None:
    service = OfertaService(mock_pool)
    service.repo = AsyncMock()
    service.audit_repo = AsyncMock()

    tenant_id = uuid4()
    curso_id = uuid4()
    actor_id = uuid4()

    payload = CursoCreate(
        codigo_curso="SYS101",
        nombre_curso="Introduccion a Sistemas",
        creditos=4,
        tipo_curso="OBLIGATORIO",
        ciclo_sugerido=1
    )

    service.repo.get_curso_by_codigo.return_value = None
    service.repo.create_curso.return_value = {
        "id": curso_id,
        "id_tenant": tenant_id,
        "codigo_curso": "SYS101",
        "nombre_curso": "Introduccion a Sistemas",
        "creditos": 4,
        "tipo_curso": "OBLIGATORIO",
        "ciclo_sugerido": 1,
        "activo": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    res = await service.crear_curso(tenant_id, payload, actor_id=actor_id)

    assert res.codigo_curso == "SYS101"
    assert res.nombre_curso == "Introduccion a Sistemas"

@pytest.mark.asyncio
async def test_oferta_crear_seccion_success(mock_pool) -> None:
    service = OfertaService(mock_pool)
    service.repo = AsyncMock()
    service.periodo_repo = AsyncMock()
    service.audit_repo = AsyncMock()

    tenant_id = uuid4()
    periodo_id = uuid4()
    curso_id = uuid4()
    seccion_id = uuid4()
    actor_id = uuid4()

    payload = SeccionCreate(
        id_periodo=periodo_id,
        id_curso=curso_id,
        codigo_seccion="A",
        vacantes_maximas=40
    )

    service.periodo_repo.get_by_id.return_value = {
        "id": periodo_id,
        "estado": "CONFIGURACION"
    }
    service.repo.get_curso_by_id.return_value = {
        "id": curso_id
    }
    service.repo.get_seccion_by_codigo.return_value = None
    service.repo.create_seccion.return_value = {
        "id": seccion_id,
        "id_tenant": tenant_id,
        "id_periodo": periodo_id,
        "id_curso": curso_id,
        "codigo_seccion": "A",
        "vacantes_maximas": 40,
        "vacantes_disponibles": 40,
        "estado": "ABIERTA",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    res = await service.crear_seccion(tenant_id, payload, actor_id=actor_id)

    assert res.codigo_seccion == "A"
    assert res.vacantes_maximas == 40

@pytest.mark.asyncio
async def test_oferta_crear_seccion_invalid_period_state(mock_pool) -> None:
    service = OfertaService(mock_pool)
    service.repo = AsyncMock()
    service.periodo_repo = AsyncMock()

    tenant_id = uuid4()
    periodo_id = uuid4()
    curso_id = uuid4()

    payload = SeccionCreate(
        id_periodo=periodo_id,
        id_curso=curso_id,
        codigo_seccion="A",
        vacantes_maximas=40
    )

    service.periodo_repo.get_by_id.return_value = {
        "id": periodo_id,
        "estado": "MATRICULA"  # Cannot create sections in MATRICULA state
    }

    with pytest.raises(ValidationError, match="No se pueden crear ni modificar secciones"):
        await service.crear_seccion(tenant_id, payload, actor_id=uuid4())

@pytest.mark.asyncio
async def test_oferta_crear_componente_evaluacion_success(mock_pool) -> None:
    service = OfertaService(mock_pool)
    service.repo = AsyncMock()

    tenant_id = uuid4()
    seccion_id = uuid4()
    escala_id = uuid4()
    componente_id = uuid4()

    payload = ComponenteEvaluacionCreate(
        id_tipo_componente=uuid4(),
        id_escala=escala_id,
        peso_relativo=Decimal("30.00"),
        orden_presentacion=1
    )

    service.repo.get_by_id.return_value = {"id": seccion_id}
    service.repo.get_escala_by_id_and_tenant.return_value = {"id": escala_id}
    # Existing components sum to 60.00
    service.repo.list_componentes_by_seccion.return_value = [
        {"peso_relativo": Decimal("40.00")},
        {"peso_relativo": Decimal("20.00")}
    ]
    service.repo.create_componente_evaluacion.return_value = {
        "id": componente_id,
        "id_seccion": seccion_id,
        "id_tipo_componente": payload.id_tipo_componente,
        "id_escala": escala_id,
        "peso_relativo": Decimal("30.00"),
        "orden_presentacion": 1,
        "estado": "BORRADOR",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    res = await service.crear_componente_evaluacion(tenant_id, seccion_id, payload, actor_id=uuid4())

    assert res.peso_relativo == Decimal("30.00")

@pytest.mark.asyncio
async def test_oferta_crear_componente_evaluacion_exceeds_weight(mock_pool) -> None:
    service = OfertaService(mock_pool)
    service.repo = AsyncMock()

    tenant_id = uuid4()
    seccion_id = uuid4()
    escala_id = uuid4()

    payload = ComponenteEvaluacionCreate(
        id_tipo_componente=uuid4(),
        id_escala=escala_id,
        peso_relativo=Decimal("30.00"),
        orden_presentacion=1
    )

    service.repo.get_by_id.return_value = {"id": seccion_id}
    service.repo.get_escala_by_id_and_tenant.return_value = {"id": escala_id}
    # Existing components sum to 80.00 (80 + 30 = 110 > 100)
    service.repo.list_componentes_by_seccion.return_value = [
        {"peso_relativo": Decimal("50.00")},
        {"peso_relativo": Decimal("30.00")}
    ]

    with pytest.raises(ValidationError, match="La suma de pesos supera el 100% permitido"):
        await service.crear_componente_evaluacion(tenant_id, seccion_id, payload, actor_id=uuid4())
