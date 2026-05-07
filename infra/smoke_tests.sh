#!/usr/bin/env bash
# infra/smoke_tests.sh · SMT-ONIC validación post-deploy
# =====================================================
# Ejecuta los 7 smoke tests del DEPLOY_PRODUCCION.md §4.
# Exit code 0 si todos verdes · 1 si algún fallo.
#
# Uso:
#   ./infra/smoke_tests.sh                        # local (http://localhost:8095)
#   ./infra/smoke_tests.sh https://smt-onic.com   # producción
#   API_URL=https://staging.smt-onic.com ./infra/smoke_tests.sh
#
# Pre-requisitos: curl + python3 (jq ya no es requerido).

set -uo pipefail

# Configuración
API_URL="${1:-${API_URL:-http://localhost:8095}}"
TEST_USER="${TEST_USER:-wilson}"
TEST_PASSWORD_FILE="${TEST_PASSWORD_FILE:-backend/.seed_credentials.txt}"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

ok()   { echo -e "${GREEN}✓ PASS${NC} · $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}✗ FAIL${NC} · $1"; FAIL=$((FAIL + 1)); }
warn() { echo -e "${YELLOW}⚠ WARN${NC} · $1"; WARN=$((WARN + 1)); }

# Helper: extraer un campo JSON con Python (reemplazo de jq)
# Uso: jget '<json-string>' '<dotted-path>'  → imprime valor o vacío
jget() {
  python -c "
import json, sys
try:
    data = json.loads(sys.argv[1])
    for key in sys.argv[2].split('.'):
        if key.endswith(']'):
            base, idx = key[:-1].split('[')
            data = data[base][int(idx)] if base else data[int(idx)]
        elif data is None:
            print('')
            sys.exit(0)
        else:
            data = data.get(key) if isinstance(data, dict) else None
    if data is None:
        print('')
    elif isinstance(data, (dict, list)):
        print(json.dumps(data, ensure_ascii=False))
    else:
        print(data)
except Exception as e:
    print('', end='')
" "$1" "$2"
}

echo "=================================================="
echo "SMT-ONIC · smoke tests · $API_URL"
echo "Fecha: $(date -Iseconds)"
echo "=================================================="

# ---------------------------------------------------------------------------
# Test 1 · Health endpoint (no requiere auth)
# Acepta shape mínimo {"status":"ok"} y shape extendido con table counts.
# ---------------------------------------------------------------------------
echo ""
echo "[1/7] Health endpoint..."
HEALTH=$(curl -fsS "$API_URL/api/v1/health" 2>&1) && {
  STATUS=$(jget "$HEALTH" "status")
  if [[ "$STATUS" == "ok" ]]; then
    DB_OK=$(jget "$HEALTH" "db.ok")
    if [[ "$DB_OK" == "True" || "$DB_OK" == "true" || -z "$DB_OK" ]]; then
      ok "/api/v1/health responde 200 con status=ok"
    else
      fail "/api/v1/health status=ok pero db.ok=$DB_OK"
    fi
  else
    fail "/api/v1/health status='$STATUS' (esperado 'ok'). Respuesta: ${HEALTH:0:200}"
  fi
} || fail "/api/v1/health no responde"

# ---------------------------------------------------------------------------
# Test 2 · Login + obtener token JWT
# Formato esperado del .seed_credentials.txt (cualquiera de los dos):
#   - "<usuario>:<password>" (legacy)
#   - "USERNAME=<usuario>" + "PASSWORD=<password>" (canónico)
# ---------------------------------------------------------------------------
echo ""
echo "[2/7] Login y obtener token JWT..."
TOKEN=""
if [[ ! -f "$TEST_PASSWORD_FILE" ]]; then
  warn "No se encontró $TEST_PASSWORD_FILE · saltando tests autenticados"
else
  # Intento canónico KEY=VALUE
  TEST_PASSWORD=$(grep -E "^PASSWORD=" "$TEST_PASSWORD_FILE" | cut -d'=' -f2-)
  USER_FROM_FILE=$(grep -E "^USERNAME=" "$TEST_PASSWORD_FILE" | cut -d'=' -f2-)
  [[ -n "$USER_FROM_FILE" ]] && TEST_USER="$USER_FROM_FILE"
  # Fallback formato legacy "user:pass"
  if [[ -z "$TEST_PASSWORD" ]]; then
    TEST_PASSWORD=$(grep -E "^${TEST_USER}:" "$TEST_PASSWORD_FILE" | cut -d':' -f2)
  fi
  if [[ -z "$TEST_PASSWORD" ]]; then
    warn "No se encontró password para $TEST_USER en $TEST_PASSWORD_FILE"
  else
    LOGIN_RESP=$(curl -fsS -X POST "$API_URL/api/v1/auth/login" \
      -H 'Content-Type: application/json' \
      -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASSWORD\"}" 2>&1) || LOGIN_RESP=""
    TOKEN=$(jget "$LOGIN_RESP" "access_token")
    [[ -z "$TOKEN" ]] && TOKEN=$(jget "$LOGIN_RESP" "token")
    if [[ -n "$TOKEN" ]]; then
      ok "Login exitoso · token obtenido (${#TOKEN} chars)"
    else
      fail "Login falló: ${LOGIN_RESP:0:200}"
    fi
  fi
fi

auth_curl() {
  [[ -z "$TOKEN" ]] && return 1
  curl -fsS -H "Authorization: Bearer $TOKEN" "$@"
}

# ---------------------------------------------------------------------------
# Test 3 · /proyecciones (T08) · debe retornar filas
# ---------------------------------------------------------------------------
echo ""
echo "[3/7] Endpoint /proyecciones..."
PROY=$(curl -fsS "$API_URL/api/v1/dashboard/proyecciones?grupo_etnico=Indigena" 2>&1) && {
  TOTAL=$(jget "$PROY" "total")
  if [[ -z "$TOTAL" || "$TOTAL" == "0" ]]; then
    DATA=$(jget "$PROY" "data")
    [[ -n "$DATA" && "$DATA" != "[]" ]] && TOTAL="?>0"
  fi
  if [[ "$TOTAL" == "?>0" ]] || [[ -n "$TOTAL" && "$TOTAL" =~ ^[0-9]+$ && "$TOTAL" -gt 0 ]]; then
    ok "/proyecciones retorna $TOTAL filas"
  else
    fail "/proyecciones retorna sin datos (total=$TOTAL) · ¿se aplicó seed 004?"
  fi
} || fail "/proyecciones no responde"

# ---------------------------------------------------------------------------
# Test 4 · /intercensal con FAC (T02)
# ---------------------------------------------------------------------------
echo ""
echo "[4/7] Endpoint /intercensal con aplicar_fac=true..."
INTER=$(curl -fsS "$API_URL/api/v1/dashboard/intercensal?grupo_etnico=Indigena&aplicar_fac=true" 2>&1) && {
  FAC_OK=$(jget "$INTER" "fac_aplicado")
  if [[ "$FAC_OK" == "True" || "$FAC_OK" == "true" ]]; then
    ok "/intercensal aplica FAC correctamente"
  else
    warn "/intercensal responde pero fac_aplicado=$FAC_OK · ¿tabla proyecciones.fac vacía?"
  fi
} || fail "/intercensal no responde"

# ---------------------------------------------------------------------------
# Test 5 · /brecha con sources detallados (T06)
# ---------------------------------------------------------------------------
echo ""
echo "[5/7] Endpoint /brecha con source_detalle..."
BRECHA=$(curl -fsS "$API_URL/api/v1/dashboard/brecha" 2>&1) && {
  HAS_DETAIL=$(jget "$BRECHA" "pasos.[0].source_detalle")
  if [[ -n "$HAS_DETAIL" && "$HAS_DETAIL" != "null" && "$HAS_DETAIL" != "{}" ]]; then
    ok "/brecha incluye source_detalle en steps"
  else
    fail "/brecha no incluye source_detalle"
  fi
} || fail "/brecha no responde"

# ---------------------------------------------------------------------------
# Test 6 · Auth · /pueblos sin token = 401
# ---------------------------------------------------------------------------
echo ""
echo "[6/7] Auth: /pueblos/ sin token debe retornar 401..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/pueblos/")
if [[ "$STATUS" == "401" ]]; then
  ok "/pueblos/ correctamente retorna 401 sin token"
elif [[ "$STATUS" == "200" ]]; then
  fail "/pueblos/ retorna 200 sin token · auth NO aplicada"
else
  fail "/pueblos/ retorna $STATUS (esperado 401)"
fi

# ---------------------------------------------------------------------------
# Test 7 · Auth · /pueblos con token = 200
# ---------------------------------------------------------------------------
echo ""
echo "[7/7] Auth: /pueblos/ con token debe retornar 200..."
if [[ -n "$TOKEN" ]]; then
  PUEBLOS=$(auth_curl "$API_URL/api/v1/pueblos/") && {
    TOTAL=$(jget "$PUEBLOS" "total")
    if [[ -z "$TOTAL" ]]; then
      DATA_LEN=$(python -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    if isinstance(d, list):
        print(len(d))
    elif isinstance(d, dict):
        for k in ['data','items','pueblos']:
            if k in d and isinstance(d[k], list):
                print(len(d[k])); break
        else:
            print(0)
except Exception:
    print(0)
" "$PUEBLOS")
      TOTAL="$DATA_LEN"
    fi
    if [[ -n "$TOTAL" && "$TOTAL" =~ ^[0-9]+$ && "$TOTAL" -gt 0 ]]; then
      ok "/pueblos/ con token retorna $TOTAL pueblos"
    else
      warn "/pueblos/ con token responde pero shape inesperado · TOTAL=$TOTAL"
    fi
  } || fail "/pueblos/ con token falla"
else
  warn "Saltado · no hay token disponible"
fi

# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------
echo ""
echo "=================================================="
echo "RESUMEN · $PASS pass · $FAIL fail · $WARN warn"
echo "=================================================="

if [[ "$FAIL" -gt 0 ]]; then
  echo -e "${RED}DEPLOY NO VÁLIDO · $FAIL tests fallaron · ver §7 rollback de DEPLOY_PRODUCCION.md${NC}"
  exit 1
elif [[ "$WARN" -gt 0 ]]; then
  echo -e "${YELLOW}DEPLOY VÁLIDO CON ADVERTENCIAS · revisar warnings antes de anunciar${NC}"
  exit 0
else
  echo -e "${GREEN}DEPLOY VÁLIDO · todos los smoke tests verdes · seguro para go-live${NC}"
  exit 0
fi
