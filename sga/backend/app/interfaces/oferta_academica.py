from uuid import UUID

import asyncpg


class OfertaAcademicaInterface:
    """
    Contrato para el modulo de Oferta Academica (Ramos Jacay).
    RF-USR-04 consulta evaluaciones activas al desactivar un docente.
    """

    async def obtener_evaluaciones_activas_docente(
        self,
        conn: asyncpg.Connection,
        *,
        id_tenant: UUID,
        docente_id: UUID,
    ) -> list[dict]:
        raise NotImplementedError(
            "Implementar en modulo Oferta Academica (feature/oferta-academica)."
        )


class OfertaAcademicaStub(OfertaAcademicaInterface):
    """Stub temporal hasta que Oferta Academica este disponible."""

    async def obtener_evaluaciones_activas_docente(
        self,
        conn: asyncpg.Connection,
        *,
        id_tenant: UUID,
        docente_id: UUID,
    ) -> list[dict]:
        return []
