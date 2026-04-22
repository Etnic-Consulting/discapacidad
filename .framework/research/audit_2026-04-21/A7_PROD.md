# A7 Production Readiness — SMT-ONIC

Auditoría 2026-04-21 · Estado del proyecto: **NO APTO para producción** (6 bloqueantes verificados).

## 1. Seguridad

- ❌ **Auth ausente en endpoints de datos**: `/api/v1/dashboard/*`, `/api/v1/conflicto/*`, `/api/v1/demografia/*` no tienen `Depends(get_current_user)`. Confirmado dinámicamente: `curl -s http://localhost:8095/api/v1/dashboard/panorama-kpis` → 200 sin token. Solo `/api/v1/auth/me` y `/api/v1/formulario/*` están protegidos.
- ❌ **CORS abierto**: `backend/app/main.py` tiene `allow_methods=["*"]` y `allow_headers=["*"]`. Aceptable en dev, NO en prod.
- ❌ **XSS**: `frontend/src/components/SectionHead.jsx:12` usa `dangerouslySetInnerHTML={{ __html: intro }}` sin sanitizar.
- ⚠️ **Secrets en `.env` con valores reales** en disco (`DB_PASSWORD=smt_onic_2026`, GitHub PAT). `.env` SÍ está en `.gitignore:34` y `git log --all -- .env` no devuelve nada — riesgo por filtración local, no por repo público. Rotar igual.
- ❌ **Sin rate limit** (slowapi/limits ausente) → fuerza bruta en `/api/v1/auth/login`.
- ❌ **Sin security headers** (no CSP, X-Frame-Options, HSTS).
- ✅ **SQL injection**: revisado `dashboard.py:60,96`. `text(f"...")` solo interpola strings hardcoded; valores de usuario van como bound params (`:grupo_etnico`). Patrón feo pero seguro.
- ⚠️ **HTTPS-ready**: no hay reverse proxy en docker-compose. Pendiente nginx/traefik.

## 2. Observabilidad

- ⚠️ **Logging**: solo `conflicto.py` usa logger. Resto silencioso. Sin formato JSON, sin request ID.
- ❌ **Sin error monitoring** (Sentry/glitchtip).
- ⚠️ **Health checks**: backend tiene `/api/v1/dashboard/` (root) pero no `/health` ni `/ready`.
- ❌ **Sin métricas** (Prometheus, OpenTelemetry).

## 3. Datos / DB

- ❌ **Migraciones vacías**: `backend/alembic/versions/` sin archivos. Schema en `001_schema.sql` aplicado por init container.
- ❌ **Sin política de backups** (no hay script ni doc).
- ✅ **Pool conexiones**: SQLAlchemy default (5+10).
- ✅ **PostGIS** habilitado.
- ⚠️ **Índices**: revisar models — confirmar índices en `cod_pueblo`, `cod_mpio`, `periodo`.

## 4. Build / Deploy

- ❌ **Frontend sin Dockerfile**. Solo backend tiene.
- ❌ **Backend Dockerfile no es multi-stage** y corre como **root** (sin `USER appuser`).
- ❌ **Sin `.dockerignore`** → COPY copia `.venv`, `.git`, `data/`.
- ✅ **`requirements.txt` con versiones pinneadas**.
- ⚠️ **`package.json` con `^x.y.z`** (rangos sueltos) — `package-lock.json` mitiga, verificar que esté commiteado.
- ❌ **Sin CI/CD**: no `.github/workflows/`, no `.gitlab-ci.yml`.
- ⚠️ **`.env.example`**: existe pero parcial (verificar).

## 5. Tests

- ❌ **Sin pytest backend** (`backend/tests/` vacío o solo manual).
- ❌ **Sin tests frontend** (vitest/jest no configurado).
- ❌ **Sin E2E** (Playwright disponible vía MCP pero no en CI).

## 6. Performance

- ⚠️ **Bundle frontend**: Vite default, sin análisis bundle ni code-splitting reportado.
- ❌ **Sin cache HTTP** en endpoints read-heavy (Cache-Control headers ausentes).
- ⚠️ **Compresión**: depende de reverse proxy (no configurado).
- ⚠️ **N+1**: revisar `models.py` — relationships sin `lazy="joined"` donde aplica.

## 7. Resiliencia

- ⚠️ **Frontend ante API down**: revisado parcial. `ProyeccionesPage` y `VozPropiaPage` usan FALLBACK silencioso (no avisan al usuario).
- ❌ **Sin retry/circuit breaker** en cliente.

## 8. Documentación

- ✅ **README** con setup.
- ✅ **CLAUDE.md** del workspace (framework v2.1).
- ✅ **OpenAPI/Swagger** disponible en `/docs`.
- ❌ **Sin runbook** (cómo restaurar backup, rotar secrets, incident response).
- ❌ **Sin ADRs**.

## 9. Cumplimiento ONIC

- ✅ **Terminología "capacidades diversas"** respetada en UI.
- ❌ **Datos sensibles sin auth**: víctimas, ubicaciones de pueblos accesibles sin login.
- ❌ **Sin política de retención** datos formulario (Habeas Data).

## Veredicto

### 🔴 BLOQUEANTES PRE-PROD (6)

1. **Auth en `/api/v1/dashboard/*`, `/conflicto/*`, `/demografia/*`** (datos sensibles abiertos)
2. **Cerrar CORS** (`allow_methods=["GET","POST"]`, origin específico)
3. **Sanitizar XSS** en `SectionHead.jsx:12` (DOMPurify o eliminar `dangerouslySetInnerHTML`)
4. **Inicializar alembic** + primera migración (autogenerate desde modelos actuales)
5. **Crear `frontend/Dockerfile`** (multi-stage Node→nginx)
6. **Backend Dockerfile**: multi-stage + USER non-root + `.dockerignore`

### 🟠 ALTOS PRE-LAUNCH (8)

7. Rotar secrets `.env` (DB password + revocar PAT GitHub)
8. Rate limit en `/auth/login` (slowapi 5/min)
9. Security headers middleware (secure-headers o manual)
10. Sentry/glitchtip backend + frontend
11. Logging estructurado JSON con request_id
12. Tests pytest mínimos en `auth/`, `dashboard/`, `formulario/`
13. CI workflow (.github/workflows/ci.yml: lint + tests + docker build)
14. Política backups DB (cron pg_dump → S3/local)

### 🟡 MEJORA CONTINUA (resto)

15. Health checks `/health` y `/ready`
16. Cache HTTP en endpoints estables
17. Runbook + ADRs
18. Política retención formulario
19. WAF / nginx delante
20. Code-splitting frontend
