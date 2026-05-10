# Matriz de autenticación · API SMT-ONIC v1.0

**Audiencia**: ingeniería ONIC + cualquier desarrollador que necesite entender qué endpoints son públicos vs cerrados y por qué.
**Última actualización**: 2026-05-10 · post sprint S9.

---

## §1 · Introducción

Esta matriz documenta el modelo de autenticación de la API SMT-ONIC v1.0. Existen 3 niveles de acceso:

| Nivel | Significado | Endpoint típico |
|---|---|---|
| **público** | sin token · accesible anónimamente | `/dashboard/proyecciones` |
| **auth** | requiere JWT válido en `Authorization: Bearer <token>` | `/pueblos/` · `/auth/me` |
| **admin** | (no implementado v1 · diferido a v1.5+) reservado para mutaciones administrativas | — |

**Smoke test 6 valida la integridad de auth**: `./infra/smoke_tests.sh` corre `GET /pueblos/` SIN token y espera **401 Unauthorized**. Si retorna 200, la auth está abierta · CRÍTICO · ver `_docs/RUNBOOK_INCIDENTES.md` Incidente 7.

**Convenciones de status codes**:

| Status | Significado | Cuándo |
|---|---|---|
| 200 | OK | request válido |
| 401 | Unauthorized | sin token · token inválido · token expirado |
| 403 | Forbidden | (v1.5+) token válido pero rol insuficiente |
| 404 | Not Found | recurso inexistente (NO endpoint inexistente · FastAPI da 404 para ambos) |
| 422 | Unprocessable Entity | request bien autenticado pero esquema Pydantic falla |
| 5xx | Server Error | bug API · ver `RUNBOOK §1` |

---

## §2 · Tabla maestra (todos los endpoints)

Ordenada alfabéticamente por router. Auth column: `🔓 público` · `🔐 auth` · `🔐⚙️ admin (v1.5+)`.

| Método | Ruta | Auth | Smoke test cubre | Notas |
|---|---|---|---|---|
| POST | `/auth/login` | 🔓 | smoke 2 | retorna `{access_token, token_type, expires_in}` |
| POST | `/auth/logout` | 🔐 | — | invalida token en lado servidor |
| GET | `/auth/me` | 🔐 | — | retorna `UserOut` del usuario actual |
| GET | `/conflicto/victimas/resumen` | 🔓 | — | agregados RUV cruzados |
| GET | `/conflicto/victimas/hechos` | 🔓 | — | hechos victimizantes |
| GET | `/conflicto/victimas/por-pueblo` | 🔓 | — | breakdown por pueblo |
| GET | `/conflicto/victimas/por-hecho` | 🔓 | — | breakdown por tipo de hecho |
| GET | `/conflicto/victimas/por-tipo` | 🔓 | — | breakdown por categoría |
| GET | `/conflicto/victimas/pueblo/{pueblo_id}` | 🔓 | — | detalle por cod_pueblo |
| GET | `/dashboard/` | 🔓 | — | root del dashboard |
| GET | `/dashboard/prevalencia/departamento` | 🔓 | — | tabla CNPV por dpto |
| GET | `/dashboard/prevalencia/municipio` | 🔓 | — | tabla CNPV por mpio |
| GET | `/dashboard/dificultades` | 🔓 | — | categorización CD CNPV |
| GET | `/dashboard/filtros` | 🔓 | — | filtros disponibles UI |
| GET | `/dashboard/brecha` | 🔓 | smoke 5 | incluye `source_detalle` por paso |
| GET | `/dashboard/salud` | 🔓 | — | indicadores de salud |
| GET | `/dashboard/intercensal` | 🔓 | smoke 4 | aplica FAC si `aplicar_fac=true` |
| GET | `/dashboard/smt-resumen` | 🔓 | — | usa vista `smt.smt_resumen` (seed 012) |
| GET | `/dashboard/proyecciones` | 🔓 | smoke 3 | 104 filas esperadas |
| GET | `/dashboard/panorama-kpis` | 🔓 | — | KPIs landing |
| GET | `/demografia/nbi` | 🔓 | — | NBI nacional |
| GET | `/demografia/nbi/{cod_pueblo}` | 🔓 | — | NBI por pueblo |
| GET | `/demografia/lengua` | 🔓 | — | lengua nativa por pueblo |
| GET | `/demografia/educacion/{cod_pueblo}` | 🔓 | — | nivel educativo |
| GET | `/demografia/vivienda/{cod_pueblo}` | 🔓 | — | tipo vivienda |
| GET | `/demografia/perfil/{cod_pueblo}` | 🔓 | — | perfil agregado |
| GET | `/demografia/ranking` | 🔓 | — | ranking demográfico |
| GET | `/demografia/piramide/{cod_pueblo}` | 🔓 | — | pirámide poblacional estándar |
| GET | `/demografia/resguardos` | 🔓 | — | listado resguardos (NO `/geo/resguardos`) |
| GET | `/demografia/resguardo/{cod_resguardo}` | 🔓 | — | detalle resguardo (info básica) |
| GET | `/demografia/resguardos-pueblo/{cod_pueblo}` | 🔓 | — | resguardos por pueblo |
| GET | `/demografia/piramide-disc/{cod_pueblo}` | 🔓 | — | pirámide capacidades diversas (S9 verificado · TIKUNA 397) |
| GET | `/demografia/piramide-disc-tipo/{cod_pueblo}` | 🔓 | — | pirámide CD por tipo |
| GET | `/demografia/piramide-nacional` | 🔓 | — | pirámide poblacional nacional |
| GET | `/demografia/piramide-disc-nacional` | 🔓 | — | pirámide CD nacional |
| GET | `/demografia/piramide-disc-tipo-nacional` | 🔓 | — | pirámide CD por tipo nacional |
| POST | `/formulario/respuesta` | 🔐 | — | 201 Created · solo dinamizador autenticado submit |
| GET | `/formulario/respuestas` | 🔐 | — | listado paginado |
| GET | `/formulario/respuestas/{respuesta_id}` | 🔐 | — | detalle |
| GET | `/formulario/stats` | 🔐 | — | agregados |
| GET | `/formulario/territorios/macros` | 🔓 | — | catálogo macrorregiones |
| GET | `/formulario/territorios/dptos` | 🔓 | — | catálogo dptos |
| GET | `/formulario/territorios/mpios` | 🔓 | — | catálogo mpios |
| GET | `/formulario/territorios/resguardos` | 🔓 | — | catálogo resguardos |
| GET | `/formulario/territorios/comunidades` | 🔓 | — | catálogo comunidades |
| GET | `/geo/departamentos` | 🔓 | — | geometría dptos (PostGIS) |
| GET | `/geo/municipios` | 🔓 | — | geometría mpios |
| GET | `/geo/resguardos` | 🔐 | — | **AUTH** · coordenadas precisas sensibles |
| GET | `/geo/macrorregiones` | 🔓 | — | macrorregiones DANE |
| GET | `/geo/smt/macrorregiones` | 🔓 | — | macrorregiones ONIC (5) |
| GET | `/indicadores/*` lectura | 🔓 | — | listado de definiciones |
| GET | `/indicadores/admin/*` | 🔐 | — | mutaciones de definiciones |
| GET | `/api/v1/informes/{tipo}/_catalog` | 🔓 | smoke nuevo | catálogo IDs por nivel |
| GET | `/api/v1/informes/{tipo}/_index` | 🔓 | — | catálogo con metadata |
| GET | `/api/v1/informes/{tipo}/{id}` | 🔓 | smoke nuevo | JSON canonical o HTML según `Accept` |
| GET | `/api/v1/informes/MANIFEST.json` | 🔓 | — | catálogo global 2.127 entries |
| GET | `/observatorio/*` | 🔓 | — | endpoints observatorio VBG-CNMI |
| GET | `/pueblos/` | 🔐 | **smoke 6 + 7** | listado completo con cruces · sin token → 401 · con token → 200 |

**Total v1.4.1**: 11 routers · 56 endpoints · 8 con auth requerido · 48 públicos.

---

## §3 · Detalles por router

### Router `auth.py`

**Propósito**: emisión y validación de JWT.

**Convenciones**:

- Login retorna JWT firmado HMAC SHA256 con `JWT_SECRET` del `.env.prod`.
- Token expira en 24h (configurable `JWT_EXPIRE_HOURS`).
- Logout invalida server-side (tabla `smt.token_blacklist` v1.5+ · v1 deja que expire naturalmente).
- `/auth/me` retorna `UserOut` con `username`, `role`, `created_at`.

### Router `conflicto.py`

**Propósito**: agregados RUV (Registro Único de Víctimas) cruzados con CNPV étnico. Todos los endpoints son públicos porque los datos del RUV son públicos por ley colombiana (Ley 1448/2011 art. 154).

### Router `dashboard.py`

**Propósito**: vistas agregadas para el dashboard principal. Todos los endpoints son públicos porque los datos derivan de CNPV 2018 (público DANE) + proyecciones FAC Lee-Carter (metodología documentada en `_docs/METODO_FAC_v1.md`).

**Smoke tests** cubre 3, 4, 5 de este router.

### Router `demografia.py`

**Propósito**: detalle demográfico por pueblo + pirámides poblacionales (estándar y CD). Públicos porque CNPV.

**Endpoint clave para S9**: `/piramide-disc/{cod_pueblo}` · render_pueblo lo consume offline para generar la pirámide visual en `_static/informes/pueblo/{id}.html`.

### Router `formulario.py`

**Propósito**: entrada de datos del Sistema de Monitoreo Territorial (SMT). Los **endpoints de respuesta** son AUTH porque las respuestas crudas son sensibles (datos personales de dinamizadores + comunidades en construcción · Convenio 169 OIT + Ley 1581/2012). Los **endpoints de catálogo de territorios** son públicos porque son listas administrativas.

### Router `geo.py`

**Propósito**: geometrías administrativas. Departamentos, municipios y macrorregiones son públicos (DANE). **Resguardos detallados** son AUTH porque las coordenadas precisas son sensibles a presión territorial sobre comunidades indígenas (decisión doctrinal · soberanía territorial).

### Router `indicadores.py`

**Propósito**: definiciones de indicadores + cálculos. Lectura pública. Escritura (`POST /indicadores/admin/*`) AUTH para evitar modificación arbitraria de definiciones.

### Router `informes.py`

**Propósito**: servir los 2.127 informes pre-renderizados de `backend/_static/informes/`. Todos públicos porque los datos son derivados de CNPV (público). El render offline aplica k-anonimato HONESTO (badge `n<30` si `con_disc < 30`).

### Router `observatorio.py`

**Propósito**: endpoints del Observatorio VBG-CNMI (Violencia Basada en Género contra mujeres indígenas). Datos agregados públicos.

### Router `pueblos.py`

**Propósito**: listado completo de pueblos indígenas con cruces (territorio, prevalencia, conflicto). AUTH porque el cruce completo es sensible. Es el endpoint que valida el **smoke test 6** (sin token → 401).

---

## §4 · Convenciones de auth (JWT)

### Flujo de token

```text
1. Frontend POST /auth/login {username, password}
2. Backend verifica bcrypt hash en smt.users
3. Backend firma JWT con HMAC SHA256 usando JWT_SECRET
4. Backend retorna {access_token, token_type:"bearer", expires_in:86400}
5. Frontend guarda token en localStorage
6. Cada request: header Authorization: Bearer <jwt-token>
7. Backend Depends(get_current_user) decodifica + valida expiry
```

### Casos de error

| Caso | Status | Body |
|---|---|---|
| Sin header `Authorization` | 401 | `{"detail":"Not authenticated"}` |
| Token malformado | 401 | `{"detail":"Could not validate credentials"}` |
| Token firma inválida | 401 | `{"detail":"Could not validate credentials"}` |
| Token expirado (>24h) | 401 | `{"detail":"Token expired"}` |
| Usuario removido de DB | 401 | `{"detail":"User not found"}` |
| Body request inválido (Pydantic) | 422 | `{"detail":[{"loc":[...],"msg":"..."}]}` |

### Rotación de secretos

- `JWT_SECRET` debe rotarse cada **90 días** (decisión D2 del handoff).
- Rotación invalida todos los tokens activos · usuarios deben re-login.
- Generar nuevo secreto: `openssl rand -hex 32`.

---

## §5 · Apéndice · validación con curl

```bash
# 1. Login (debe retornar 200 + JWT)
TOKEN=$(curl -s -X POST https://smt-onic.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"wilson","password":"<password-del-seed>"}' | jq -r '.access_token')
echo "Token: $TOKEN"

# 2. Endpoint público SIN token (debe retornar 200)
curl -i https://smt-onic.com/dashboard/proyecciones | head -3
# Espera HTTP/2 200

# 3. Endpoint auth SIN token (debe retornar 401)
curl -i https://smt-onic.com/pueblos/ | head -3
# Espera HTTP/2 401 (smoke test 6)

# 4. Endpoint auth CON token (debe retornar 200)
curl -i -H "Authorization: Bearer $TOKEN" https://smt-onic.com/pueblos/ | head -3
# Espera HTTP/2 200 (smoke test 7)

# 5. Endpoint auth CON token MALFORMADO (debe retornar 401)
curl -i -H "Authorization: Bearer invalido.token.aqui" https://smt-onic.com/pueblos/ | head -3
# Espera HTTP/2 401

# 6. Informe pre-renderizado SIN token (debe retornar 200)
curl -i https://smt-onic.com/api/v1/informes/pueblo/660 | head -3
# Espera HTTP/2 200 (TIKUNA · público)
```

---

## §6 · Cross-references

- `_docs/ARCHITECTURE.md` · §5 Flujo auth JWT (visión general)
- `_docs/RUNBOOK_INCIDENTES.md` · Incidente 7 (auth abierta · CRÍTICO)
- `_docs/CHECKLIST_GO_LIVE.md` · §3 Variables de entorno (JWT_SECRET, seed creds)
- `INSTRUCCIONES_INGENIERIA_ONIC.md` · §2 (decisión D2 custodia de secretos)
