from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import get_settings


def cuenta_bloqueada(bloqueado_hasta: datetime | None) -> bool:
    if bloqueado_hasta is None:
        return False
    return bloqueado_hasta.replace(tzinfo=UTC) > datetime.now(UTC)


def calcular_bloqueo(intentos_fallidos: int) -> datetime | None:
    settings = get_settings()
    if intentos_fallidos < settings.max_login_attempts:
        return None
    return datetime.now(UTC) + timedelta(minutes=settings.login_lockout_minutes)
