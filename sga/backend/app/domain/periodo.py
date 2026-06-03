from datetime import date
from app.models.schemas import PeriodoEstado


def validar_fechas_periodo(fecha_inicio: date, fecha_fin: date) -> None:
    if fecha_inicio >= fecha_fin:
        raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin.")


def validar_transicion_estado_periodo(estado_actual: str, estado_nuevo: str) -> None:
    # CONFIGURACION -> MATRICULA -> REGISTRO_NOTAS -> CERRADO
    secuencia = [
        PeriodoEstado.CONFIGURACION.value,
        PeriodoEstado.MATRICULA.value,
        PeriodoEstado.REGISTRO_NOTAS.value,
        PeriodoEstado.CERRADO.value,
    ]

    if estado_actual not in secuencia:
        raise ValueError(f"Estado actual inválido: {estado_actual}")
    if estado_nuevo not in secuencia:
        raise ValueError(f"Estado nuevo inválido: {estado_nuevo}")

    idx_actual = secuencia.index(estado_actual)
    idx_nuevo = secuencia.index(estado_nuevo)

    if idx_nuevo != idx_actual + 1:
        raise ValueError(
            f"Transición no permitida: de {estado_actual} a {estado_nuevo}. "
            "La secuencia debe ser: CONFIGURACION -> MATRICULA -> REGISTRO_NOTAS -> CERRADO."
        )
