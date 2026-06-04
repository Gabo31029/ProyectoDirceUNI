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
    validar_periodo_en_matricula("MATRICULA")


def test_periodo_en_matricula_invalido() -> None:
    with pytest.raises(ValueError, match="MATRICULA"):
        validar_periodo_en_matricula("CONFIGURACION")


def test_seccion_sin_vacantes() -> None:
    with pytest.raises(ValueError, match="vacantes"):
        validar_seccion_con_vacantes(0, "ABIERTA")


def test_seccion_cerrada() -> None:
    with pytest.raises(ValueError, match="abierta"):
        validar_seccion_con_vacantes(5, "CERRADA")


def test_prerrequisito_no_cumplido() -> None:
    requerido = uuid4()
    with pytest.raises(ValueError, match="Prerrequisitos no cumplidos"):
        validar_prerrequisitos_cumplidos([requerido], set())


def test_prerrequisito_cumplido() -> None:
    requerido = uuid4()
    validar_prerrequisitos_cumplidos([requerido], {requerido})


def test_exceso_creditos() -> None:
    with pytest.raises(ValueError, match="limite maximo"):
        validar_limite_creditos(16, 4, 18)


def test_creditos_dentro_limite() -> None:
    validar_limite_creditos(4, 4, 18)


def test_matricula_inactiva() -> None:
    with pytest.raises(ValueError, match="activa"):
        validar_matricula_activa("RETIRADA")


def test_inscripcion_ya_retirada() -> None:
    with pytest.raises(ValueError, match="activa"):
        validar_inscripcion_activa("RETIRADA")
