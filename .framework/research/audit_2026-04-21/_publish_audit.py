"""One-shot: publish HALLAZGO entries to pizarra and create queue tasks for AUDIT_E2E_2026-04-21."""
import json
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PIZARRA = ROOT / ".framework" / "comms" / "log.jsonl"
QUEUE = ROOT / ".framework" / "tasks" / "queue.jsonl"

now = datetime.now().astimezone()
fecha = now.strftime("%Y-%m-%d")
hora = now.strftime("%H:%M:%S")
ts = now.isoformat()

hallazgos = [
    ("H-ONIC-001", "CRIT", "Endpoints /api/v1/dashboard/*, /conflicto/*, /demografia/* sin auth - datos sensibles abiertos. curl 200 sin token. Agregar Depends(get_current_user) en cada router."),
    ("H-ONIC-002", "CRIT", "CORS allow_methods=[*] + allow_headers=[*] en backend/app/main.py:16 - restringir a GET/POST y origin del frontend prod."),
    ("H-ONIC-003", "CRIT", "XSS dangerouslySetInnerHTML sin sanitizar en frontend/src/components/SectionHead.jsx:12 - usar DOMPurify o eliminar."),
    ("H-ONIC-004", "CRIT", "alembic/versions vacio - sin migraciones. Ejecutar alembic init + autogenerate desde modelos."),
    ("H-ONIC-005", "CRIT", "Falta frontend/Dockerfile - crear multi-stage Node->nginx."),
    ("H-ONIC-006", "CRIT", "backend/Dockerfile single-stage + corre como root + sin .dockerignore - refactor multi-stage + USER appuser."),
    ("H-ONIC-007", "ALTO", "Rotar secrets en .env (DB_PASSWORD + revocar PAT GitHub ghp_...). .env NO esta en git pero credenciales son reales en disco."),
    ("H-ONIC-008", "ALTO", "Sin rate limit en /api/v1/auth/login - agregar slowapi 5/min."),
    ("H-ONIC-009", "ALTO", "Sin security headers (CSP, X-Frame-Options, HSTS) - middleware secure-headers."),
    ("H-ONIC-010", "ALTO", "Sin error monitoring (Sentry/glitchtip) backend+frontend."),
    ("H-ONIC-011", "ALTO", "Logging no estructurado, sin request_id - solo conflicto.py usa logger."),
    ("H-ONIC-012", "ALTO", "Sin tests pytest backend - anadir tests minimos auth/dashboard/formulario."),
    ("H-ONIC-013", "ALTO", "Sin CI workflow - crear .github/workflows/ci.yml con lint+tests+docker build."),
    ("H-ONIC-014", "ALTO", "Inconsistencia conteo pueblos entre paginas: Panorama 124, Pueblos 107, Conflicto 70, Territorios 67. Definir fuente de verdad unica + nota metodologica."),
    ("H-ONIC-015", "ALTO", "VozPropiaPage: 2 graficos en blanco pese a 1044 personas en KPI - debug API o renderer."),
    ("H-ONIC-016", "ALTO", "IndicadoresPage: 11/13 indicadores Sin valor. Cargar valores reales o ocultar pendientes en UI."),
    ("H-ONIC-017", "ALTO", "PuebloDetalle Maku: KPI poblacion=49 vs piramide total=50. Reconciliar fuente."),
    ("H-ONIC-018", "MED", "ProyeccionesPage y VozPropiaPage usan FALLBACK silencioso cuando API falla - agregar banner naranja datos de respaldo."),
    ("H-ONIC-019", "MED", "Jerga sin glosario: CNPV, RUV, por mil, Washington Group, intercensal, RLCPD, CPLI - agregar tooltip con definicion."),
    ("H-ONIC-020", "MED", "Recharts sin alt text, semaforos color-unico - fallan WCAG AA. Agregar iconos junto a colores."),
    ("H-ONIC-021", "MED", "Loading states ausentes/inconsistentes - Panorama OK, Conflicto parcial, Formulario sin overlay submit."),
    ("H-ONIC-022", "MED", "Formulario: 9 preguntas Washington Group sin contexto - pop-up explicativo al abrir Bloque C."),
    ("H-ONIC-023", "BAJO", "Footer inconsistente entre paginas - unificar."),
    ("H-ONIC-024", "BAJO", "ColombiaMap sin viewport scaling para mobile."),
    ("H-ONIC-025", "BAJO", "Sin politica retencion datos formulario (Habeas Data) - documentar."),
]

n = 0
with PIZARRA.open("a", encoding="utf-8") as f:
    for hid, sev, desc in hallazgos:
        entry = {
            "id": "clip-" + uuid.uuid4().hex[:12],
            "de": "clip",
            "para": "wilson",
            "fecha": fecha,
            "hora": hora,
            "ts": ts,
            "mensaje": "[HALLAZGO] " + hid + " (" + sev + ") - " + desc,
            "meta": {"tag": "HALLAZGO", "task_id": hid, "severity": sev, "audit": "AUDIT_E2E_2026-04-21"},
        }
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        n += 1
print("OK:", n, "hallazgos publicados en pizarra")

task_specs = [
    ("H-ONIC-001", "ollama", "ollama-standard", "standard_code", "P0", "Q1",
     "Auth en routers dashboard/conflicto/demografia",
     ["backend/app/routers/dashboard.py", "backend/app/routers/conflicto.py", "backend/app/routers/demografia.py"],
     "Importar get_current_user de auth.py. Agregar current_user=Depends(get_current_user) a cada endpoint GET de los 3 routers. Mantener estructura existente."),
    ("H-ONIC-002", "ollama", "ollama-simple", "simple_edit", "P0", "Q1",
     "Cerrar CORS en main.py",
     ["backend/app/main.py"],
     "En CORSMiddleware cambiar allow_methods=[*] -> [GET,POST], allow_headers=[*] -> [Authorization,Content-Type], allow_origins leer de env CORS_ALLOWED_ORIGINS (csv). Documentar en .env.example."),
    ("H-ONIC-003", "ollama", "ollama-simple", "simple_edit", "P0", "Q1",
     "Sanitizar SectionHead XSS",
     ["frontend/src/components/SectionHead.jsx", "frontend/package.json"],
     "Instalar dompurify. En SectionHead.jsx:12 envolver intro con DOMPurify.sanitize. Si todos los call-sites pasan texto plano, mejor reemplazar por <p>{intro}</p>."),
    ("H-ONIC-004", "clip", "sonnet-4-6", "standard_code", "P0", "Q1",
     "Inicializar alembic + primera migracion",
     ["backend/alembic.ini", "backend/alembic/env.py", "backend/alembic/versions/0001_initial.py"],
     "alembic init si no esta. env.py debe importar Base de app.database y target_metadata=Base.metadata. Generar migracion inicial autogenerate desde el schema actual (cnpv, smt, geo, ruv). Verificar que aplica limpia sobre DB vacia."),
    ("H-ONIC-005", "clip", "sonnet-4-6", "standard_code", "P0", "Q1",
     "Crear frontend/Dockerfile multi-stage",
     ["frontend/Dockerfile", "frontend/.dockerignore", "frontend/nginx.conf", "docker-compose.yml"],
     "Stage 1: node:20-alpine, npm ci, npm run build. Stage 2: nginx:alpine, COPY dist a /usr/share/nginx/html, nginx.conf con SPA fallback (try_files $uri /index.html), gzip, security headers, expose 80. Agregar servicio frontend en docker-compose.yml."),
    ("H-ONIC-006", "ollama", "ollama-standard", "standard_code", "P0", "Q1",
     "Backend Dockerfile multi-stage + non-root + .dockerignore",
     ["backend/Dockerfile", "backend/.dockerignore"],
     "Multi-stage: builder instala deps en venv, runtime python:3.12-slim COPY --from=builder /opt/venv. RUN useradd -m appuser, USER appuser. .dockerignore: .venv,.git,__pycache__,.pytest_cache,*.pyc,data/,tests/,docs/. Mantener compatibilidad con docker-compose actual."),
    ("H-ONIC-007", "wilson", "humano", "manual", "P0", "Q1",
     "Rotar secrets: PAT GitHub + DB password",
     [".env"],
     "1) Revocar PAT GitHub ghp_... en https://github.com/settings/tokens. 2) Generar nuevo si necesario, NO commitear. 3) Cambiar DB_PASSWORD en .env y recrear DB. 4) Verificar git ls-files .env vacio y .gitignore linea 34."),
    ("H-ONIC-008", "ollama", "ollama-simple", "simple_edit", "P1", "Q1",
     "Rate limit /auth/login con slowapi",
     ["backend/app/routers/auth.py", "backend/requirements.txt", "backend/app/main.py"],
     "pip install slowapi. main.py: limiter=Limiter(key_func=get_remote_address); app.state.limiter=limiter; app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler). En auth.py login: @limiter.limit(5/minute)."),
    ("H-ONIC-009", "ollama", "ollama-standard", "standard_code", "P1", "Q1",
     "Security headers middleware",
     ["backend/app/main.py", "backend/app/middleware/security_headers.py"],
     "Middleware que agregue: X-Content-Type-Options nosniff, X-Frame-Options DENY, Referrer-Policy strict-origin-when-cross-origin, Strict-Transport-Security max-age=31536000 (solo si request es https), Content-Security-Policy basica para SPA."),
    ("H-ONIC-010", "clip", "sonnet-4-6", "standard_code", "P1", "Q2",
     "Sentry backend + frontend",
     ["backend/app/main.py", "backend/requirements.txt", "frontend/src/main.jsx", "frontend/package.json", ".env.example"],
     "sentry-sdk[fastapi] backend. @sentry/react frontend. SENTRY_DSN_BACKEND y VITE_SENTRY_DSN en env. Inicializar antes de app/router. traces_sample_rate=0.1 prod."),
    ("H-ONIC-011", "ollama", "ollama-standard", "standard_code", "P1", "Q2",
     "Logging estructurado JSON con request_id",
     ["backend/app/main.py", "backend/app/middleware/logging.py", "backend/requirements.txt"],
     "structlog o python-json-logger. Middleware genera X-Request-ID si no viene, lo propaga en logs. Format JSON: ts, level, request_id, method, path, status, duration_ms, msg."),
    ("H-ONIC-012", "clip", "sonnet-4-6", "complex_code", "P1", "Q2",
     "Tests pytest minimos",
     ["backend/tests/conftest.py", "backend/tests/test_auth.py", "backend/tests/test_dashboard.py", "backend/tests/test_formulario.py", "backend/pytest.ini"],
     "pytest + pytest-asyncio + httpx.AsyncClient + DB de test (sqlite memoria o postgres test). Smoke tests: login OK/KO, GET dashboard requiere auth, POST formulario respuesta valida."),
    ("H-ONIC-013", "clip", "sonnet-4-6", "standard_code", "P1", "Q2",
     "CI workflow GitHub Actions",
     [".github/workflows/ci.yml"],
     "Jobs: backend-test (postgres service, ruff+pytest), frontend-test (npm ci, lint, build), docker-build (build backend+frontend images). Trigger push main + PR."),
    ("H-ONIC-014", "clip", "sonnet-4-6", "complex_code", "P1", "Q2",
     "Reconciliar conteos de pueblos (124/107/70/67)",
     ["backend/app/routers/dashboard.py", "backend/app/routers/demografia.py", "backend/app/services/pueblos_canonical.py", "frontend/src/pages/PanoramaPage.jsx", "frontend/src/pages/PueblosPage.jsx", "frontend/src/pages/TerritoriosPage.jsx", "frontend/src/pages/ConflictoPage.jsx"],
     "1) Definir fuente canonica (probablemente cnpv.pueblos_canonicos = 124). 2) Endpoint /api/v1/pueblos/canonical retorna lista unica. 3) Cada KPI 'pueblos X' agrega nota 'X de 124 con dato Y'. 4) Documentar metodologia en pagina About o footer."),
    ("H-ONIC-015", "ollama", "ollama-standard", "standard_code", "P1", "Q2",
     "VozPropia: graficos vacios pese a datos",
     ["frontend/src/pages/VozPropiaPage.jsx", "backend/app/routers/dashboard.py"],
     "Debug: confirmar endpoint que alimenta los 2 graficos retorna data. Si devuelve [], cargar datos reales en smt.respuestas_formulario o agregar empty state explicito 'Sin datos por macrorregion todavia'."),
    ("H-ONIC-016", "clip", "sonnet-4-6", "standard_code", "P2", "Q3",
     "Indicadores: 11/13 sin valor - cargar o documentar pending",
     ["backend/scripts/calculate_indicadores.py", "backend/app/routers/indicadores.py"],
     "Implementar calculos faltantes (cobertura por macrorregion, brechas, etc.) o marcar UI 'En desarrollo' explicitamente con fecha estimada. Evitar 'Sin valor' que sugiere bug."),
    ("H-ONIC-017", "ollama", "ollama-simple", "simple_edit", "P2", "Q3",
     "PuebloDetalle Maku: 49 vs 50",
     ["backend/app/routers/demografia.py", "backend/app/services/perfil_pueblo.py"],
     "Auditar query: KPI 'poblacion total' vs suma piramide quinquenal. Probable causa: 1 persona con sexo='no informa' excluida de piramide. Reconciliar - sumar totales y mostrar misma cifra o nota."),
    ("H-ONIC-018", "ollama", "ollama-simple", "simple_edit", "P2", "Q3",
     "Banner FALLBACK en Proyecciones/VozPropia",
     ["frontend/src/pages/ProyeccionesPage.jsx", "frontend/src/pages/VozPropiaPage.jsx"],
     "Cuando catch usa fallback, set state usandoFallback=true. Renderizar arriba de la pagina: <Note variant=warning>Mostrando datos de respaldo. La conexion con la API fallo.</Note>."),
    ("H-ONIC-019", "ollama", "ollama-standard", "standard_code", "P2", "Q3",
     "Glosario flotante con tooltip",
     ["frontend/src/components/Glossary.jsx", "frontend/src/lib/glossary.js", "frontend/src/pages/PanoramaPage.jsx", "frontend/src/pages/IndicadoresPage.jsx", "frontend/src/pages/ProyeccionesPage.jsx"],
     "Componente <Term term=CNPV>CNPV 2018</Term> que renderiza tooltip al hover. glossary.js: dict {CNPV: Censo Nacional 2018 DANE, RUV: Registro Unico Victimas, por mil: numero de casos cada 1000 personas, ...}. Aplicar en KPIs/headers de las 3 paginas mas densas."),
    ("H-ONIC-020", "ollama", "ollama-simple", "simple_edit", "P2", "Q4",
     "Accesibilidad: alt text + iconos en estado",
     ["frontend/src/components/Badge.jsx", "frontend/src/pages/IndicadoresPage.jsx", "frontend/src/pages/PueblosPage.jsx"],
     "Badges Confiabilidad ALTA/MEDIA/BAJA y semaforos indicadores: agregar icono junto al color. Recharts: agregar role=img aria-label=descripcion en el contenedor."),
    ("H-ONIC-021", "ollama", "ollama-simple", "simple_edit", "P2", "Q4",
     "Loading states consistentes",
     ["frontend/src/pages/ConflictoPage.jsx", "frontend/src/pages/FormularioPage.jsx"],
     "Conflicto: si un fetch falla, mostrar skeleton especifico de ese grafico (no dejar blanco). Formulario: overlay 'Guardando...' con aria-busy=true durante submit."),
    ("H-ONIC-022", "ollama", "ollama-simple", "simple_edit", "P3", "Q4",
     "Formulario Bloque C: contexto Washington Group",
     ["frontend/src/pages/FormularioPage.jsx"],
     "Antes de las 9 preguntas WG, mostrar pop-up o card explicativo: 'Que es Washington Group? Conjunto estandarizado de 9 preguntas para identificar capacidades diversas, recomendado por Naciones Unidas y adoptado por DANE en CNPV.' Boton 'Entendido, continuar'."),
    ("H-ONIC-023", "ollama", "ollama-simple", "simple_edit", "P3", "Q4",
     "Footer consistente",
     ["frontend/src/components/SiteChrome.jsx", "frontend/src/App.jsx"],
     "Componente <Footer/> con: logo ONIC, SMT v2.0, enlace poblacion@onic.org.co, ano. Render en todas las paginas excepto /login (o tambien)."),
    ("H-ONIC-024", "ollama", "ollama-simple", "simple_edit", "P3", "Q4",
     "ColombiaMap viewport scaling movil",
     ["frontend/src/components/ColombiaMap.jsx"],
     "Container con max-height vh-50 en movil, evitar overflow horizontal. Touch zoom habilitado en Leaflet."),
    ("H-ONIC-025", "wilson", "humano", "manual", "P3", "Q4",
     "Politica retencion datos formulario (Habeas Data)",
     ["docs/POLITICA_HABEAS_DATA.md", "frontend/src/pages/FormularioPage.jsx"],
     "Redactar politica con juridico ONIC: finalidad, retencion, derechos titular, contacto. Mostrar consentimiento informado al inicio del formulario con checkbox obligatorio."),
]

m = 0
with QUEUE.open("a", encoding="utf-8") as f:
    for tid, owner, tier, ttype, prio, quad, title, files, spec in task_specs:
        task = {
            "id": tid,
            "phase": "AUDIT-2026-04-21",
            "owner": owner,
            "model_tier": tier,
            "task_type": ttype,
            "priority": prio,
            "quadrant": quad,
            "title": title,
            "files": files,
            "spec": spec,
            "status": "pending",
            "depends_on": [],
            "blocks": [],
        }
        f.write(json.dumps(task, ensure_ascii=False) + "\n")
        m += 1
print("OK:", m, "tareas creadas en cola")
