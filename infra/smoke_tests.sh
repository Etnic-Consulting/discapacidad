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
# Pre-requisitos: curl, jq, docker (para login fixture).
# Generado por Sprint S2.D03 · 2026-05-02

set -uo pipefail

# Configuración
API_URL="${1:-${API_URL:-http://localhost:8095}}"
TEST_USER="${TEST_USER:-wilson}"
TEST_PASSWORD_FILE="${TEST_PASSWORD_FILE:-backend/.seed_credentials.txt}"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contadores
PASS=0
FAIL=0
WARN=0

ok() {
  echo -e "${GREEN}✓ PASS${NC} · $1"
  PASS=$((PASS + 1))
}

fail() {
  echo -e "${RED}✗ FAIL${NC} · $1"
  FAIL=$((FAIL + 1))
}

warn() {
  echo -e "${YELLOW}⚠ WARN${NC} · $1"
  WARN=$((WARN + 1))
}

echo "=================================================="
echo "SMT-ONIC · smoke tests · $API_URL"
echo "Fecha: $(date -Iseconds)"
echo "=================================================="

# Test 1 · Health endpoint (no requiere auth)
echo ""
echo "[1/7] Health endpoint..."
HEALTH=$(curl -fsS "$API_URL/api/v1/health" 2>&1) && {
  if echo "$HEALTH" | jq -e '.status == "ok"' > /dev/null 2>&1; then
    ok "/api/v1/health responde 200 con status=ok"
  else
    fail "/api/v1/health responde 200 pero shape inesperado: $HEALTH"
  fi
} || fail "/api/v1/health no responde"

# Test 2 · Login + obtener token
echo ""
echo "[2/7] Login y obtener token JWT..."
if [[ ! -f "$TEST_PASSWORD_FILE" ]]; then
  warn "No se encontró $TEST_PASSWORD_FILE · saltando tests autenticados (5 restantes)"
  TOKEN=""
else
  TEST_PASSWORD=$(grep -E "^${TEST_USER}:" "$TEST_PASSWORD_FILE" | cut -d':' -f2)
  if [[ -z "$TEST_PASSWORD" ]]; then
    warn "No se encontró password para $TEST_USER en $TEST_PASSWORD_FILE"
    TOKEN=""
  else
    LOGIN_RESP=$(curl -fsS -X POST "$API_URL/api/v1/auth/login" \
      -H 'Content-Type: application/json' \
      -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASSWORD\"}" 2>&1)
    TOKEN=$(echo "$LOGIN_RESP" | jq -r '.access_token // empty' 2>/dev/null)
    if [[ -n "$TOKEN" && "$TOKEN" != "null" ]]; then
      ok "Login exitoso · token obtenido (${#TOKEN} chars)"
    else
      fail "Login falló: $LOGIN_RESP"
      TOKEN=""
    fi
  fi
fi

# Helper para llamadas autenticadas
auth_curl() {
  if [[ -z "$TOKEN" ]]; then
    return 1
  fi
  curl -fsS -H "Authorization: Bearer $TOKEN" "$@"
}

# Test 3 · Endpoint nuevo · /proyecciones (T08)
echo ""
echo "[3/7] Endpoint /proyecciones (T08 nuevo)..."
PROY=$(curl -fsS "$API_URL/api/v1/dashboard/proyecciones?grupo_etnico=Indigena" 2>&1) && {
  TOTAL=$(echo "$PROY" | jq -r '.total // 0')
  if [[ "$TOTAL" -gt 0 ]]; then
    ok "/proyecciones retorna $TOTAL filas (esperado >0 · idealmente 104 = 4 escenarios × 26 años)"
  else
    fail "/proyecciones retorna total=0 · ¿se aplicó seed 004?"
  fi
} || fail "/proyecciones no responde"

# Test 4 · Endpoint extendido · /intercensal con FAC (T02)
echo ""
echo "[4/7] Endpoint /intercensal con aplicar_fac=true (T02 patch)..."
INTER=$(curl -fsS "$API_URL/api/v1/dashboard/intercensal?grupo_etnico=Indigena&aplicar_fac=true" 2>&1) && {
  FAC_OK=$(echo "$INTER" | jq -r '.fac_aplicado // false')
  if [[ "$FAC_OK" == "true" ]]; then
    ok "/intercensal aplica FAC correctamente"
  else
    warn "/intercensal responde pero fac_aplicado=false · ¿tabla proyecciones.fac vacía?"
  fi
} || fail "/intercensal no responde"

# Test 5 · Endpoint extendido · /brecha con sources (T06)
echo ""
echo "[5/7] Endpoint /brecha con source_detalle (T06 patch)..."
BRECHA=$(curl -fsS "$API_URL/api/v1/dashboard/brecha" 2>&1) && {
  HAS_DETAIL=$(echo "$BRECHA" | jq -r '.pasos[0].source_detalle.cita // empty' 2>/dev/null)
  if [[ -n "$HAS_DETAIL" ]]; then
    ok "/brecha incluye source_detalle.cita en steps"
  else
    fail "/brecha no incluye source_detalle · patch T06 no aplicado?"
  fi
} || fail "/brecha no responde"

# Test 6 · Auth aplicada · pueblos sin token debe ser 401 (T24)
echo ""
echo "[6/7] Auth: /pueblos/ sin token debe retornar 401 (T24)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/pueblos/")
if [[ "$STATUS" == "401" ]]; then
  ok "/pueblos/ correctamente retorna 401 sin token"
elif [[ "$STATUS" == "200" ]]; then
  fail "/pueblos/ retorna 200 sin token · auth NO aplicada · T24 sin efecto"
else
  fail "/pueblos/ retorna $STATUS (esperado 401)"
fi

# Test 7 · Auth aplicada · pueblos CON token debe ser 200
echo ""
echo "[7/7] Auth: /pueblos/ con token debe retornar 200..."
if [[ -n "$TOKEN" ]]; then
  PUEBLOS=$(auth_curl "$API_URL/api/v1/pueblos/") && {
    PUEBLOS_TOTAL=$(echo "$PUEBLOS" | jq -r '.total // .data | length' 2>/dev/null)
    if [[ -n "$PUEBLOS_TOTAL" ]] && [[ "$PUEBLOS_TOTAL" -gt 0 ]]; then
      ok "/pueblos/ con token retorna $PUEBLOS_TOTAL pueblos"
    else
      warn "/pueblos/ con token retorna 200 pero shape inesperado"
    fi
  } || fail "/pueblos/ con token falla"
else
  warn "Saltado · no hay token (login falló o credenciales no disponibles)"
fi

# Resumen
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
