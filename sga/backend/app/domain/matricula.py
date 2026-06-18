from uuid import UUID

# =============================================================================
# REGLAS DE NEGOCIO PURAS (DOMINIO) - SIN DEPENDENCIAS DE BD NI FRAMEWORKS
# =============================================================================

def validar_periodo_en_matricula(estado_periodo: str) -> None:
    """
    Valida que el período académico se encuentre en fase de matrícula.
    Si el período está en configuración, registro de notas o cerrado, no se permite matricularse.
    """
    if estado_periodo != "MATRICULA":
        raise ValueError(
            f"El periodo academico debe estar en estado MATRICULA. Estado actual: {estado_periodo}."
        )


def validar_matricula_activa(estado_matricula: str) -> None:
    """
    Verifica que la matrícula del estudiante esté activa.
    No se permiten inscripciones si la matrícula fue retirada o finalizada.
    """
    if estado_matricula != "ACTIVA":
        raise ValueError("La matricula no esta activa.")


def validar_seccion_con_vacantes(vacantes_disponibles: int, estado_seccion: str) -> None:
    """
    Verifica que la sección seleccionada esté abierta para matrícula y tenga vacantes libres.
    """
    if estado_seccion != "ABIERTA":
        raise ValueError(f"La seccion no esta abierta. Estado: {estado_seccion}.")
    if vacantes_disponibles <= 0:
        raise ValueError("La seccion no tiene vacantes disponibles.")


def validar_limite_creditos(
    creditos_actuales: int,
    creditos_nuevos: int,
    creditos_maximos: int,
) -> None:
    """
    Verifica que el estudiante no exceda la cantidad máxima de créditos permitidos para el período.
    """
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
    """
    Verifica que el estudiante haya aprobado todos los prerrequisitos obligatorios de la asignatura.
    """
    faltantes = set(requeridos) - cumplidos
    if faltantes:
        raise ValueError(
            "Prerrequisitos no cumplidos. "
            f"Cursos requeridos pendientes: {sorted(str(c) for c in faltantes)}"
        )


def validar_inscripcion_activa(estado_inscripcion: str) -> None:
    """
    Verifica que una inscripción específica a un curso se encuentre activa.
    Requerido antes de procesar retiros voluntarios de asignaturas.
    """
    if estado_inscripcion != "ACTIVA":
        raise ValueError("La inscripcion no esta activa.")
