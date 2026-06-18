from functools import lru_cache
from pathlib import Path
from typing import List
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    database_url: str = ""

    database_host: str = ""
    database_port: int = 5432
    database_user: str = "postgres"
    database_password: str = ""
    database_name: str = "postgres"
    supabase_project_ref: str = ""
    supabase_pooler_region: str = "us-west-2"
    supabase_pooler_aws: int = 1
    supabase_pooler_port: int = 5432
    supabase_pooler_host: str = ""
    database_use_pooler: bool = True

    jwt_secret_key: str = "dev-secret-key-change-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    seed_admin_central_email: str = "admin.central@sga.local"
    seed_admin_central_password: str = "AdminCentral123!"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        # Si DATABASE_URL está definido, usarlo tal cual (CI/Docker suelen usar localhost).
        # Solo se construye la URL de Supabase cuando DATABASE_URL no está configurado.
        if self.database_url:
            return self.database_url

        if not self.database_password or not self.supabase_project_ref:
            raise ValueError(
                "Configure DATABASE_PASSWORD y SUPABASE_PROJECT_REF en backend/.env"
            )

        encoded_password = quote_plus(self.database_password)

        if self.database_use_pooler:
            host = self.supabase_pooler_host or (
                f"aws-{self.supabase_pooler_aws}-{self.supabase_pooler_region}.pooler.supabase.com"
            )
            port = self.supabase_pooler_port
            user = f"postgres.{self.supabase_project_ref}"
        else:
            host = self.database_host or f"db.{self.supabase_project_ref}.supabase.co"
            port = self.database_port
            user = self.database_user

        return f"postgresql://{user}:{encoded_password}@{host}:{port}/{self.database_name}"

    @property
    def database_ssl_required(self) -> bool:
        url = self.resolved_database_url.lower()
        return "supabase.co" in url or "pooler.supabase.com" in url


@lru_cache
def get_settings() -> Settings:
    return Settings()
