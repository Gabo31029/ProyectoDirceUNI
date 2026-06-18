import asyncpg

from app.core.security import hash_password
from app.repositories.audit_repository import AuditRepository


async def run_seed(pool: asyncpg.Pool) -> None:
    """Crea datos base de desarrollo si no existen."""
    from app.core.config import get_settings

    settings = get_settings()
    if settings.environment != "development":
        return

    audit_repo = AuditRepository()
    async with pool.acquire() as conn:
        exists_central = await conn.fetchval(
            "SELECT 1 FROM usuarios WHERE email = $1 AND id_tenant IS NULL",
            settings.seed_admin_central_email,
        )
        if not exists_central:
            user_id = await conn.fetchval(
                """
                INSERT INTO usuarios (
                    email, password_hash, nombre, apellido, rol, id_tenant, activo
                ) VALUES ($1, $2, $3, $4, 'ADMIN_CENTRAL', NULL, TRUE)
                RETURNING id
                """,
                settings.seed_admin_central_email,
                hash_password(settings.seed_admin_central_password),
                "Administrador",
                "Central",
            )
            await audit_repo.registrar(
                conn,
                id_tenant=None,
                id_usuario=user_id,
                tipo_operacion="USUARIO_CREADO",
                entidad_afectada="usuarios",
                id_entidad=user_id,
                valor_nuevo={"email": settings.seed_admin_central_email, "rol": "ADMIN_CENTRAL"},
            )

        exists_tenant = await conn.fetchval(
            "SELECT id FROM tenants WHERE dominio = 'uni-demo'"
        )
        if not exists_tenant:
            demo_tenant_id = await conn.fetchval(
                """
                INSERT INTO tenants (id, nombre, dominio, zona_horaria)
                VALUES ('a1111111-1111-1111-1111-111111111111', 'Universidad Demo', 'uni-demo', 'America/Lima')
                RETURNING id
                """
            )
        else:
            demo_tenant_id = exists_tenant

        if demo_tenant_id:
            exists_admin = await conn.fetchval(
                """
                SELECT 1 FROM usuarios
                WHERE email = 'admin@uni-demo.local' AND id_tenant = $1
                """,
                demo_tenant_id,
            )
            if not exists_admin:
                await conn.execute(
                    """
                    INSERT INTO usuarios (
                        id_tenant, email, password_hash, nombre, apellido, rol, activo
                    ) VALUES ($1, $2, $3, $4, $5, 'ADMIN', TRUE)
                    """,
                    demo_tenant_id,
                    "admin@uni-demo.local",
                    hash_password("AdminDemo123!"),
                    "Admin",
                    "Demo",
                )

        if demo_tenant_id:
            await _seed_matricula_demo(conn, demo_tenant_id)


async def _seed_matricula_demo(conn: asyncpg.Connection, tenant_id) -> None:
    """Datos minimos para probar matricula en desarrollo."""
    if tenant_id is None:
        return
    alumno_id = await conn.fetchval(
        """
        SELECT id FROM usuarios
        WHERE id_tenant = $1 AND email = 'alumno@uni-demo.local'
        """,
        tenant_id,
    )
    if alumno_id is None:
        alumno_id = await conn.fetchval(
            """
            INSERT INTO usuarios (
                id_tenant, email, password_hash, nombre, apellido, rol, activo
            ) VALUES ($1, $2, $3, $4, $5, 'ALUMNO', TRUE)
            RETURNING id
            """,
            tenant_id,
            "alumno@uni-demo.local",
            hash_password("AlumnoDemo123!"),
            "Juan",
            "Perez",
        )

    periodo_id = await conn.fetchval(
        """
        SELECT id FROM periodo_academico
        WHERE id_tenant = $1 AND nombre_periodo = '2026-1'
        """,
        tenant_id,
    )
    if periodo_id is None:
        periodo_id = await conn.fetchval(
            """
            INSERT INTO periodo_academico (
                id_tenant, nombre_periodo, fecha_inicio, fecha_fin, estado
            ) VALUES ($1, '2026-1', '2026-03-01', '2026-07-15', 'MATRICULA')
            RETURNING id
            """,
            tenant_id,
        )
        politica_exists = await conn.fetchval(
            "SELECT 1 FROM politica_credito WHERE id_periodo = $1",
            periodo_id,
        )
        if not politica_exists:
            await conn.execute(
                """
                INSERT INTO politica_credito (id_periodo, ppa_minimo, ppa_maximo, creditos_maximos)
                VALUES ($1, 0, 20, 18)
                """,
                periodo_id,
            )

    curso_id = await conn.fetchval(
        """
        SELECT id FROM curso WHERE id_tenant = $1 AND codigo_curso = 'MAT101'
        """,
        tenant_id,
    )
    if curso_id is None:
        curso_id = await conn.fetchval(
            """
            INSERT INTO curso (
                id_tenant, codigo_curso, nombre_curso, creditos, tipo_curso, ciclo_sugerido
            ) VALUES ($1, 'MAT101', 'Matematicas I', 4, 'OBLIGATORIO', 1)
            RETURNING id
            """,
            tenant_id,
        )

    seccion_exists = await conn.fetchval(
        """
        SELECT 1 FROM seccion
        WHERE id_periodo = $1 AND id_curso = $2 AND codigo_seccion = 'A'
        """,
        periodo_id,
        curso_id,
    )
    if not seccion_exists and periodo_id and curso_id:
        await conn.execute(
            """
            INSERT INTO seccion (
                id_tenant, id_periodo, id_curso, codigo_seccion,
                vacantes_maximas, vacantes_disponibles, estado
            ) VALUES ($1, $2, $3, 'A', 30, 30, 'ABIERTA')
            """,
            tenant_id,
            periodo_id,
            curso_id,
        )
