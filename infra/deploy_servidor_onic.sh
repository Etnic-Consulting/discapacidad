#!/usr/bin/env bash
# infra/deploy_servidor_onic.sh · SMT-ONIC orquestador de deploy
# ===============================================================
# Script único que el equipo de ingeniería ONIC corre la primera vez
# para dejar el sistema listo en su servidor.
#
# Idempotente · safe to re-run.
#
# Pre-requisitos en el servidor:
#   - Docker ≥ 20.10 + Compose v2
#   - Node 20+ (para build del frontend)
#   - jq, curl, git
#   - Archivo .env.prod completo (copiado de .env.prod.example)
#   - Variables URL_DATA y EXPECTED_SHA256 exportadas
#
# Uso:
#   cp .env.prod.example .env.prod && $EDITOR .env.prod
#   export URL_DATA="https://<canal-seguro>/bd_consolidada.tar.gz"
#   export EXPECTED_SHA256="<sha256-que-Wilson-entrega-aparte>"
#   chmod +x infra/deploy_servidor_onic.sh
#   ./infra/deploy_servidor_onic.sh
#
# Generado por Sprint S2.A03 · 2026-05-03

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

step() { echo -e "${BLUE}══${NC} ${YELLOW}$1${NC}"; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "═══════════════════════════════════════════════════════════"
echo "  SMT-ONIC · deploy_servidor_onic.sh"
echo "  $(date -Iseconds)"
echo "  Repo: $REPO_ROOT"
echo "═══════════════════════════════════════════════════════════"

# ─────────────────────────────────────────────────────────────
step "1/8 · Validar pre-requisitos"
# ─────────────────────────────────────────────────────────────

command -v docker >/dev/null 2>&1 || fail "docker no instalado"
docker compose version >/dev/null 2>&1 || fail "docker compose v2 no disponible"
command -v jq >/dev/null 2>&1 || fail "jq no instalado · sudo apt install jq"
command -v curl >/dev/null 2>&1 || fail "curl no instalado"
command -v git >/dev/null 2>&1 || fail "git no instalado"
command -v node >/dev/null 2>&1 || warn "node no instalado · build del frontend será saltado · ver §6"
command -v npm >/dev/null 2>&1 || warn "npm no instalado · build del frontend será saltado · ver §6"

[[ -f ".env.prod" ]] || fail ".env.prod no existe · copiar de .env.prod.example y rellenar"
[[ -n "${URL_DATA:-}" ]] || fail "URL_DATA no exportado · ver header de este script"
[[ -n "${EXPECTED_SHA256:-}" ]] || fail "EXPECTED_SHA256 no exportado · ver header de este script"

# Validar que .env.prod tiene los campos críticos
for key in DB_PASSWORD JWT_SECRET; do
  if ! grep -qE "^${key}=.+" .env.prod || grep -qE "^${key}=$" .env.prod; then
    fail ".env.prod · $key vacío o no definido"
  fi
done
ok "Pre-requisitos OK"

# ─────────────────────────────────────────────────────────────
step "2/8 · Levantar DB (PostGIS)"
# ─────────────────────────────────────────────────────────────

docker compose --env-file .env.prod -f docker-compose.prod.yml up -d db
ok "docker compose up -d db enviado"

# Esperar healthy
echo "    Esperando DB healthy..."
for i in {1..30}; do
  if docker exec smt-onic-db pg_isready -U smt_admin -d smt_onic >/dev/null 2>&1; then
    ok "DB healthy (intento $i)"
    break
  fi
  sleep 2
  if [[ $i -eq 30 ]]; then
    fail "DB no respondió healthy en 60s · revisar 'docker compose logs db'"
  fi
done

# ─────────────────────────────────────────────────────────────
step "3/8 · Cargar corpus + seeds + load_all (init_db.sh)"
# ─────────────────────────────────────────────────────────────

if [[ -x "infra/init_db.sh" ]]; then
  ./infra/init_db.sh
  ok "init_db.sh completado"
else
  warn "infra/init_db.sh no ejecutable · saltando"
  warn "Si esta es la primera vez corriendo, levantar manualmente:"
  warn "  bash infra/init_db.sh"
fi

# ─────────────────────────────────────────────────────────────
step "4/8 · Levantar API"
# ─────────────────────────────────────────────────────────────

docker compose --env-file .env.prod -f docker-compose.prod.yml up -d api
ok "docker compose up -d api enviado"

echo "    Esperando API healthy..."
for i in {1..30}; do
  if curl -fsS http://localhost:8095/api/v1/health >/dev/null 2>&1; then
    ok "API healthy (intento $i)"
    break
  fi
  sleep 2
  if [[ $i -eq 30 ]]; then
    fail "API no respondió en 60s · revisar 'docker compose logs api'"
  fi
done

# ─────────────────────────────────────────────────────────────
step "5/8 · Build frontend estático"
# ─────────────────────────────────────────────────────────────

if command -v npm >/dev/null 2>&1; then
  pushd frontend >/dev/null
  if [[ ! -d "node_modules" ]]; then
    echo "    Primer build · instalando dependencias (toma ~2 min)..."
    npm ci --silent
  fi
  echo "    Construyendo bundle producción..."
  VITE_API_URL=/api/v1 npm run build --silent
  popd >/dev/null

  if [[ -d "frontend/dist" ]] && [[ -f "frontend/dist/index.html" ]]; then
    ok "Bundle construido en frontend/dist/"
  else
    fail "frontend/dist/index.html no existe · build falló"
  fi

  # Mover a docroot si /var/www existe
  if [[ -d "/var/www" ]]; then
    sudo mkdir -p /var/www/smt-onic-frontend
    sudo cp -r frontend/dist/* /var/www/smt-onic-frontend/
    ok "Bundle copiado a /var/www/smt-onic-frontend/"
  else
    warn "/var/www no existe · copiar manualmente frontend/dist/* al docroot del nginx"
  fi
else
  warn "Saltado · instalar Node 20+ y re-correr este step"
fi

# ─────────────────────────────────────────────────────────────
step "6/8 · Smoke tests"
# ─────────────────────────────────────────────────────────────

if [[ -x "infra/smoke_tests.sh" ]]; then
  if ./infra/smoke_tests.sh; then
    ok "Smoke tests verdes"
  else
    fail "Smoke tests fallaron · NO anunciar go-live · revisar output"
  fi
else
  chmod +x infra/smoke_tests.sh 2>/dev/null || true
  if ./infra/smoke_tests.sh; then
    ok "Smoke tests verdes"
  else
    fail "Smoke tests fallaron"
  fi
fi

# ─────────────────────────────────────────────────────────────
step "7/8 · Verificar config nginx (recordatorio)"
# ─────────────────────────────────────────────────────────────

if [[ -f "/etc/nginx/sites-enabled/smt-onic" ]]; then
  if sudo nginx -t >/dev/null 2>&1; then
    ok "nginx config válida"
  else
    warn "nginx -t falló · revisar /etc/nginx/sites-available/smt-onic"
  fi
else
  warn "Nginx no configurado todavía · ver INSTRUCCIONES_INGENIERIA_ONIC.md §4"
  warn "Comandos:"
  warn "  sudo cp infra/nginx.smt-onic.conf /etc/nginx/sites-available/smt-onic"
  warn "  sudo ln -sf /etc/nginx/sites-available/smt-onic /etc/nginx/sites-enabled/"
  warn "  sudo certbot --nginx -d smt-onic.com -d www.smt-onic.com"
fi

# ─────────────────────────────────────────────────────────────
step "8/8 · Resumen final"
# ─────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "  ${GREEN}✓ DEPLOY OK${NC} · listo para validación humana"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Estado de containers:"
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
echo ""
echo "  Próximos pasos (Wilson + ingeniería ONIC):"
echo "    1. Verificar https://smt-onic.com/ carga el frontend (tras nginx + DNS)"
echo "    2. Login como usuario seed · validar UX completo"
echo "    3. Revisar docker logs api --tail=100 buscando errores no fatales"
echo "    4. Configurar cron de backup (ver INSTRUCCIONES_INGENIERIA_ONIC.md §6)"
echo "    5. Firmar minuta de handoff (_docs/MINUTA_HANDOFF_TEMPLATE.md)"
echo ""
echo "  Si algo va mal:"
echo "    docker compose logs api --tail=50"
echo "    docker compose logs db --tail=50"
echo "    ./infra/smoke_tests.sh https://smt-onic.com   # tras DNS configurado"
echo ""
