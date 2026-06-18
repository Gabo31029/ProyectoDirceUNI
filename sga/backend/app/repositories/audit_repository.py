import json
from typing import Any
from uuid import UUID

import asyncpg


class AuditRepository:
    async def registrar(
        self,
        conn: asyncpg.Connection,
        *,
        id_tenant: UUID | None,
        id_usuario: UUID | None,
        tipo_operacion: str,
        entidad_afectada: str | None = None,
        id_entidad: UUID | None = None,
        valor_anterior: dict | None = None,
        valor_nuevo: dict | None = None,
        motivo_rechazo: str | None = None,
    ) -> None:
        await conn.execute(
            """
            INSERT INTO auditoria_eventos (
                id_tenant, id_usuario, tipo_operacion, entidad_afectada,
                id_entidad, valor_anterior, valor_nuevo, motivo_rechazo
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8)
            """,
            id_tenant,
            id_usuario,
            tipo_operacion,
            entidad_afectada,
            id_entidad,
            json.dumps(valor_anterior, default=str) if valor_anterior else None,
            json.dumps(valor_nuevo, default=str) if valor_nuevo else None,
            motivo_rechazo,
        )
