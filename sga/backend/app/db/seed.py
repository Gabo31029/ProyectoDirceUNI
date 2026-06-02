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

        demo_tenant_id = await conn.fetchval(
            "SELECT id FROM tenants WHERE dominio = 'uni-demo'"
        )
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
