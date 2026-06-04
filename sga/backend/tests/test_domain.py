import pytest

from app.domain.auth import calcular_bloqueo, cuenta_bloqueada
from app.domain.tenant import validar_dominio_tenant
from app.domain.users import validar_escala_evaluacion, validar_rol_usuario_creacion


def test_validar_dominio_tenant_ok() -> None:
    validar_dominio_tenant("uni-demo")


def test_validar_dominio_tenant_invalido() -> None:
    with pytest.raises(ValueError):
        validar_dominio_tenant("Uni_Demo")


def test_validar_escala_evaluacion_ok() -> None:
    validar_escala_evaluacion(minima=0, maxima=20, aprobatoria=11)


def test_validar_escala_evaluacion_invalida() -> None:
    with pytest.raises(ValueError):
        validar_escala_evaluacion(minima=0, maxima=20, aprobatoria=25)


def test_admin_no_puede_crear_admin_central() -> None:
    with pytest.raises(ValueError):
        validar_rol_usuario_creacion(rol_creador="ADMIN", rol_nuevo="ADMIN_CENTRAL")


def test_cuenta_bloqueada_falso_si_no_hay_fecha() -> None:
    assert cuenta_bloqueada(None) is False


def test_calcular_bloqueo_por_intentos() -> None:
    bloqueo = calcular_bloqueo(5)
    assert bloqueo is not None
