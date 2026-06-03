from fastapi import APIRouter, Depends, Header, status

from app.core.database import db
from app.core.dependencies import CurrentUser, get_current_user
from app.core.security import decode_access_token
from app.models.schemas import LoginRequest, TokenResponse, UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


def _auth_service() -> AuthService:
    return AuthService(db.connection())


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    return await _auth_service().login(payload)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: CurrentUser = Depends(get_current_user),
    authorization: str | None = Header(default=None),
) -> None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    await _auth_service().logout(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        jti=current_user.jti,
        exp=int(payload["exp"]),
    )


@router.get("/me", response_model=UserPublic)
async def me(current_user: CurrentUser = Depends(get_current_user)) -> UserPublic:
    return await _auth_service().get_me(current_user.id)
