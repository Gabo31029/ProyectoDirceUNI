from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest

from app.domain.periodo import validar_fechas_periodo, validar_transicion_estado_periodo
from app.domain.oferta import validar_prerrequisitos, validar_suma_pesos_componentes, validar_edicion_seccion
from app.models.schemas import PeriodoEstado


def test_validar_fechas_periodo_ok() -> None:
    fecha_inicio = date(2026, 3, 1)
    fecha_fin = date(2026, 7, 15)
    # No debería lanzar excepciones
    validar_fechas_periodo(fecha_inicio, fecha_fin)


def test_validar_fechas_periodo_invalido() -> None:
    fecha_inicio = date(2026, 7, 15)
    fecha_fin = date(2026, 3, 1)
    with pytest.raises(ValueError, match="La fecha de inicio debe ser anterior a la fecha de fin."):
        validar_fechas_periodo(fecha_inicio, fecha_fin)


def test_validar_transicion_estado_periodo_ok() -> None:
    # CONFIGURACION -> MATRICULA
    validar_transicion_estado_periodo("CONFIGURACION", "MATRICULA")
    # MATRICULA -> REGISTRO_NOTAS
    validar_transicion_estado_periodo("MATRICULA", "REGISTRO_NOTAS")
    # REGISTRO_NOTAS -> CERRADO
    validar_transicion_estado_periodo("REGISTRO_NOTAS", "CERRADO")


def test_validar_transicion_estado_periodo_retroceder() -> None:
    with pytest.raises(ValueError, match="Transición no permitida"):
        validar_transicion_estado_periodo("MATRICULA", "CONFIGURACION")


def test_validar_transicion_estado_periodo_saltar() -> None:
    with pytest.raises(ValueError, match="Transición no permitida"):
        validar_transicion_estado_periodo("CONFIGURACION", "REGISTRO_NOTAS")


def test_validar_prerrequisitos_curso_ok() -> None:
    curso_req = uuid4()
    # No debería lanzar excepciones
    validar_prerrequisitos("APROBACION_CURSO", curso_req, None)


def test_validar_prerrequisitos_curso_invalido() -> None:
    with pytest.raises(ValueError, match="se debe especificar el curso requerido"):
        validar_prerrequisitos("APROBACION_CURSO", None, None)


def test_validar_prerrequisitos_creditos_ok() -> None:
    # No debería lanzar excepciones
    validar_prerrequisitos("MINIMO_CREDITOS", None, 120)


def test_validar_prerrequisitos_creditos_invalido() -> None:
    with pytest.raises(ValueError, match="se debe especificar un valor mayor a cero"):
        validar_prerrequisitos("MINIMO_CREDITOS", None, 0)
    with pytest.raises(ValueError, match="se debe especificar un valor mayor a cero"):
        validar_prerrequisitos("MINIMO_CREDITOS", None, None)


def test_validar_suma_pesos_componentes_ok() -> None:
    existentes = [Decimal("30.00"), Decimal("40.00")]
    # 30 + 40 + 30 = 100 (válido, no excede 100)
    validar_suma_pesos_componentes(existentes, Decimal("30.00"))


def test_validar_suma_pesos_componentes_excedido() -> None:
    existentes = [Decimal("30.00"), Decimal("40.00")]
    with pytest.raises(ValueError, match="La suma de pesos supera el 100% permitido"):
        # 30 + 40 + 31 = 101 (inválido)
        validar_suma_pesos_componentes(existentes, Decimal("31.00"))


def test_validar_edicion_seccion_ok() -> None:
    # No debería lanzar excepciones
    validar_edicion_seccion(PeriodoEstado.CONFIGURACION.value)


def test_validar_edicion_seccion_invalida() -> None:
    with pytest.raises(ValueError, match="No se pueden crear ni modificar secciones"):
        validar_edicion_seccion(PeriodoEstado.MATRICULA.value)
