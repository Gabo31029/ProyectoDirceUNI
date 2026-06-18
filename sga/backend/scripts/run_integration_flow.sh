#!/usr/bin/env bash
# Flujo integral de matrícula (equivalente a Thunder 00 + 01).
# Requisito: uvicorn corriendo en http://127.0.0.1:8000
set -euo pipefail

BASE="${BASE_URL:-http://127.0.0.1:8000}"

echo "==> Health"
curl -sf "$BASE/health" | head -c 200
echo ""

echo "==> Login ALUMNO"
LOGIN=$(curl -sf -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alumno@uni-demo.local","password":"AlumnoDemo123!","dominio_tenant":"uni-demo"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token OK"

AUTH="Authorization: Bearer $TOKEN"

echo "==> GET /auth/me"
ME=$(curl -sf "$BASE/api/v1/auth/me" -H "$AUTH")
ALUMNO_ID=$(echo "$ME" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "alumno_id=$ALUMNO_ID"

echo "==> GET periodos"
PERIODOS=$(curl -sf "$BASE/api/v1/periodos" -H "$AUTH")
ID_PERIODO=$(echo "$PERIODOS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'])")
echo "id_periodo=$ID_PERIODO"

echo "==> GET secciones"
SECCIONES=$(curl -sf "$BASE/api/v1/oferta/periodos/$ID_PERIODO/secciones" -H "$AUTH")
ID_SECCION=$(echo "$SECCIONES" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'])")
echo "id_seccion=$ID_SECCION"

echo "==> POST matrícula"
MAT_CODE=$(curl -s -o /tmp/mat.json -w "%{http_code}" -X POST "$BASE/api/v1/matriculas" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"id_periodo\":\"$ID_PERIODO\"}")
if [ "$MAT_CODE" = "201" ]; then
  MATRICULA_ID=$(python3 -c "import json; print(json.load(open('/tmp/mat.json'))['id'])")
elif [ "$MAT_CODE" = "409" ]; then
  echo "Matrícula ya existe, reutilizando..."
  MATRICULA_ID=$(curl -sf "$BASE/api/v1/matriculas?alumno_id=$ALUMNO_ID" -H "$AUTH" | \
    python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
else
  echo "FAIL matrícula HTTP $MAT_CODE"; cat /tmp/mat.json; exit 1
fi
echo "matricula_id=$MATRICULA_ID"

echo "==> POST inscripción"
INS_CODE=$(curl -s -o /tmp/ins.json -w "%{http_code}" -X POST \
  "$BASE/api/v1/matriculas/$MATRICULA_ID/inscripciones" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"id_seccion\":\"$ID_SECCION\"}")
if [ "$INS_CODE" != "201" ]; then
  echo "FAIL inscripción HTTP $INS_CODE"; cat /tmp/ins.json; exit 1
fi
INSCRIPCION_ID=$(python3 -c "import json; print(json.load(open('/tmp/ins.json'))['id'])")
echo "inscripcion_id=$INSCRIPCION_ID"

echo "==> POST retiro"
curl -sf -X POST "$BASE/api/v1/inscripciones/$INSCRIPCION_ID/retiro" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"motivo":"Prueba integral script"}' | head -c 300
echo ""

echo ""
echo "OK — flujo integral completado (Health → Login → Matrícula → Inscripción → Retiro)"
