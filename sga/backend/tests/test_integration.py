import os

import pytest  # pyrefly: ignore [missing-import]
import pytest_asyncio  # pyrefly: ignore [missing-import]
from httpx import ASGITransport, AsyncClient  # pyrefly: ignore [missing-import]

# Solo ejecutar si hay base de datos disponible
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Definir RUN_INTEGRATION_TESTS=1 con Docker levantado",
)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    from app.main import app  # pyrefly: ignore [missing-import]
    from app.core.database import lifespan  # pyrefly: ignore [missing-import]

    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_admin_central(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin.central@sga.local",
            "password": "AdminCentral123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["rol"] == "ADMIN_CENTRAL"


async def get_admin_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@uni-demo.local",
            "password": "AdminDemo123!",
            "dominio_tenant": "uni-demo",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_periodo_integration_flow(client: AsyncClient) -> None:
    from app.core.database import db  # pyrefly: ignore [missing-import]
    # Limpiar cualquier periodo activo remanente de ejecuciones previas
    async with db.connection().acquire() as conn:
        await conn.execute(
            "UPDATE periodo_academico SET estado = 'CERRADO' WHERE estado IN ('MATRICULA', 'REGISTRO_NOTAS')"
        )

    headers = await get_admin_headers(client)

    # 1. Crear periodo 1 (max_length=20)
    periodo1_name = f"P1-{os.getpid()}"
    res_p1 = await client.post(
        "/api/v1/periodos",
        json={
            "nombre_periodo": periodo1_name,
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-07-20",
        },
        headers=headers,
    )
    assert res_p1.status_code == 201
    p1 = res_p1.json()
    assert p1["nombre_periodo"] == periodo1_name
    assert p1["estado"] == "CONFIGURACION"
    p1_id = p1["id"]

    # 2. Listar periodos y encontrar el nuevo
    res_list = await client.get("/api/v1/periodos", headers=headers)
    assert res_list.status_code == 200
    periodos = res_list.json()
    found = any(p["id"] == p1_id for p in periodos)
    assert found, "El periodo creado no se encontró en la lista."

    # 3. Transicionar periodo 1 a MATRICULA
    res_trans1 = await client.post(
        f"/api/v1/periodos/{p1_id}/transicion",
        json={"estado_nuevo": "MATRICULA"},
        headers=headers,
    )
    assert res_trans1.status_code == 200
    assert res_trans1.json()["estado"] == "MATRICULA"

    # 4. Crear periodo 2 (max_length=20)
    periodo2_name = f"P2-{os.getpid()}"
    res_p2 = await client.post(
        "/api/v1/periodos",
        json={
            "nombre_periodo": periodo2_name,
            "fecha_inicio": "2026-08-01",
            "fecha_fin": "2026-12-15",
        },
        headers=headers,
    )
    assert res_p2.status_code == 201
    p2_id = res_p2.json()["id"]

    # 5. Intentar transicionar periodo 2 a MATRICULA (Debe fallar con 409 por simultaneidad activa)
    res_trans2_fail = await client.post(
        f"/api/v1/periodos/{p2_id}/transicion",
        json={"estado_nuevo": "MATRICULA"},
        headers=headers,
    )
    assert res_trans2_fail.status_code == 409

    # 6. Limpiar estado transicionando P1 a CERRADO
    await client.post(
        f"/api/v1/periodos/{p1_id}/transicion",
        json={"estado_nuevo": "REGISTRO_NOTAS"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/periodos/{p1_id}/transicion",
        json={"estado_nuevo": "CERRADO"},
        headers=headers,
    )


async def get_admin_central_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin.central@sga.local",
            "password": "AdminCentral123!",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_oferta_academica_integration_flow(client: AsyncClient) -> None:
    central_headers = await get_admin_central_headers(client)
    admin_headers = await get_admin_headers(client)
    tenant_id = "a1111111-1111-1111-1111-111111111111"

    # 1. Obtener o crear escala de evaluación
    res_escalas = await client.get(
        f"/api/v1/tenants/{tenant_id}/catalogos/escalas-evaluacion",
        headers=central_headers,
    )
    assert res_escalas.status_code == 200
    escalas = res_escalas.json()
    if not escalas:
        res_scale_create = await client.post(
            f"/api/v1/tenants/{tenant_id}/catalogos/escalas-evaluacion",
            json={
                "nombre_escala": "Vigesimal",
                "nota_minima": 0.0,
                "nota_maxima": 20.0,
                "nota_aprobatoria": 10.5,
            },
            headers=central_headers,
        )
        assert res_scale_create.status_code == 201
        escala_id = res_scale_create.json()["id"]
    else:
        escala_id = escalas[0]["id"]

    # 2. Obtener o crear tipo de evaluacion "PC"
    res_tipos = await client.get(
        f"/api/v1/tenants/{tenant_id}/catalogos/tipos-evaluacion",
        headers=central_headers,
    )
    assert res_tipos.status_code == 200
    tipos = res_tipos.json()
    pc_tipo = next((t for t in tipos if t["codigo"] == "PC"), None)
    if not pc_tipo:
        res_tipo_create = await client.post(
            f"/api/v1/tenants/{tenant_id}/catalogos/tipos-evaluacion",
            json={
                "codigo": "PC",
                "nombre": "Practica Calificada",
                "descripcion": "Evaluacion de practica continua",
            },
            headers=central_headers,
        )
        assert res_tipo_create.status_code == 201
        tipo_comp_id = res_tipo_create.json()["id"]
    else:
        tipo_comp_id = pc_tipo["id"]

    # 3. Crear Periodo Académico
    period_name = f"P-OF-{os.getpid()}"
    if len(period_name) > 20:
        period_name = period_name[:20]
    res_period = await client.post(
        "/api/v1/periodos",
        json={
            "nombre_periodo": period_name,
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-07-20",
        },
        headers=admin_headers,
    )
    assert res_period.status_code == 201
    period_id = res_period.json()["id"]

    # 4. Crear Plan de Estudios
    carrera_name = f"Carrera-{os.getpid()}"
    res_plan = await client.post(
        "/api/v1/oferta/planes-estudio",
        json={
            "carrera": carrera_name,
            "version_plan": "2026-I",
            "creditos_totales": 200,
        },
        headers=admin_headers,
    )
    assert res_plan.status_code == 201
    plan_id = res_plan.json()["id"]

    # 5. Activar Plan de Estudios
    res_act_plan = await client.put(
        f"/api/v1/oferta/planes-estudio/{plan_id}/activar",
        headers=admin_headers,
    )
    assert res_act_plan.status_code == 200
    assert res_act_plan.json()["estado"] == "ACTIVO"

    # 6. Crear Curso
    course_code = f"C-{os.getpid()}"
    if len(course_code) > 20:
        course_code = course_code[:20]
    res_course = await client.post(
        "/api/v1/oferta/cursos",
        json={
            "codigo_curso": course_code,
            "nombre_curso": "Ingenieria de Requerimientos",
            "creditos": 4,
            "tipo_curso": "OBLIGATORIO",
            "ciclo_sugerido": 5,
        },
        headers=admin_headers,
    )
    assert res_course.status_code == 201
    course_id = res_course.json()["id"]

    # 7. Asociar Curso al Plan de Estudios
    res_assoc = await client.post(
        f"/api/v1/oferta/planes-estudio/{plan_id}/cursos",
        json={
            "id_curso": course_id,
            "ciclo_en_plan": 5,
            "es_obligatorio": True,
        },
        headers=admin_headers,
    )
    assert res_assoc.status_code == 201

    # 8. Crear Sección (Periodo en CONFIGURACION, OK)
    res_sec = await client.post(
        "/api/v1/oferta/secciones",
        json={
            "id_periodo": period_id,
            "id_curso": course_id,
            "codigo_seccion": "A",
            "vacantes_maximas": 40,
        },
        headers=admin_headers,
    )
    assert res_sec.status_code == 201
    seccion_id = res_sec.json()["id"]

    # 9. Crear Evaluación Académica (40%, OK)
    res_comp1 = await client.post(
        f"/api/v1/oferta/secciones/{seccion_id}/evaluaciones",
        json={
            "id_tipo_evaluacion": tipo_comp_id,
            "id_escala": escala_id,
            "peso_relativo": 40.0,
            "orden_presentacion": 1,
        },
        headers=admin_headers,
    )
    assert res_comp1.status_code == 201

    # 10. Crear Evaluación Académica Excesiva (70%, Error 400)
    res_comp2 = await client.post(
        f"/api/v1/oferta/secciones/{seccion_id}/evaluaciones",
        json={
            "id_tipo_evaluacion": tipo_comp_id,
            "id_escala": escala_id,
            "peso_relativo": 70.0,
            "orden_presentacion": 2,
        },
        headers=admin_headers,
    )
    assert res_comp2.status_code == 400

    # 11. Transicionar Periodo a MATRICULA
    res_trans = await client.post(
        f"/api/v1/periodos/{period_id}/transicion",
        json={"estado_nuevo": "MATRICULA"},
        headers=admin_headers,
    )
    assert res_trans.status_code == 200
    assert res_trans.json()["estado"] == "MATRICULA"

    # 12. Intentar crear sección (Periodo en MATRICULA, Error 400)
    res_sec_fail = await client.post(
        "/api/v1/oferta/secciones",
        json={
            "id_periodo": period_id,
            "id_curso": course_id,
            "codigo_seccion": "B",
            "vacantes_maximas": 40,
        },
        headers=admin_headers,
    )
    assert res_sec_fail.status_code == 400

    # 13. Limpiar estado transicionando el periodo creado a CERRADO
    await client.post(
        f"/api/v1/periodos/{period_id}/transicion",
        json={"estado_nuevo": "REGISTRO_NOTAS"},
        headers=admin_headers,
    )
    await client.post(
        f"/api/v1/periodos/{period_id}/transicion",
        json={"estado_nuevo": "CERRADO"},
        headers=admin_headers,
    )




