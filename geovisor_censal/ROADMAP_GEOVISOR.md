# ROADMAP: GEOVISOR CENSAL DE PUEBLOS INDIGENAS
## Proyecto derivado del SMT-ONIC
## Fecha: 3 abril 2026

---

## 1. OBJETIVO

Construir un geovisor que permita ver la informacion censal (CNPV 2018) al maximo
nivel de detalle geografico para territorios indigenas: resguardos, comunidades,
secciones rurales, centros poblados y clusters de viviendas — incluyendo zonas
FUERA de resguardos donde habitan comunidades indigenas.

---

## 2. FUENTES DE DATOS DESCUBIERTAS

### 2.1 ArcGIS REST API del DANE (acceso libre, sin CAPTCHA)

**URL base**: https://geoportal.dane.gov.co/mparcgis/rest/services

**MGN 2018 (Marco Geoestadistico Nacional) — geometrias**:
| Capa | Layer ID | Geometria | Cantidad estimada |
|------|----------|-----------|-------------------|
| Seccion Urbana | 214 | Polygon | ~350K |
| Manzana | 215 | Polygon | ~700K |
| Sector Urbano | 246 | Polygon | ~40K |
| Sector Rural | 286 | Polygon | ~33K |
| Seccion Rural | 287 | Polygon | ~73K |
| Zona Urbana | 305 | Polygon | ~1.1K |
| Municipio | 317 | Polygon | ~1.1K |
| Departamento | 319 | Polygon | 33 |

Endpoint: FeatureServer/query?where=...&outFields=*&f=geojson

**Indicadores Grupos Etnicos por Resguardo (49 servicios)**:
- Funcionamiento humano (cap. diversas) total, por sexo, por tipo (9 tipos)
- Poblacion indigena total, por grupos de edad (0-14, 15-64, 65+)
- Lengua nativa
- Alfabetismo, nivel educativo (7 niveles)
- Asistencia escolar
- Servicios basicos (energia, acueducto, alcantarillado, gas, basura)
- Poblacion por grupo etnico

### 2.2 Shapefile de viviendas ONIC (ya cargado)
- 268,274 viviendas con coordenadas lat/lon
- Pueblo, personas, servicios, resguardo
- Fuente: DANE entregado a ONIC

### 2.3 Microdatos CNPV 2018 (descarga manual + CAPTCHA)
- 48 variables por persona
- Antioquia ya procesado: 37,628 indigenas
- Pendiente: otros departamentos

### 2.4 SpatiaLite ONIC (ya cargado en PostGIS)
- 830 resguardos con geometria
- 13,868 comunidades como puntos
- 1,935 clusters de viviendas

---

## 3. ARQUITECTURA DEL GEOVISOR

```
[DANE ArcGIS REST API]          [PostGIS smt_onic]
   49 servicios etnicos              viviendas, microdatos,
   MGN manzanas/secciones            resguardos, comunidades
         |                                    |
         v                                    v
  [Backend FastAPI — Geovisor]
   Proxy + cache de geometrias DANE
   Queries espaciales PostGIS
   Clustering de viviendas fuera de resguardo
         |
         v
  [Frontend React + Leaflet]
   Mapa multi-capa con zoom semantico
   Al hacer zoom: mpio -> sector -> seccion -> manzana -> viviendas
   Click: ficha censal del area
```

### 3.1 Zoom semantico

| Zoom | Nivel | Geometria | Datos |
|------|-------|-----------|-------|
| 5-7 | Departamento | Poligono DANE | Prevalencia etnica |
| 7-9 | Municipio | Poligono DANE | Poblacion indigena, NBI |
| 9-11 | Resguardo | Poligono ONIC | Cap. diversas, lengua, educacion |
| 11-13 | Sector rural | Poligono DANE MGN | Datos agregados del sector |
| 13-15 | Seccion rural/urbana | Poligono DANE MGN | Datos censales detallados |
| 15-17 | Comunidad/Cluster | Punto/poligono ONIC | Viviendas, personas |
| 17+ | Vivienda individual | Punto shapefile | Pueblo, servicios, personas |

### 3.2 Cluster de viviendas fuera de resguardo

Muchas comunidades indigenas no estan dentro de resguardos titulados.
El shapefile de viviendas permite identificar estos agrupamientos:

```python
# Algoritmo DBSCAN para clustering espacial
from sklearn.cluster import DBSCAN
import numpy as np

# Viviendas SIN resguardo (uva2_codte IS NULL) 
coords = np.array([[lat, lon] for lat, lon in viviendas_sin_resguardo])
clustering = DBSCAN(eps=0.005, min_samples=3)  # ~500m radio, min 3 viviendas
labels = clustering.fit_predict(coords)

# Cada cluster = una "comunidad no resguardada"
# Se le puede asignar: convex hull como geometria, pueblo dominante, 
# poblacion total, tasa de cap. diversas estimada
```

---

## 4. DATOS POR NIVEL GEOGRAFICO

### 4.1 Por Resguardo (disponible via REST API DANE + nuestro REDATAM)

| Indicador | Servicio DANE | Nuestro dato |
|-----------|--------------|--------------|
| Funcionamiento humano (total) | Serv_Resg_DifFuncionaHum_2018 | cnpv.disc_resguardo |
| Dif. ver | Serv_Resg_DifVer_2018 | — |
| Dif. oir | Serv_Resg_DifOir_2018 | — |
| Dif. caminar | Serv_Resg_DifMoverse_2018 | — |
| Dif. hablar | Serv_Resg_DifHablar_2018 | — |
| Dif. agarrar | Serv_Resg_Difagarrar_2018 | — |
| Dif. cognitiva | Serv_Resg_Difcogni_2018 | — |
| Dif. comer | Serv_Resg_Difcomer_2018 | — |
| Dif. interactuar | Serv_Resg_DifInteractuar_2018 | — |
| Dif. actividades diarias | Serv_Resg_DifActivDiarias_2018 | — |
| Func. humano hombres | Serv_Resg_DifFuncionaHumSexo_H2018 | — |
| Func. humano mujeres | Serv_Resg_DifFuncionaHumSexo_M2018 | — |
| Poblacion total | Serv_Resg_PoblacionTotal_2018 | visor_dane.resguardo_pueblo |
| Pob. indigena | Serv_Resg_PoblacionIndigenaEnResguardo_CNPV_2018 | — |
| Pob. 0-14 | Serv_Resg_PoblIndigena_0a14_2018 | — |
| Pob. 15-64 | Serv_Resg_PoblIndigena_15a64_2018 | — |
| Pob. 65+ | Serv_Resg_PoblIndigena_65ymas_2018 | — |
| Habla lengua | Serv_Resg_Habla_lengua_2018 | visor_dane.lengua_pueblo |
| Alfabetismo | Serv_Resg_Alfabetismo15yMas_2018f | visor_dane.alfabetismo_pueblo |
| Asistencia escolar | Serv_Resg_AsisEscolar_2018 | — |
| Nivel educativo (7 niveles) | 7 servicios | visor_dane.educacion_pueblo |
| Energia | Serv_Resg_ServicioEnergia_2018 | visor_dane.viviendas |
| Acueducto | Serv_Resg_ServicioAcueducto_2018 | visor_dane.viviendas |
| Alcantarillado | Serv_Resg_ServicioAlcantarillado_2018 | visor_dane.viviendas |
| Gas | Serv_Resg_Servicio_Gas_2018 | visor_dane.viviendas |
| Basura | Serv_Resg_Servicio_Basura_2018 | visor_dane.viviendas |

**49 indicadores por resguardo disponibles via REST sin autenticacion.**

### 4.2 Por Seccion Rural / Manzana (via microdatos + MGN)

Cruce: microdatos.COD_DANE_ANM → MGN.Seccion/Manzana
Variables: TODAS las 48 del censo, agregadas al nivel de la seccion/manzana

### 4.3 Por Vivienda individual (shapefile ONIC)

Cada punto tiene: pueblo, personas, servicios, coordenadas.
Enriquecido con tasas del resguardo/municipio.

---

## 5. ROADMAP TECNICO

### Sprint 1 (1 semana): Descargar datos DANE via REST API
- [ ] Descargar los 49 servicios de grupos etnicos por resguardo
- [ ] Descargar secciones rurales del MGN para departamentos con resguardos
- [ ] Almacenar en PostGIS (schema geovisor)
- [ ] Verificar JOIN entre MGN y microdatos

### Sprint 2 (1 semana): Cluster de viviendas fuera de resguardo
- [ ] Identificar viviendas sin resguardo en el shapefile
- [ ] Aplicar DBSCAN clustering espacial
- [ ] Generar geometrias (convex hull) para cada cluster
- [ ] Asignar pueblo dominante y tasas a cada cluster
- [ ] Cargar clusters a PostGIS

### Sprint 3 (2 semanas): Backend del geovisor
- [ ] FastAPI con endpoints por nivel geografico
- [ ] Proxy cache para servicios DANE REST
- [ ] Queries espaciales PostGIS (ST_Contains, ST_Intersects)
- [ ] Generacion de fichas censales por area

### Sprint 4 (2 semanas): Frontend del geovisor
- [ ] React + Leaflet con zoom semantico
- [ ] Capas toggleables por nivel
- [ ] Popup fichas al click
- [ ] Panel lateral con estadisticas del area visible
- [ ] Exportacion de areas seleccionadas

### Sprint 5 (1 semana): Integracion con SMT-ONIC
- [ ] Link bidireccional entre geovisor y dashboard de cap. diversas
- [ ] Filtros compartidos
- [ ] Informes territoriales con mapas del geovisor

---

## 6. STACK TECNOLOGICO

- **Backend**: FastAPI + PostGIS (mismo stack que SMT-ONIC)
- **Frontend**: React + Leaflet + TileLayer + GeoJSON
- **Datos**: PostGIS (local) + DANE REST API (proxy)
- **Clustering**: scikit-learn DBSCAN
- **Geometrias**: Shapely, GeoPandas

---

## 7. ENTREGABLES

1. Geovisor web con zoom semantico hasta nivel de vivienda
2. Fichas censales por resguardo, seccion rural y cluster
3. Identificacion de comunidades fuera de resguardo
4. Base de datos PostGIS con todas las geometrias integradas
5. API para consulta espacial ("dame los indicadores de esta area")
