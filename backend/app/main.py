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
from app.routers import dashboard, pueblos, geo, conflicto, indicadores, demografia, auth, formulario


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
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        h = response.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
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


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "smt-onic-api"}
