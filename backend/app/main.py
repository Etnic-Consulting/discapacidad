import json
import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.routers import dashboard, pueblos, geo, conflicto, indicadores, demografia, auth, formulario, informes, observatorio


request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    handler.addFilter(_RequestIdFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)


_configure_logging()
access_log = logging.getLogger("smt_onic.access")


class RequestIdLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        token = request_id_ctx.set(rid)
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            access_log.exception(
                "request failed method=%s path=%s duration_ms=%.1f",
                request.method, request.url.path, duration_ms,
            )
            request_id_ctx.reset(token)
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = rid
        access_log.info(
            "method=%s path=%s status=%d duration_ms=%.1f",
            request.method, request.url.path, response.status_code, duration_ms,
        )
        request_id_ctx.reset(token)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """E02 · Headers de seguridad estándar OWASP."""
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        h = response.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        # CSP solo para HTML responses · API JSON no requiere
        ct = h.get("content-type", "").lower()
        if "text/html" in ct:
            h.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'",
            )
        # HSTS: solo si la request viene por HTTPS (en prod nginx termina TLS)
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


# A09 · Trazabilidad de cifras: cada response declara la(s) tabla(s) BD origen
# Mapeo path → tabla canónica (extender al agregar endpoints nuevos)
_DATA_SOURCE_MAP = {
    "/api/v1/pueblos/": "pueblo.disc_nacional",
    "/api/v1/pueblos/{cod_pueblo}/perfil": "pueblo.{disc,sexo,edad,limitacion,tratamiento,causa,enfermo}_nacional",
    "/api/v1/dashboard/panorama-kpis": "pueblo.disc_nacional + cnpv.disc_indigena_mpio",
    "/api/v1/dashboard/prevalencia/departamento": "cnpv.prevalencia_etnia_dpto",
    "/api/v1/dashboard/dificultades": "cnpv.dificultades_etnia_dpto",
    "/api/v1/dashboard/brecha": "cnpv.resumen_nacional_etnico",
    "/api/v1/dashboard/intercensal": "cnpv.comparacion_intercensal + proyecciones.fac",
    "/api/v1/dashboard/proyecciones": "proyecciones.escenarios",
    "/api/v1/dashboard/smt-resumen": "smt.resumen",
    "/api/v1/dashboard/filtros": "geo.{departamentos,municipios} + smt_geo.resguardos",
    "/api/v1/demografia/piramide-nacional": "visor_dane.piramide_pueblo (DANE Visor 2021)",
    "/api/v1/demografia/piramide-disc-nacional": "pueblo.piramide_disc (REDATAM CNPV 2018)",
    "/api/v1/demografia/piramide-disc-tipo-nacional": "pueblo.piramide_disc_tipo (REDATAM CNPV 2018, top-30 pueblos)",
    "/api/v1/demografia/nbi": "visor_dane.{nbi_pueblo,ipm_pueblo,poblacion_pueblo}",
    "/api/v1/demografia/lengua": "visor_dane.lengua_pueblo",
    "/api/v1/geo/macrorregiones": "smt_geo.macrorregiones + smt_geo.resguardos",
    "/api/v1/geo/smt/resguardos": "smt_geo.resguardos + cnpv.disc_indigena_mpio",
    "/api/v1/conflicto/victimas/resumen": "ext.ruv_hechos_municipal",
    "/api/v1/indicadores/": "indicadores.definiciones",
    "/api/v1/indicadores/valores": "indicadores.valores",
}


class CacheControlMiddleware(BaseHTTPMiddleware):
    """F02 · Cache HTTP en endpoints idempotentes y estáticos.

    Sólo aplica si el response no tiene Cache-Control · no rompe responses
    sensibles (auth/me, etc · esos retornan no-store automáticamente).
    """
    _CACHEABLE = {
        "/api/v1/geo/macrorregiones": 1800,           # 30 min · cambia raro
        "/api/v1/geo/smt/macrorregiones": 1800,
        "/api/v1/geo/smt/resguardos": 600,            # 10 min · GeoJSON pesado
        "/api/v1/indicadores/": 1800,
        "/api/v1/dashboard/filtros": 600,
        "/api/v1/dashboard/smt-resumen": 600,
        "/api/v1/formulario/territorios/macros": 3600,
    }
    _NO_STORE = {"/api/v1/auth/me", "/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/health"}

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.method != "GET" or response.status_code != 200:
            return response
        path = request.url.path
        if path in self._NO_STORE:
            response.headers.setdefault("Cache-Control", "no-store, no-cache, must-revalidate")
            return response
        ttl = self._CACHEABLE.get(path)
        if ttl and "cache-control" not in {k.lower() for k in response.headers}:
            response.headers["Cache-Control"] = f"public, max-age={ttl}, s-maxage={ttl}"
        return response


class DataSourceMiddleware(BaseHTTPMiddleware):
    """A09 · Agrega header X-Data-Source con la tabla BD origen del response.
    Permite trazabilidad cifra → fuente desde el frontend o consumidor externo.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        path = request.url.path
        # Match exacto primero
        source = _DATA_SOURCE_MAP.get(path)
        if not source:
            # Match por prefijo (ej: /api/v1/pueblos/720/perfil)
            for k, v in _DATA_SOURCE_MAP.items():
                if "{" in k:
                    prefix = k.split("{")[0]
                    if path.startswith(prefix):
                        source = v
                        break
        if source:
            response.headers["X-Data-Source"] = source
            response.headers["X-Data-Authority"] = "CIFRAS_CANONICAS_v1.md"
        return response


_LOGIN_RL_PATH = "/api/v1/auth/login"
_LOGIN_RL_WINDOW_S = 60
_LOGIN_RL_MAX = 8
_login_attempts: dict[str, list[float]] = {}


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path != _LOGIN_RL_PATH:
            return await call_next(request)
        ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "anon")
        )
        now = time.time()
        bucket = _login_attempts.setdefault(ip, [])
        cutoff = now - _LOGIN_RL_WINDOW_S
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)
        if len(bucket) >= _LOGIN_RL_MAX:
            retry_after = int(_LOGIN_RL_WINDOW_S - (now - bucket[0])) + 1
            access_log.warning(
                "rate_limit method=POST path=%s ip=%s attempts=%d window_s=%d",
                _LOGIN_RL_PATH, ip, len(bucket), _LOGIN_RL_WINDOW_S,
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": f"Demasiados intentos de login. Reintenta en {retry_after}s."},
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)
        return await call_next(request)


app = FastAPI(
    title="SMT-ONIC API",
    description="Sistema de Monitoreo Territorial - Personas con Capacidades Diversas de Pueblos Indigenas",
    version="2.0.0",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(DataSourceMiddleware)
app.add_middleware(LoginRateLimitMiddleware)
app.add_middleware(RequestIdLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(pueblos.router, prefix="/api/v1/pueblos", tags=["Pueblos"])
app.include_router(geo.router, prefix="/api/v1/geo", tags=["Geografia"])
app.include_router(conflicto.router, prefix="/api/v1/conflicto", tags=["Conflicto Armado"])
app.include_router(indicadores.router, prefix="/api/v1/indicadores", tags=["Indicadores"])
app.include_router(demografia.router, prefix="/api/v1/demografia", tags=["Demografia"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(formulario.router, prefix="/api/v1/formulario", tags=["Formulario"])
app.include_router(informes.router, prefix="/api/v1/informes", tags=["Informes"])
app.include_router(observatorio.router, prefix="/api/v1/observatorio", tags=["Observatorio"])


@app.get("/api/v1/health")
async def health():
    """B05 · Health check completo · BD + schema + datos esperados."""
    from app.database import get_db
    from sqlalchemy import text

    checks = {
        "service": "smt-onic-api",
        "version": "2.0.0",
        "status": "ok",
    }
    db_ok = True
    db_errors: list[str] = []

    # Iterador único · cierra sesión al final
    db_gen = get_db()
    try:
        db = await db_gen.__anext__()
        # (schema, tabla, min_esperado, critica)
        # critica=False → tabla opcional (REDATAM, shapefiles, SMT forms); su ausencia no degrada status
        TABLE_CHECKS = [
            ("cnpv", "resumen_nacional_etnico", 1, True),
            ("pueblo", "disc_nacional", 100, True),
            ("indicadores", "definiciones", 12, True),
            ("proyecciones", "fac", 5, True),
            ("proyecciones", "escenarios", 100, True),
            ("pueblo", "piramide_disc", 1000, False),   # cargado vía scraper REDATAM
            ("smt_geo", "resguardos", 800, False),       # cargado vía shapefiles
            ("smt_geo", "macrorregiones", 5, False),     # cargado vía shapefiles
            ("visor_dane", "piramide_pueblo", 5000, False),  # datos DANE adicionales
            ("smt", "resumen", 30, False),               # calculado desde formularios SMT
        ]
        for schema, tabla, esperado_min, critica in TABLE_CHECKS:
            try:
                r = await db.execute(text(f"SELECT COUNT(*) FROM {schema}.{tabla}"))
                cnt = r.scalar() or 0
                checks[f"{schema}.{tabla}"] = {
                    "rows": cnt,
                    "min_expected": esperado_min,
                    "ok": cnt >= esperado_min,
                    "optional": not critica,
                }
                if cnt < esperado_min and critica:
                    db_ok = False
                    db_errors.append(f"{schema}.{tabla} tiene {cnt} filas < esperado {esperado_min}")
            except Exception as e:
                # Rollback para evitar InFailedSqlTransaction en queries siguientes
                try:
                    await db.rollback()
                except Exception:
                    pass
                if critica:
                    db_ok = False
                    db_errors.append(f"{schema}.{tabla}: {str(e)[:80]}")
                checks[f"{schema}.{tabla}"] = {"ok": False, "optional": not critica, "error": str(e)[:80]}
    except Exception as e:
        db_ok = False
        db_errors.append(f"db connection: {str(e)[:120]}")
    finally:
        try:
            await db_gen.aclose()
        except Exception:
            pass

    checks["db"] = {"ok": db_ok, "errors": db_errors[:5] if db_errors else []}
    if not db_ok:
        checks["status"] = "degraded"
    return checks
