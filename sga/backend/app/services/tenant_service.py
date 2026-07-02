from uuid import UUID

import asyncpg

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.tenant import validar_dominio_tenant
from app.domain.users import validar_escala_evaluacion
from app.models.schemas import (
    EscalaEvaluacionCreate,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
    TipoCatalogoCreate,
    TipoEventoCreate,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.tenant_repository import TenantRepository


def _map_tenant(row: asyncpg.Record) -> TenantResponse:
    return TenantResponse(
        id=str(row["id"]),
        nombre=row["nombre"],
        dominio=row["dominio"],
        zona_horaria=row["zona_horaria"],
        estado=row["estado"],
    )


class TenantService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.repo = TenantRepository(pool)
        self.audit_repo = AuditRepository()
        self.pool = pool

    async def create_tenant(
        self, payload: TenantCreate, *, actor_id: UUID
    ) -> TenantResponse:
        import uuid
        try:
            validar_dominio_tenant(payload.dominio)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        if await self.repo.get_by_dominio(payload.dominio):
            raise ConflictError("Ya existe un tenant con ese dominio.")

        row = await self.repo.create(
            nombre=payload.nombre,
            dominio=payload.dominio,
            zona_horaria=payload.zona_horaria,
        )

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                default_conditions = [
                    ("PRUEBA_ACADEMICA", "Prueba Académica", "El estudiante tiene un rendimiento deficiente y se encuentra en periodo de prueba."),
                    ("RIESGO_ACADEMICO", "Riesgo Académico", "El estudiante tiene un promedio ponderado bajo o desaprobaciones acumuladas."),
                    ("SANCIONADO", "Sancionado", "El estudiante tiene una sanción disciplinaria o académica."),
                    ("EGRESADO", "Egresado", "El estudiante ha completado satisfactoriamente los requisitos del plan.")
                ]
                for codigo, nombre, descripcion in default_conditions:
                    cond_id = uuid.uuid4()
                    await conn.execute(
                        """
                        INSERT INTO cat_tipo_condicion (id, id_tenant, codigo, nombre, descripcion)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        cond_id,
                        row["id"],
                        codigo,
                        nombre,
                        descripcion,
                    )
                    await conn.execute(
                        """
                        INSERT INTO tipo_condicion_academica (id_tipo_condicion, id_tenant, codigo, nombre, descripcion)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        cond_id,
                        row["id_tenant"],
                        codigo,
                        nombre,
                        descripcion,
                    )

                default_events = [
                    ("EVT-NOTA-FINAL-CALCULADA", "Nota Final Calculada", "CTA-CREDITOS-APROBADOS", "INCREMENTO"),
                    ("EVT-REPROBO-CURSO", "Reprobó Curso", "CTA-DESAPROBACIONES", "INCREMENTO"),
                    ("EVT-SNAPSHOT-PROMEDIO", "Snapshot de Promedio Semestral/Acumulado", "CTA-PROMEDIO-SNAPSHOT", "ASIGNACION"),
                    ("EVT-CONDICION-ACTIVADA", "Condición Académica Activada", None, None),
                    ("EVT-CONDICION-RESUELTA", "Condición Académica Resuelta", None, None),
                    ("EVT-NOTA-CORREGIDA", "Nota Corregida por Docente", "CTA-CREDITOS-APROBADOS", "INCREMENTO"),
                ]
                for codigo, nombre, cuenta_obj, operacion in default_events:
                    evt_id = uuid.uuid4()
                    await conn.execute(
                        """
                        INSERT INTO cat_tipo_evento (id, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        evt_id,
                        row["id"],
                        codigo,
                        nombre,
                        cuenta_obj,
                        operacion,
                    )
                    await conn.execute(
                        """
                        INSERT INTO tipo_evento (id_tipo_evento, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        evt_id,
                        row["id_tenant"],
                        codigo,
                        nombre,
                        cuenta_obj,
                        operacion,
                    )

                await self.audit_repo.registrar(
                    conn,
                    id_tenant=row["id"],
                    id_usuario=actor_id,
                    tipo_operacion="TENANT_CREADO",
                    entidad_afectada="tenants",
                    id_entidad=row["id"],
                    valor_nuevo={"nombre": payload.nombre, "dominio": payload.dominio},
                )
        return _map_tenant(row)

    async def list_tenants(self) -> list[TenantResponse]:
        rows = await self.repo.list_all()
        return [_map_tenant(row) for row in rows]

    async def get_tenant(self, tenant_id: UUID) -> TenantResponse:
        row = await self.repo.get_by_id(tenant_id)
        if row is None:
            raise NotFoundError("Tenant no encontrado.")
        return _map_tenant(row)

    async def update_tenant(
        self,
        tenant_id: UUID,
        payload: TenantUpdate,
        *,
        actor_id: UUID,
    ) -> TenantResponse:
        existing = await self.repo.get_by_id(tenant_id)
        if existing is None:
            raise NotFoundError("Tenant no encontrado.")

        row = await self.repo.update(
            tenant_id,
            nombre=payload.nombre,
            zona_horaria=payload.zona_horaria,
            estado=payload.estado.value if payload.estado else None,
        )
        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="TENANT_ACTUALIZADO",
                entidad_afectada="tenants",
                id_entidad=tenant_id,
                valor_anterior=dict(existing),
                valor_nuevo=dict(row),
            )
        return _map_tenant(row)

    async def add_escala(
        self, tenant_id: UUID, payload: EscalaEvaluacionCreate, *, actor_id: UUID
    ) -> dict:
        if await self.repo.get_by_id(tenant_id) is None:
            raise NotFoundError("Tenant no encontrado.")
        try:
            validar_escala_evaluacion(
                minima=payload.nota_minima,
                maxima=payload.nota_maxima,
                aprobatoria=payload.nota_aprobatoria,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        row = await self.repo.create_escala(
            tenant_id,
            nombre_escala=payload.nombre_escala,
            nota_minima=payload.nota_minima,
            nota_maxima=payload.nota_maxima,
            nota_aprobatoria=payload.nota_aprobatoria,
        )
        await self._audit_catalogo(tenant_id, actor_id, "ESCALA_EVALUACION_CREADA", row["id"])
        return dict(row)

    async def list_escalas(self, tenant_id: UUID) -> list[dict]:
        rows = await self.repo.list_escalas(tenant_id)
        return [dict(row) for row in rows]

    async def add_tipo_componente(
        self, tenant_id: UUID, payload: TipoCatalogoCreate, *, actor_id: UUID
    ) -> dict:
        row = await self.repo.create_tipo_componente(
            tenant_id, codigo=payload.codigo, nombre=payload.nombre
        )
        await self._audit_catalogo(tenant_id, actor_id, "TIPO_COMPONENTE_CREADO", row["id"])
        return dict(row)

    async def list_tipos_componente(self, tenant_id: UUID) -> list[dict]:
        return [dict(r) for r in await self.repo.list_tipos_componente(tenant_id)]

    async def add_tipo_condicion(
        self, tenant_id: UUID, payload: TipoCatalogoCreate, *, actor_id: UUID
    ) -> dict:
        row = await self.repo.create_tipo_condicion(
            tenant_id,
            codigo=payload.codigo,
            nombre=payload.nombre,
            descripcion=payload.descripcion,
        )
        await self._audit_catalogo(tenant_id, actor_id, "TIPO_CONDICION_CREADO", row["id"])
        return dict(row)

    async def list_tipos_condicion(self, tenant_id: UUID) -> list[dict]:
        return [dict(r) for r in await self.repo.list_tipos_condicion(tenant_id)]

    async def add_tipo_evento(
        self, tenant_id: UUID, payload: TipoEventoCreate, *, actor_id: UUID
    ) -> dict:
        row = await self.repo.create_tipo_evento(
            tenant_id,
            codigo=payload.codigo,
            nombre=payload.nombre,
            descripcion=payload.descripcion,
            cuenta_objetivo=payload.cuenta_objetivo,
            operacion=payload.operacion,
        )
        await self._audit_catalogo(tenant_id, actor_id, "TIPO_EVENTO_CREADO", row["id"])
        return dict(row)

    async def list_tipos_evento(self, tenant_id: UUID) -> list[dict]:
        return [dict(r) for r in await self.repo.list_tipos_evento(tenant_id)]

    async def _audit_catalogo(
        self, tenant_id: UUID, actor_id: UUID, operacion: str, entidad_id: UUID
    ) -> None:
        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion=operacion,
                entidad_afectada="catalogos",
                id_entidad=entidad_id,
            )
