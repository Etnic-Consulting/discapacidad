from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import dashboard, pueblos, geo, conflicto, indicadores, demografia

app = FastAPI(
    title="SMT-ONIC API",
    description="Sistema de Monitoreo Territorial - Personas con Capacidades Diversas de Pueblos Indigenas",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(pueblos.router, prefix="/api/v1/pueblos", tags=["Pueblos"])
app.include_router(geo.router, prefix="/api/v1/geo", tags=["Geografia"])
app.include_router(conflicto.router, prefix="/api/v1/conflicto", tags=["Conflicto Armado"])
app.include_router(indicadores.router, prefix="/api/v1/indicadores", tags=["Indicadores"])
app.include_router(demografia.router, prefix="/api/v1/demografia", tags=["Demografia"])


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "smt-onic-api"}
