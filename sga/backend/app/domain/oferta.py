from uuid import UUID
from decimal import Decimal
from app.models.schemas import PeriodoEstado


def validar_prerrequisitos(
    tipo_prereq: str,
    id_curso_requerido: UUID | None,
    valor_min_creditos: int | None,
) -> None:
    if tipo_prereq == "APROBACION_CURSO":
        if id_curso_requerido is None:
            raise ValueError(
                "Para el prerrequisito de tipo APROBACION_CURSO se debe especificar el curso requerido."
            )
    elif tipo_prereq == "MINIMO_CREDITOS":
        if valor_min_creditos is None or valor_min_creditos <= 0:
            raise ValueError(
                "Para el prerrequisito de tipo MINIMO_CREDITOS se debe especificar un valor mayor a cero."
            )
    else:
        raise ValueError(f"Tipo de prerrequisito desconocido: {tipo_prereq}")


def validar_suma_pesos_evaluaciones(pesos_existentes: list[Decimal], nuevo_peso: Decimal) -> None:
    suma = sum(pesos_existentes) + nuevo_peso
    if suma > Decimal("100.00"):
        raise ValueError(
            f"La suma de pesos supera el 100% permitido. Suma acumulada solicitada: {suma}%"
        )


def validar_edicion_seccion(estado_periodo: str) -> None:
    if estado_periodo != PeriodoEstado.CONFIGURACION.value:
        raise ValueError(
            f"No se pueden crear ni modificar secciones cuando el periodo está en estado {estado_periodo}. "
            "Debe estar en CONFIGURACION."
        )
