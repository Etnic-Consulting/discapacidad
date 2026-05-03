#!/usr/bin/env bash
# infra/init_db.sh · SMT-ONIC primer deploy · carga inicial DB
# =============================================================
# Ejecuta UNA SOLA VEZ tras el primer `docker compose up -d db`.
# Idempotente · safe to re-run (los seeds tienen TRUNCATE/DELETE previo).
#
# Pasos (en orden):
#   1. Verifica DB healthy
#   2. Descarga bd_consolidada.tar.gz desde URL_DATA (S3/GCS/Drive)
#   3. Verifica SHA256 checksum
#   4. Descomprime a $DISCAPACIDAD_DIR
#   5. Aplica seeds 003+004+005 (FAC + proyecciones + indicadores)
#   6. Ejecuta load_all.py para cargar CNPV completo (~15-30 min)
#   7. Verifica counts post-carga
#   8. Reporta status
#
# Generado por Sprint S2.D02 · 2026-05-02

set -euo pipefail

# Configuración
URL_DATA="${URL_DATA:?URL_DATA requerido · ej: https://drive.google.com/.../bd_consolidada.tar.gz}"
EXPECTED_SHA256="${EXPECTED_SHA256:?EXPECTED_SHA256 requerido · ver bd_consolidada.sha256 entregado por Director}"
DISCAPACIDAD_DIR="${DISCAPACIDAD_DIR:-/data/discapacidad}"
DB_CONTAINER="${DB_CONTAINER:-smt-onic-db}"
DB_USER="${DB_USER:-smt_admin}"
DB_NAME="${DB_NAME:-smt_onic}"
API_CONTAINER="${API_CONTAINER:-smt-onic-api}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() { echo -e "${YELLOW}→${NC} $1"; }
ok()   { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }

echo "=================================================="
echo "SMT-ONIC · init_db.sh · $(date -Iseconds)"
echo "DISCAPACIDAD_DIR: $DISCAPACIDAD_DIR"
echo "=================================================="

# 1 · DB healthy
step "1/8 · Verificar DB healthy..."
if ! docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
  fail "DB no responde · ¿levantó docker compose up -d db?"
fi
ok "DB healthy"

# 2 · Descargar tar.gz si no existe
TAR_PATH="$DISCAPACIDAD_DIR/bd_consolidada.tar.gz"
mkdir -p "$DISCAPACIDAD_DIR"

if [[ -f "$TAR_PATH" ]]; then
  step "2/8 · tar.gz ya existe · saltando descarga"
else
  step "2/8 · Descargando $URL_DATA → $TAR_PATH..."
  if ! curl -fsSL -o "$TAR_PATH" "$URL_DATA"; then
    fail "Descarga falló"
  fi
  ok "Descarga completa · $(du -h "$TAR_PATH" | cut -f1)"
fi

# 3 · Verificar checksum
step "3/8 · Verificando SHA256..."
ACTUAL_SHA=$(sha256sum "$TAR_PATH" | cut -d' ' -f1)
if [[ "$ACTUAL_SHA" != "$EXPECTED_SHA256" ]]; then
  fail "Checksum mismatch · esperado $EXPECTED_SHA256 · obtuve $ACTUAL_SHA"
fi
ok "Checksum válido"

# 4 · Descomprimir
if [[ -d "$DISCAPACIDAD_DIR/bd_consolidada" ]]; then
  step "4/8 · bd_consolidada/ ya existe · saltando descompresión"
else
  step "4/8 · Descomprimiendo a $DISCAPACIDAD_DIR..."
  tar -xzf "$TAR_PATH" -C "$DISCAPACIDAD_DIR"
  ok "Descompresión completa · $(ls "$DISCAPACIDAD_DIR/bd_consolidada/" | wc -l) archivos"
fi

# 5 · Aplicar seeds (idempotentes)
step "5/8 · Aplicando seeds 003+004+005..."
for seed in 003_seed_proyecciones_fac.sql 004_seed_proyecciones_escenarios.sql 005_seed_indicadores_definiciones.sql; do
  if [[ -f "backend/sql/$seed" ]]; then
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "backend/sql/$seed" >/dev/null 2>&1 \
      && echo "    ✓ $seed" \
      || fail "Aplicar $seed falló · revisar logs"
  else
    fail "No se encontró backend/sql/$seed"
  fi
done
ok "Seeds aplicados"

# 6 · Carga CNPV completa (largo · 15-30 min)
step "6/8 · Carga CNPV completa via load_all.py..."
echo "    ⏱  Esto puede tomar 15-30 minutos · no interrumpir"
if docker exec "$API_CONTAINER" python -m scripts.load_all 2>&1 | tail -5; then
  ok "Carga CNPV completa"
else
  fail "load_all.py falló · revisar logs · re-correr este script (idempotente)"
fi

# 7 · Verificar counts post-carga
step "7/8 · Verificando counts post-carga..."
COUNTS=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "
  SELECT 'fac:' || COUNT(*) FROM proyecciones.fac
  UNION ALL SELECT 'escenarios:' || COUNT(*) FROM proyecciones.escenarios
  UNION ALL SELECT 'indicadores:' || COUNT(*) FROM indicadores.definiciones
  UNION ALL SELECT 'cnpv_resumen:' || COUNT(*) FROM cnpv.resumen_nacional_etnico
  UNION ALL SELECT 'cnpv_dpto:' || COUNT(*) FROM cnpv.prevalencia_etnia_dpto
  UNION ALL SELECT 'pueblo_disc:' || COUNT(*) FROM pueblo.disc_nacional;
")
echo "$COUNTS" | while IFS= read -r line; do echo "    $line"; done

# Validaciones mínimas
FAC_COUNT=$(echo "$COUNTS" | grep "^fac:" | cut -d':' -f2)
ESC_COUNT=$(echo "$COUNTS" | grep "^escenarios:" | cut -d':' -f2)
IND_COUNT=$(echo "$COUNTS" | grep "^indicadores:" | cut -d':' -f2)

[[ "$FAC_COUNT" == "8" ]]   || fail "proyecciones.fac=$FAC_COUNT (esperado 8)"
[[ "$ESC_COUNT" == "832" ]] || fail "proyecciones.escenarios=$ESC_COUNT (esperado 832)"
[[ "$IND_COUNT" == "12" ]]  || fail "indicadores.definiciones=$IND_COUNT (esperado 12)"
ok "Counts validados"

# 8 · Smoke test final
step "8/8 · Ejecutando smoke tests..."
if [[ -x "infra/smoke_tests.sh" ]]; then
  if ./infra/smoke_tests.sh; then
    ok "Smoke tests verdes"
  else
    fail "Smoke tests fallaron · revisar output"
  fi
else
  echo "    ⚠ smoke_tests.sh no ejecutable · saltando · run manualmente"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}init_db.sh completado · listo para tráfico${NC}"
echo "=================================================="
echo "Próximo paso: configurar nginx + DNS (ver DEPLOY_PRODUCCION.md §5)"
