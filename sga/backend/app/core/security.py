from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    *,
    user_id: UUID,
    rol: str,
    tenant_id: UUID | None,
    expires_minutes: int | None = None,
) -> tuple[str, UUID, datetime]:
    settings = get_settings()
    expire_delta = timedelta(
        minutes=expires_minutes or settings.jwt_access_token_expire_minutes
    )
    expires_at = datetime.now(UTC) + expire_delta
    jti = uuid4()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "rol": rol,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "jti": str(jti),
        "exp": int(expires_at.timestamp()),
        "iat": int(now.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token invalido o expirado.") from exc
