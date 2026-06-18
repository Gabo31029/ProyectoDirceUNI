"""
Fixtures para pruebas de integración automatizadas (pytest).

- HTTP real: FastAPI TestClient → Router → Service → Repository → BD
- Sin mocks de módulos internos
- Verificación de persistencia: SQLAlchemy
- PostgreSQL real (asyncpg). SQLite no es compatible sin cambiar producción.

Sin Docker (Supabase del .env):
  cd Proy_SW505_2026_1_Grupo_4/sga/backend
  .venv/bin/python scripts/apply_supabase_hybrid_migration.py   # una sola vez
  ./scripts/run_integration_pytest.sh

Con Docker local (schema limpio db/schema.sql):
  docker compose up -d db
  TEST_DATABASE_URL=postgresql://sga:sga_dev@127.0.0.1:5432/sga ./scripts/run_integration_pytest.sh

ADVERTENCIA: cada prueba borra solo el tenant de prueba f1111111-...
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password

BACKEND_ROOT = Path(__file__).resolve().parents[2]
LOCAL_DEFAULT = "postgresql://sga:sga_dev@127.0.0.1:5432/sga"


def _load_database_url_from_dotenv() -> str | None:
    env_path = BACKEND_ROOT / ".env"
    if not env_path.is_file():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL=") and not line.endswith("="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


def _resolve_test_database_url() -> str:
    explicit = os.getenv("TEST_DATABASE_URL")
    if explicit:
        return explicit
    from_env = os.getenv("DATABASE_URL") or _load_database_url_from_dotenv()
    if from_env:
        return from_env
    return LOCAL_DEFAULT


TEST_DATABASE_URL = _resolve_test_database_url()

TENANT_ID = UUID("f1111111-1111-1111-1111-111111111111")
ALUMNO_ID = UUID("f2222222-2222-2222-2222-222222222222")
PERIODO_MATRICULA_ID = UUID("f3333333-3333-3333-3333-333333333333")
CURSO_BASE_ID = UUID("f5555555-5555-5555-5555-555555555555")
CURSO_CON_PREREQ_ID = UUID("f6666666-6666-6666-6666-666666666666")
CURSO_REQUERIDO_ID = UUID("f7777777-7777-7777-7777-777777777777")
SECCION_OK_ID = UUID("f8888888-8888-8888-8888-888888888888")
SECCION_LLENA_ID = UUID("f9999999-9999-9999-9999-999999999999")
SECCION_PREREQ_ID = UUID("faaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
PLAN_ESTUDIOS_ID = UUID("f4444444-4444-4444-4444-444444444444")

HYBRID_MIGRATION = BACKEND_ROOT / "db" / "migrations" / "006_supabase_hybrid_perfil_sync.sql"


def _matricula_columns(conn) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'matricula'
                """
            )
        )
    }


def _table_exists(conn, table_name: str) -> bool:
    return (
        conn.execute(
            text(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = :name
                """
            ),
            {"name": table_name},
        ).first()
        is not None
    )


def _is_hybrid_schema(conn) -> bool:
    cols = _matricula_columns(conn)
    return "id_alumno" in cols and "id_perfil_alumno" in cols


def _apply_hybrid_migration(conn) -> None:
    if not HYBRID_MIGRATION.is_file():
        return
    conn.execute(text(HYBRID_MIGRATION.read_text(encoding="utf-8")))


def _insert_hybrid_legacy_seed(conn, params: dict) -> None:
    """Perfil legacy requerido por columnas id_perfil_alumno en Supabase híbrido."""
    conn.execute(
        text(
            """
            INSERT INTO usuario (
                id_usuario, id_tenant, nombre_completo, email, password_hash, rol
            ) VALUES (
                CAST(:alumno_id AS uuid), CAST(:tenant_id AS uuid),
                'Ana Integracion', 'alumno.int@test.local', :pwd, 'ALUMNO'
            )
            """
        ),
        params,
    )
    conn.execute(
        text(
            """
            INSERT INTO plan_estudios (
                id, id_plan_estudios, id_tenant, carrera, version_plan, creditos_totales, estado
            ) VALUES (
                CAST(:plan_id AS uuid), CAST(:plan_id AS uuid), CAST(:tenant_id AS uuid),
                'Ingenieria Integracion', 'v1', 120, 'ACTIVO'
            )
            """
        ),
        params,
    )
    conn.execute(
        text(
            """
            INSERT INTO perfil_alumno (
                id_perfil_alumno, id_usuario, id_plan_estudios,
                codigo_alumno, carrera, periodo_ingreso
            ) VALUES (
                CAST(:alumno_id AS uuid), CAST(:alumno_id AS uuid),
                CAST(:plan_id AS uuid), 'INT-001', 'Ingenieria Integracion', '2026-1'
            )
            """
        ),
        params,
    )


def _cleanup_integration_data(conn, tenant_id: str) -> None:
    """Borra solo datos del tenant de prueba (seguro en Supabase compartido)."""
    statements = [
        "DELETE FROM inscripcion WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM matricula WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM cuenta_seguimiento_alumno WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM auditoria_eventos WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM seccion WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM prerrequisito WHERE id_curso IN (SELECT id FROM curso WHERE id_tenant = CAST(:tid AS uuid))",
        "DELETE FROM politica_credito WHERE id_periodo IN (SELECT id FROM periodo_academico WHERE id_tenant = CAST(:tid AS uuid))",
        "DELETE FROM periodo_academico WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM curso WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM perfil_alumno WHERE id_usuario IN (SELECT id FROM usuarios WHERE id_tenant = CAST(:tid AS uuid))",
        "DELETE FROM plan_estudios WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM usuario WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM usuarios WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM tenants WHERE id = CAST(:tid AS uuid)",
    ]
    for sql in statements:
        conn.execute(text(sql), {"tid": tenant_id})


@dataclass(frozen=True)
class IntegrationSeed:
    """Datos semilla compartidos entre módulos (periodos, oferta, matrícula)."""

    tenant_id: UUID
    alumno_id: UUID
    periodo_matricula_id: UUID
    seccion_ok_id: UUID
    seccion_llena_id: UUID
    seccion_prereq_id: UUID
    curso_con_prereq_id: UUID
    curso_requerido_id: UUID
    alumno_token: str


def _engine_url() -> str:
    url = TEST_DATABASE_URL
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _create_db_engine() -> Engine:
    url = _engine_url()
    connect_args: dict = {}
    if "supabase" in url.lower():
        connect_args["sslmode"] = "require"
    return create_engine(url, connect_args=connect_args or None)


def _assert_matricula_schema_compatible(conn) -> None:
    """Requiere columnas del módulo matrícula (id_alumno). Supabase híbrido: migración 006."""
    cols = _matricula_columns(conn)
    if "id_alumno" not in cols:
        pytest.skip(
            "Tabla matricula sin id_alumno. Aplica db/schema.sql o migrations/004 en la BD."
        )
    if _is_hybrid_schema(conn):
        if not _table_exists(conn, "perfil_alumno"):
            pytest.skip(
                "Schema híbrido sin tabla perfil_alumno. "
                "Ejecuta: .venv/bin/python scripts/apply_supabase_hybrid_migration.py"
            )
        _apply_hybrid_migration(conn)


@pytest.fixture(scope="session")
def test_database_available() -> str:
    engine = _create_db_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        with engine.begin() as conn:
            _assert_matricula_schema_compatible(conn)
    except Exception as exc:
        pytest.skip(
            f"BD de integración no disponible: {exc}\n"
            f"URL probada: {TEST_DATABASE_URL.split('@')[-1] if '@' in TEST_DATABASE_URL else TEST_DATABASE_URL}\n"
            "Opciones: docker compose up -d db  O  TEST_DATABASE_URL / .env DATABASE_URL."
        )
    finally:
        engine.dispose()
    return TEST_DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def configure_integration_environment(test_database_available: str) -> None:
    os.environ["DATABASE_URL"] = test_database_available
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_USE_POOLER"] = "false"
    os.environ.pop("SUPABASE_PROJECT_REF", None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def db_engine(test_database_available: str):
    engine = _create_db_engine()
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def isolated_database(db_engine) -> None:
    tid = str(TENANT_ID)
    with db_engine.begin() as conn:
        _cleanup_integration_data(conn, tid)
    yield
    with db_engine.begin() as conn:
        _cleanup_integration_data(conn, tid)


def _insert_seed_data(conn) -> IntegrationSeed:
    pwd = hash_password("AlumnoTest123!")
    params = {
        "tenant_id": str(TENANT_ID),
        "alumno_id": str(ALUMNO_ID),
        "periodo_id": str(PERIODO_MATRICULA_ID),
        "pwd": pwd,
        "curso_base": str(CURSO_BASE_ID),
        "curso_adv": str(CURSO_CON_PREREQ_ID),
        "curso_req": str(CURSO_REQUERIDO_ID),
        "sec_ok": str(SECCION_OK_ID),
        "sec_llena": str(SECCION_LLENA_ID),
        "sec_prereq": str(SECCION_PREREQ_ID),
        "plan_id": str(PLAN_ESTUDIOS_ID),
    }
    hybrid = _is_hybrid_schema(conn)
    if hybrid:
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, id_tenant, nombre, dominio, zona_horaria, estado)
                VALUES (
                    CAST(:tenant_id AS uuid), CAST(:tenant_id AS uuid),
                    'Tenant Integracion', 'uni-int', 'America/Lima', 'ACTIVO'
                )
                """
            ),
            params,
        )
    else:
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, nombre, dominio, zona_horaria, estado)
                VALUES (CAST(:tenant_id AS uuid), 'Tenant Integracion', 'uni-int', 'America/Lima', 'ACTIVO')
                """
            ),
            params,
        )
    conn.execute(
        text(
            """
            INSERT INTO usuarios (
                id, id_tenant, email, password_hash, nombre, apellido, rol, activo
            ) VALUES (
                CAST(:alumno_id AS uuid), CAST(:tenant_id AS uuid), 'alumno.int@test.local', :pwd,
                'Ana', 'Integracion', 'ALUMNO', TRUE
            )
            """
        ),
        params,
    )
    if hybrid:
        _insert_hybrid_legacy_seed(conn, params)
    if hybrid:
        conn.execute(
            text(
                """
                INSERT INTO periodo_academico (
                    id, id_periodo, id_tenant, nombre_periodo, fecha_inicio, fecha_fin, estado
                ) VALUES (
                    CAST(:periodo_id AS uuid), CAST(:periodo_id AS uuid), CAST(:tenant_id AS uuid), '2026-1',
                    '2026-03-01', '2026-07-15', 'MATRICULA'
                )
                """
            ),
            params,
        )
    else:
        conn.execute(
            text(
                """
                INSERT INTO periodo_academico (
                    id, id_tenant, nombre_periodo, fecha_inicio, fecha_fin, estado
                ) VALUES (
                    CAST(:periodo_id AS uuid), CAST(:tenant_id AS uuid), '2026-1',
                    '2026-03-01', '2026-07-15', 'MATRICULA'
                )
                """
            ),
            params,
        )
    conn.execute(
        text(
            """
            INSERT INTO politica_credito (id_periodo, ppa_minimo, ppa_maximo, creditos_maximos)
            VALUES (CAST(:periodo_id AS uuid), 0, 20, 18)
            """
        ),
        params,
    )
    if hybrid:
        conn.execute(
            text(
                """
                INSERT INTO curso (
                    id, id_curso, id_tenant, codigo_curso, nombre_curso, creditos, tipo_curso, ciclo_sugerido
                ) VALUES
                    (CAST(:curso_base AS uuid), CAST(:curso_base AS uuid), CAST(:tenant_id AS uuid), 'MAT101', 'Matematicas I', 4, 'OBLIGATORIO', 1),
                    (CAST(:curso_adv AS uuid), CAST(:curso_adv AS uuid), CAST(:tenant_id AS uuid), 'MAT201', 'Matematicas II', 4, 'OBLIGATORIO', 2),
                    (CAST(:curso_req AS uuid), CAST(:curso_req AS uuid), CAST(:tenant_id AS uuid), 'MAT100', 'Precalculo', 3, 'OBLIGATORIO', 1)
                """
            ),
            params,
        )
    else:
        conn.execute(
            text(
                """
                INSERT INTO curso (
                    id, id_tenant, codigo_curso, nombre_curso, creditos, tipo_curso, ciclo_sugerido
                ) VALUES
                    (CAST(:curso_base AS uuid), CAST(:tenant_id AS uuid), 'MAT101', 'Matematicas I', 4, 'OBLIGATORIO', 1),
                    (CAST(:curso_adv AS uuid), CAST(:tenant_id AS uuid), 'MAT201', 'Matematicas II', 4, 'OBLIGATORIO', 2),
                    (CAST(:curso_req AS uuid), CAST(:tenant_id AS uuid), 'MAT100', 'Precalculo', 3, 'OBLIGATORIO', 1)
                """
            ),
            params,
        )
    conn.execute(
        text(
            """
            INSERT INTO prerrequisito (id_curso, id_curso_requerido, tipo_prereq)
            VALUES (CAST(:curso_adv AS uuid), CAST(:curso_req AS uuid), 'APROBACION_CURSO')
            """
        ),
        params,
    )
    if hybrid:
        conn.execute(
            text(
                """
                INSERT INTO seccion (
                    id, id_seccion, id_tenant, id_periodo, id_curso, codigo_seccion,
                    vacantes_maximas, vacantes_disponibles, estado
                ) VALUES
                    (CAST(:sec_ok AS uuid), CAST(:sec_ok AS uuid), CAST(:tenant_id AS uuid), CAST(:periodo_id AS uuid), CAST(:curso_base AS uuid), 'A', 30, 30, 'ABIERTA'),
                    (CAST(:sec_llena AS uuid), CAST(:sec_llena AS uuid), CAST(:tenant_id AS uuid), CAST(:periodo_id AS uuid), CAST(:curso_base AS uuid), 'B', 10, 0, 'ABIERTA'),
                    (CAST(:sec_prereq AS uuid), CAST(:sec_prereq AS uuid), CAST(:tenant_id AS uuid), CAST(:periodo_id AS uuid), CAST(:curso_adv AS uuid), 'C', 20, 20, 'ABIERTA')
                """
            ),
            params,
        )
    else:
        conn.execute(
            text(
                """
                INSERT INTO seccion (
                    id, id_tenant, id_periodo, id_curso, codigo_seccion,
                    vacantes_maximas, vacantes_disponibles, estado
                ) VALUES
                    (CAST(:sec_ok AS uuid), CAST(:tenant_id AS uuid), CAST(:periodo_id AS uuid), CAST(:curso_base AS uuid), 'A', 30, 30, 'ABIERTA'),
                    (CAST(:sec_llena AS uuid), CAST(:tenant_id AS uuid), CAST(:periodo_id AS uuid), CAST(:curso_base AS uuid), 'B', 10, 0, 'ABIERTA'),
                    (CAST(:sec_prereq AS uuid), CAST(:tenant_id AS uuid), CAST(:periodo_id AS uuid), CAST(:curso_adv AS uuid), 'C', 20, 20, 'ABIERTA')
                """
            ),
            params,
        )
    token, _, _ = create_access_token(
        user_id=ALUMNO_ID, rol="ALUMNO", tenant_id=TENANT_ID
    )
    return IntegrationSeed(
        tenant_id=TENANT_ID,
        alumno_id=ALUMNO_ID,
        periodo_matricula_id=PERIODO_MATRICULA_ID,
        seccion_ok_id=SECCION_OK_ID,
        seccion_llena_id=SECCION_LLENA_ID,
        seccion_prereq_id=SECCION_PREREQ_ID,
        curso_con_prereq_id=CURSO_CON_PREREQ_ID,
        curso_requerido_id=CURSO_REQUERIDO_ID,
        alumno_token=token,
    )


@pytest.fixture
def seed(db_engine) -> IntegrationSeed:
    with db_engine.begin() as conn:
        return _insert_seed_data(conn)


@pytest.fixture
def client() -> TestClient:
    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def auth_headers(seed: IntegrationSeed) -> dict[str, str]:
    return {"Authorization": f"Bearer {seed.alumno_token}"}


@pytest.fixture
def db(db_engine):
    """Acceso SQLAlchemy para verificar estado persistido tras cada request HTTP."""

    class DatabaseVerifier:
        def one(self, sql: str, **params):
            with db_engine.connect() as conn:
                row = conn.execute(text(sql), params).mappings().first()
            assert row is not None, f"Sin filas para: {sql} {params}"
            return row

        def scalar(self, sql: str, **params):
            with db_engine.connect() as conn:
                return conn.execute(text(sql), params).scalar()

        def all(self, sql: str, **params):
            with db_engine.connect() as conn:
                return conn.execute(text(sql), params).mappings().all()

    return DatabaseVerifier()
