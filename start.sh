#!/bin/bash
echo "=========================================="
echo "  SMT-ONIC v2.1 — Iniciando servicios"
echo "=========================================="

# Start Docker if not running
docker info > /dev/null 2>&1 || {
    echo "Iniciando Docker Desktop..."
    start "" "C:/Program Files/Docker/Docker/Docker Desktop.exe"
    sleep 30
}

# Start PostgreSQL
echo "1/3 Iniciando PostgreSQL+PostGIS..."
cd "D:/1.Programacion/1.onic-smt-dashboard"
docker compose up -d db
sleep 10
docker exec smt-onic-db pg_isready -U smt_admin -d smt_onic || {
    echo "ERROR: PostgreSQL no inicio"
    exit 1
}

# Start API
echo "2/3 Iniciando API FastAPI..."
cd "D:/1.Programacion/1.onic-smt-dashboard/backend"
source .venv/Scripts/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080 &
sleep 5

# Start Frontend
echo "3/3 Iniciando Frontend React..."
cd "D:/1.Programacion/1.onic-smt-dashboard/frontend"
npm run dev -- --port 5174 &
sleep 4

echo ""
echo "=========================================="
echo "  SMT-ONIC v2.1 LISTO"
echo "=========================================="
echo "  Dashboard: http://localhost:5174"
echo "  API Docs:  http://localhost:8080/docs"
echo "  PostGIS:   localhost:5450"
echo "  QGIS:      smt_admin/smt_onic_2026"
echo "=========================================="
