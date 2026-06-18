from enum import Enum


class RolUsuario(str, Enum):
    ADMIN_CENTRAL = "ADMIN_CENTRAL"
    ADMIN = "ADMIN"
    DOCENTE = "DOCENTE"
    ALUMNO = "ALUMNO"


ROLES_INSTITUCIONALES = {RolUsuario.ADMIN, RolUsuario.DOCENTE, RolUsuario.ALUMNO}


def validar_login_contexto(*, rol: str, tenant_id_presente: bool, dominio_presente: bool) -> None:
    if rol == RolUsuario.ADMIN_CENTRAL.value:
        if dominio_presente:
            raise ValueError("El Administrador Central no requiere dominio de tenant.")
        return

    if not dominio_presente:
        raise ValueError("Debe indicar el dominio del tenant para iniciar sesion.")
    if not tenant_id_presente:
        raise ValueError("Tenant invalido o inactivo.")


def validar_rol_usuario_creacion(*, rol_creador: str, rol_nuevo: str) -> None:
    if rol_creador == RolUsuario.ADMIN_CENTRAL.value:
        if rol_nuevo == RolUsuario.ADMIN_CENTRAL.value:
            raise ValueError("No puede crear otro Administrador Central desde esta API.")
        return

    if rol_creador != RolUsuario.ADMIN.value:
        raise ValueError("Solo un Administrador puede gestionar usuarios del tenant.")

    if rol_nuevo in {RolUsuario.ADMIN_CENTRAL.value, RolUsuario.ADMIN.value}:
        raise ValueError("Un Administrador institucional no puede crear usuarios con ese rol.")


def validar_escala_evaluacion(*, minima: float, maxima: float, aprobatoria: float) -> None:
    if minima > aprobatoria or aprobatoria > maxima:
        raise ValueError(
            "La escala debe cumplir: nota_minima <= nota_aprobatoria <= nota_maxima."
        )
