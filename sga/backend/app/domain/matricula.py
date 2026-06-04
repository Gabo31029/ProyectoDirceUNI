from uuid import UUID


def validar_periodo_en_matricula(estado_periodo: str) -> None:
    if estado_periodo != "MATRICULA":
        raise ValueError(
            f"El periodo academico debe estar en estado MATRICULA. Estado actual: {estado_periodo}."
        )


def validar_matricula_activa(estado_matricula: str) -> None:
    if estado_matricula != "ACTIVA":
        raise ValueError("La matricula no esta activa.")


def validar_seccion_con_vacantes(vacantes_disponibles: int, estado_seccion: str) -> None:
    if estado_seccion != "ABIERTA":
        raise ValueError(f"La seccion no esta abierta. Estado: {estado_seccion}.")
    if vacantes_disponibles <= 0:
        raise ValueError("La seccion no tiene vacantes disponibles.")


def validar_limite_creditos(
    creditos_actuales: int,
    creditos_nuevos: int,
    creditos_maximos: int,
) -> None:
    total = creditos_actuales + creditos_nuevos
    if total > creditos_maximos:
        raise ValueError(
            f"Excede el limite maximo de creditos ({creditos_maximos}). "
            f"Creditos actuales: {creditos_actuales}, creditos del curso: {creditos_nuevos}."
        )


def validar_prerrequisitos_cumplidos(
    requeridos: list[UUID],
    cumplidos: set[UUID],
) -> None:
    faltantes = set(requeridos) - cumplidos
    if faltantes:
        raise ValueError(
            "Prerrequisitos no cumplidos. "
            f"Cursos requeridos pendientes: {sorted(str(c) for c in faltantes)}"
        )


def validar_inscripcion_activa(estado_inscripcion: str) -> None:
    if estado_inscripcion != "ACTIVA":
        raise ValueError("La inscripcion no esta activa.")
