# Dashboard SMT-ONIC — Capacidades Diversas en Pueblos Indígenas

Sistema de Monitoreo Territorial (SMT) de la **Organización Nacional Indígena de Colombia (ONIC)** para el seguimiento de personas con **capacidades diversas** en los 121 pueblos indígenas del país.

> **Nota terminológica**: La ONIC utiliza el término *capacidades diversas* en lugar de *discapacidad*, reconociendo la diversidad funcional como parte de la riqueza cultural de los pueblos originarios.

---

## Objetivo

Construir una herramienta de análisis y visualización que integre fuentes oficiales (CNPV 2018, CG 2005, RUV, DANE ArcGIS) con datos territoriales de la ONIC (830 resguardos, 13.868 comunidades, 268.274 viviendas) para:

1. Caracterizar la prevalencia de capacidades diversas por pueblo, departamento y municipio.
2. Comparar dinámicas intercensales 2005 vs 2018.
3. Georreferenciar comunidades dentro y fuera de resguardos titulados.
4. Generar informes territoriales exportables para incidencia política.

---

## Stack técnico

| Capa | Tecnología | Puerto local |
|------|-----------|--------------|
| Base de datos | PostgreSQL 16 + PostGIS 3.4 (Docker) | 5450 |
| Backend | FastAPI + SQLAlchemy async | 8080 |
| Frontend | React 18 + Vite + Recharts + Leaflet | 5174 |
| Procesamiento | Python 3.12 (pandas, geopandas, scikit-learn) | — |
| Fuentes externas | DANE ArcGIS REST API, REDATAM, RUV | — |

---

## Estructura

```
backend/           FastAPI + SQLAlchemy + scripts de ingesta
├── app/           Routers, modelos, servicios
├── sql/           Migraciones de esquema (geo, cnpv, pueblo, ext, smt, imp, victimas)
├── scripts/       ETL: REDATAM, shapefiles, microdatos, RUV
└── tests/         Pruebas pytest

frontend/          Dashboard React
├── src/
│   ├── pages/     10 páginas (Dashboard, PuebloDetalle, Informes, etc.)
│   ├── components/ GlobalSelector, gráficos, mapas
│   └── lib/       Helpers API, filtros en cascada

geovisor_censal/   Roadmap del geovisor sub-resguardo (zoom semántico)
scripts/           Scripts auxiliares de deploy
```

---

## Datos externos (NO incluidos en este repo)

Por tamaño (>10 GB) y por políticas de datos sensibles (Ley 1581/2012 de Habeas Data), los datasets no se versionan en GitHub. Se publican en **Releases** o deben obtenerse de la fuente:

| Dataset | Tamaño | Fuente | Ubicación |
|---------|--------|--------|-----------|
| Microdatos CNPV 2018 | 1.2 GB | [DANE Microdatos](https://microdatos.dane.gov.co) | Release `data-v1/cnpv2018` |
| Shapefile viviendas | 306 MB | DANE entregado a ONIC | Release `data-v1/viviendas` |
| Geodatabase ONIC (resguardos, comunidades) | 209 MB | ONIC interno | Release `data-v1/onic-gdb` |
| RUV víctimas indígenas anonimizado | 8.6 GB | Unidad Víctimas (convenio) | Release privado con auth |

---

## Instalación rápida

### 1. Base de datos

```bash
docker compose up -d
# Espera ~30s a que PostGIS arranque en localhost:5450
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate    # Git Bash
pip install -r requirements.txt
cp ../.env.example ../.env       # editar con contraseña local
uvicorn app.main:app --reload --port 8080
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev    # abre http://localhost:5174
```

---

## Páginas del dashboard

1. **Dashboard general** — KPIs nacionales, mapa de calor
2. **Pueblo detalle** — perfil demográfico, 3 pirámides (general, cap. diversas, por tipo)
3. **Comparador** — intercensal 2005 vs 2018
4. **Territorial** — resguardos + NBI + servicios
5. **Víctimas** — RUV cruzado con cap. diversas
6. **Informes** — exportables 7 páginas institucional
7. **Geovisor** — mapa con zoom semántico (en desarrollo)
8. **Modo presentación** — vista sin chrome para pantallazo
9. **Costos Claude** — monitoreo builder
10. **Admin** — gestión de usuarios ONIC

---

## Equipo

- **Wilson Herrera** — Coordinador SMT-ONIC · poblacion@onic.org.co · +57 311 220 1903
- **Claude (Anthropic)** — Auditor técnico
- **Ollama local** — Builder

---

## Licencia

Pendiente de definir con la Dirección General ONIC. Uso actual: interno institucional.

## Créditos y datos fuente

- **DANE**: Censo Nacional de Población y Vivienda 2018, Censo General 2005, MGN 2018.
- **Unidad para las Víctimas (UARIV)**: Registro Único de Víctimas.
- **ONIC**: Geodatabase de resguardos y comunidades indígenas.
- **CEPAL/REDATAM**: Motor de consulta censal.
