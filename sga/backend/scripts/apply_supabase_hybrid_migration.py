#!/usr/bin/env python3
"""Aplica 006_supabase_hybrid_perfil_sync.sql en la BD de .env (Supabase)."""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db" / "migrations" / "006_supabase_hybrid_perfil_sync.sql"


def _load_database_url() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL=") and not line.endswith("="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL no encontrado en backend/.env")


def main() -> None:
    url = _load_database_url()
    if "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    connect_args = {"sslmode": "require"} if "supabase" in url.lower() else {}
    engine = create_engine(url, connect_args=connect_args or None)
    sql = MIGRATION.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))
    print(f"OK — migración aplicada: {MIGRATION.name}")


if __name__ == "__main__":
    main()
