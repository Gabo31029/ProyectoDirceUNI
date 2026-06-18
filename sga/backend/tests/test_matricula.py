"""
Pruebas unitarias para las reglas de negocio puras (dominio) del módulo de Matrícula.

Verifican el comportamiento lógico aislado de base de datos o frameworks para asegurar
el cumplimiento de políticas académicas (periodos, vacantes, créditos, prerrequisitos).
"""

from uuid import uuid4

import pytest

from app.domain.matricula import (
    validar_inscripcion_activa,
    validar_limite_creditos,
    validar_matricula_activa,
    validar_periodo_en_matricula,
    validar_prerrequisitos_cumplidos,
    validar_seccion_con_vacantes,
)


def test_periodo_en_matricula_ok() -> None:
    """Valida que un periodo académico en estado 'MATRICULA' pase correctamente la validación."""
    validar_periodo_en_matricula("MATRICULA")


def test_periodo_en_matricula_invalido() -> None:
    """Valida que un periodo en un estado diferente de 'MATRICULA' lance un error ValueError."""
    with pytest.raises(ValueError, match="MATRICULA"):
        validar_periodo_en_matricula("CONFIGURACION")


def test_seccion_sin_vacantes() -> None:
    """Valida que intentar inscribir en una sección con 0 vacantes lance un error de validación."""
    with pytest.raises(ValueError, match="vacantes"):
        validar_seccion_con_vacantes(0, "ABIERTA")


def test_seccion_cerrada() -> None:
    """Valida que intentar inscribir en una sección que no está 'ABIERTA' lance un error."""
    with pytest.raises(ValueError, match="abierta"):
        validar_seccion_con_vacantes(5, "CERRADA")


def test_prerrequisito_no_cumplido() -> None:
    """Valida que no se permita la inscripción si el alumno no cuenta con los cursos prerrequisitos aprobados."""
    requerido = uuid4()
    with pytest.raises(ValueError, match="Prerrequisitos no cumplidos"):
        validar_prerrequisitos_cumplidos([requerido], set())


def test_prerrequisito_cumplido() -> None:
    """Valida que se apruebe la validación cuando el alumno ha aprobado todos los cursos requeridos."""
    requerido = uuid4()
    validar_prerrequisitos_cumplidos([requerido], {requerido})


def test_exceso_creditos() -> None:
    """Valida que se lance un error si el total de créditos acumulados en el periodo supera el límite permitido."""
    with pytest.raises(ValueError, match="limite maximo"):
        validar_limite_creditos(16, 4, 18)


def test_creditos_dentro_limite() -> None:
    """Valida que se apruebe la validación si el total de créditos del periodo está dentro de los límites permitidos."""
    validar_limite_creditos(4, 4, 18)


def test_matricula_inactiva() -> None:
    """Valida que se rechace la operación si el estado de la matrícula del alumno no es 'ACTIVA'."""
    with pytest.raises(ValueError, match="activa"):
        validar_matricula_activa("RETIRADA")


def test_inscripcion_ya_retirada() -> None:
    """Valida que se rechace la operación sobre inscripciones cuyo estado sea diferente de 'ACTIVA'."""
    with pytest.raises(ValueError, match="activa"):
        validar_inscripcion_activa("RETIRADA")

