#!/usr/bin/env bash
# Pruebas de integración automatizadas (pytest + TestClient).
# No requiere Docker si backend/.env tiene DATABASE_URL (Supabase).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "ERROR: no existe .venv. Crea el entorno:"
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export TEST_DATABASE_URL="${TEST_DATABASE_URL:-${DATABASE_URL:-}}"
export ENVIRONMENT=testing

echo "==> BD de pruebas: ${TEST_DATABASE_URL:-postgresql://sga:sga_dev@127.0.0.1:5432/sga}"
echo "==> Limpia solo el tenant de prueba f1111111-... (no borra uni-demo del equipo)."
echo "==> Supabase híbrido (sin Docker): la 1.ª ejecución aplica migración 006 automáticamente."
echo ""

.venv/bin/pytest tests/integration/test_matricula_integration.py -v -m integration "$@"
