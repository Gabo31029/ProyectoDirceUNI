from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

from app.core.config import get_settings


class Database:
    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        settings = get_settings()
        pool_kwargs: dict = {"min_size": 1, "max_size": 10}
        if settings.database_ssl_required:
            pool_kwargs["ssl"] = "require"
        if settings.database_use_pooler:
            pool_kwargs["statement_cache_size"] = 0
        self.pool = await asyncpg.create_pool(
            dsn=settings.resolved_database_url,
            **pool_kwargs,
        )

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    def connection(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("Pool de base de datos no inicializado.")
        return self.pool


db = Database()


@asynccontextmanager
async def lifespan(_: object) -> AsyncIterator[None]:
    await db.connect()
    from app.db.seed import run_seed

    await run_seed(db.connection())
    yield
    await db.disconnect()
