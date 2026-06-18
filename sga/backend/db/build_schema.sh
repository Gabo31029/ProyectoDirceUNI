#!/usr/bin/env bash
# Regenera schema.sql concatenando db/migrations/[0-9]*.sql en orden.
set -euo pipefail
cd "$(dirname "$0")"
OUT=schema.sql
{
  echo "-- ============================================================================="
  echo "-- GENERADO por ./db/build_schema.sh — no editar schema.sql a mano."
  echo "-- Fuente: db/migrations/*.sql — ver db/README.md"
  echo "-- ============================================================================="
  echo ""
  for f in migrations/[0-9]*.sql; do
    cat "$f"
    echo ""
  done
} > "$OUT"
echo "OK: $OUT ($(wc -l < "$OUT" | tr -d ' ') líneas)"
