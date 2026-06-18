"""
Pruebas de integración automatizadas — Módulo Matrícula (Construcción de Software I).

Verifican colaboración real entre componentes (sin mocks internos):
  HTTP (TestClient) → Router → MatriculaService → MatriculaRepository → PostgreSQL
  + contratos con Periodos Académicos, Oferta Académica y Seguimiento Académico.

No son pruebas unitarias ni pruebas manuales (Postman/Thunder).

Ejecución:
  docker compose up -d db
  pytest tests/integration/test_matricula_integration.py -v -m integration
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import IntegrationSeed, auth_headers

pytestmark = pytest.mark.integration


def _crear_matricula(client: TestClient, seed: IntegrationSeed) -> dict:
    response = client.post(
        "/api/v1/matriculas",
        headers=auth_headers(seed),
        json={"id_periodo": str(seed.periodo_matricula_id)},
    )
    assert response.status_code == 201, response.text
    return response.json()


class TestMatriculaIntegracion:
    """
    Escenarios de integración del flujo de negocio de matrícula.
    Cada prueba ejecuta HTTP real y valida efectos en la base de datos.
    """

    def test_01_matricula_exitosa_flujo_completo(
        self,
        client: TestClient,
        seed: IntegrationSeed,
        db,
    ) -> None:
        """
        Alumno → API Periodos/Oferta → API Matrícula → BD → Seguimiento.

        - Periodo en estado MATRICULA (módulo Periodos)
        - Sección con vacantes (módulo Oferta)
        - Matrícula e inscripción persistidas
        - Vacantes disminuyen
        - Cuenta de seguimiento y auditoría actualizadas
        """
        headers = auth_headers(seed)

        # Contrato: Periodos Académicos expone periodo activo
        periodos = client.get("/api/v1/periodos", headers=headers)
        assert periodos.status_code == 200
        assert any(
            p["id"] == str(seed.periodo_matricula_id) and p["estado"] == "MATRICULA"
            for p in periodos.json()
        )

        # Contrato: Oferta Académica expone secciones del periodo
        secciones = client.get(
            f"/api/v1/oferta/periodos/{seed.periodo_matricula_id}/secciones",
            headers=headers,
        )
        assert secciones.status_code == 200
        seccion = next(s for s in secciones.json() if s["id"] == str(seed.seccion_ok_id))
        vacantes_antes = seccion["vacantes_disponibles"]
        assert vacantes_antes > 0

        # Matrícula vía capa HTTP completa
        matricula = _crear_matricula(client, seed)
        matricula_id = matricula["id"]
        assert matricula["estado"] == "ACTIVA"

        inscripcion = client.post(
            f"/api/v1/matriculas/{matricula_id}/inscripciones",
            headers=headers,
            json={"id_seccion": str(seed.seccion_ok_id)},
        )
        assert inscripcion.status_code == 201, inscripcion.text
        ins_body = inscripcion.json()
        inscripcion_id = ins_body["id"]

        # Persistencia: matrícula e inscripción
        row_mat = db.one(
            "SELECT estado, creditos_matriculados FROM matricula WHERE id = :id",
            id=matricula_id,
        )
        assert row_mat["estado"] == "ACTIVA"
        assert row_mat["creditos_matriculados"] == ins_body["creditos"]

        row_ins = db.one(
            "SELECT estado FROM inscripcion WHERE id = :id",
            id=inscripcion_id,
        )
        assert row_ins["estado"] == "ACTIVA"

        # Integración Oferta: vacantes en BD
        vacantes_despues = db.scalar(
            "SELECT vacantes_disponibles FROM seccion WHERE id = :id",
            id=str(seed.seccion_ok_id),
        )
        assert vacantes_despues == vacantes_antes - 1

        # Integración Seguimiento Académico
        seguimiento = db.one(
            """
            SELECT creditos_inscritos_periodo
            FROM cuenta_seguimiento_alumno
            WHERE id_tenant = :tid AND id_alumno = :aid
            """,
            tid=str(seed.tenant_id),
            aid=str(seed.alumno_id),
        )
        assert seguimiento["creditos_inscritos_periodo"] >= ins_body["creditos"]

        eventos = db.scalar(
            """
            SELECT COUNT(*) FROM auditoria_eventos
            WHERE id_tenant = :tid AND tipo_operacion = 'INSCRIPCION_CREADA'
            """,
            tid=str(seed.tenant_id),
        )
        assert eventos >= 1

    def test_02_inscripcion_rechazada_sin_vacantes_bd_consistente(
        self,
        client: TestClient,
        seed: IntegrationSeed,
        db,
    ) -> None:
        """
        Alumno → Matrícula OK → Oferta (sección llena) → rechazo.

        - API responde error de conflicto
        - No se crea inscripción
        - Vacantes y créditos de matrícula sin cambios indebidos
        """
        headers = auth_headers(seed)
        matricula = _crear_matricula(client, seed)
        matricula_id = matricula["id"]

        inscripciones_antes = db.scalar(
            "SELECT COUNT(*) FROM inscripcion WHERE id_matricula = :mid",
            mid=matricula_id,
        )
        creditos_antes = db.scalar(
            "SELECT creditos_matriculados FROM matricula WHERE id = :id",
            id=matricula_id,
        )

        response = client.post(
            f"/api/v1/matriculas/{matricula_id}/inscripciones",
            headers=headers,
            json={"id_seccion": str(seed.seccion_llena_id)},
        )
        assert response.status_code == 409
        assert "vacantes" in response.json()["detail"].lower()

        inscripciones_despues = db.scalar(
            "SELECT COUNT(*) FROM inscripcion WHERE id_matricula = :mid",
            mid=matricula_id,
        )
        assert inscripciones_despues == inscripciones_antes

        creditos_despues = db.scalar(
            "SELECT creditos_matriculados FROM matricula WHERE id = :id",
            id=matricula_id,
        )
        assert creditos_despues == creditos_antes

        vacantes = db.scalar(
            "SELECT vacantes_disponibles FROM seccion WHERE id = :id",
            id=str(seed.seccion_llena_id),
        )
        assert vacantes == 0

    def test_03_inscripcion_rechazada_prerrequisitos_sin_alterar_estado(
        self,
        client: TestClient,
        seed: IntegrationSeed,
        db,
    ) -> None:
        """
        Alumno → Historial (sin curso aprobado) → Matrícula → inscripción rechazada.

        - Validación entre Matrícula y requisitos de Oferta/Historial
        - No se persiste inscripción del curso con prerrequisito
        """
        headers = auth_headers(seed)
        matricula = _crear_matricula(client, seed)
        matricula_id = matricula["id"]

        historial_ok = db.scalar(
            """
            SELECT COUNT(*) FROM inscripcion i
            JOIN matricula m ON m.id = i.id_matricula
            WHERE m.id_alumno = :aid AND i.id_curso = :cid AND i.estado = 'APROBADA'
            """,
            aid=str(seed.alumno_id),
            cid=str(seed.curso_requerido_id),
        )
        assert historial_ok == 0

        response = client.post(
            f"/api/v1/matriculas/{matricula_id}/inscripciones",
            headers=headers,
            json={"id_seccion": str(seed.seccion_prereq_id)},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "prerrequisito" in detail.lower() or "Prerrequisitos" in detail

        inscripciones_curso = db.scalar(
            """
            SELECT COUNT(*) FROM inscripcion
            WHERE id_matricula = :mid AND id_curso = :cid
            """,
            mid=matricula_id,
            cid=str(seed.curso_con_prereq_id),
        )
        assert inscripciones_curso == 0

        seguimiento = db.scalar(
            """
            SELECT creditos_inscritos_periodo
            FROM cuenta_seguimiento_alumno
            WHERE id_tenant = :tid AND id_alumno = :aid
            """,
            tid=str(seed.tenant_id),
            aid=str(seed.alumno_id),
        )
        assert seguimiento == 0

    def test_04_retiro_de_curso_actualiza_estado_y_seguimiento(
        self,
        client: TestClient,
        seed: IntegrationSeed,
        db,
    ) -> None:
        """
        Alumno → Matrícula → Inscripción → Retiro → Seguimiento/Auditoría.

        - Estado de inscripción RETIRADA en API y BD
        - Créditos de matrícula y seguimiento coherentes
        - Vacante liberada en Oferta
        - Evento académico registrado
        """
        headers = auth_headers(seed)
        matricula = _crear_matricula(client, seed)
        matricula_id = matricula["id"]

        ins = client.post(
            f"/api/v1/matriculas/{matricula_id}/inscripciones",
            headers=headers,
            json={"id_seccion": str(seed.seccion_ok_id)},
        )
        assert ins.status_code == 201
        inscripcion_id = ins.json()["id"]
        creditos_curso = ins.json()["creditos"]
        assert creditos_curso > 0

        vacantes_ocupadas = db.scalar(
            "SELECT vacantes_disponibles FROM seccion WHERE id = :id",
            id=str(seed.seccion_ok_id),
        )

        retiro = client.post(
            f"/api/v1/inscripciones/{inscripcion_id}/retiro",
            headers=headers,
            json={"motivo": "Integracion automatizada — retiro"},
        )
        assert retiro.status_code == 200
        assert retiro.json()["estado"] == "RETIRADA"

        fila_ins = db.one(
            "SELECT estado, fecha_retiro FROM inscripcion WHERE id = :id",
            id=inscripcion_id,
        )
        assert fila_ins["estado"] == "RETIRADA"
        assert fila_ins["fecha_retiro"] is not None

        creditos_matricula = db.scalar(
            "SELECT creditos_matriculados FROM matricula WHERE id = :id",
            id=matricula_id,
        )
        assert creditos_matricula == 0

        seguimiento = db.scalar(
            """
            SELECT creditos_inscritos_periodo
            FROM cuenta_seguimiento_alumno
            WHERE id_tenant = :tid AND id_alumno = :aid
            """,
            tid=str(seed.tenant_id),
            aid=str(seed.alumno_id),
        )
        assert seguimiento == 0

        vacantes_final = db.scalar(
            "SELECT vacantes_disponibles FROM seccion WHERE id = :id",
            id=str(seed.seccion_ok_id),
        )
        assert vacantes_final == vacantes_ocupadas + 1

        evento_retiro = db.scalar(
            """
            SELECT COUNT(*) FROM auditoria_eventos
            WHERE id_tenant = :tid AND tipo_operacion = 'INSCRIPCION_RETIRADA'
            """,
            tid=str(seed.tenant_id),
        )
        assert evento_retiro >= 1
