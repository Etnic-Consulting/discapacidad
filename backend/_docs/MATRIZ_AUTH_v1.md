# Matriz de autorización · SMT-ONIC v1.0

Documenta qué endpoints de la API requieren `Bearer token` y por qué.

## Principios

1. **Datos sensibles → cerrados.** Cualquier endpoint que exponga datos personales, identificación de víctimas, atributos por persona, o agregaciones a nivel persona requiere autenticación.
2. **Catálogos institucionales → públicos.** Listas de organización (5 macrorregiones, 33 departamentos, 1.122 municipios) son información pública del Estado o de la organización indígena, sin riesgo de re-identificación.
3. **Métricas agregadas nacionales → públicas con auth opcional.** El panorama general es público para favorecer transparencia institucional. Las consultas drill-down a pueblo, resguardo o municipio se cierran.

## Endpoints cerrados (requieren Bearer)

| Endpoint | Razón |
|---|---|
| `/api/v1/pueblos/` | Catálogo con cifras por pueblo (puede inferirse demografía sensible en pueblos pequeños) |
| `/api/v1/pueblos/<id>/perfil` | Perfil detallado |
| `/api/v1/geo/resguardos` | Polígonos + atributos por resguardo |
| `/api/v1/geo/smt/resguardos` | Idem ONIC |
| `/api/v1/indicadores/` | Definiciones (público) pero `/valores` con drill-down → cerrado |
| `/api/v1/indicadores/valores` | Valores por territorio |
| `/api/v1/conflicto/...` | Víctimas RUV cruzadas con capacidades diversas (sensible · Habeas Data) |
| `/api/v1/formulario/...` | Captura territorial · solo dinamizadores autorizados |

## Endpoints públicos (sin token)

| Endpoint | Razón |
|---|---|
| `/api/v1/health` | Monitoreo externo (Uptime Robot, Pingdom) |
| `/api/v1/dashboard/` | Resumen nacional · cifras macro |
| `/api/v1/dashboard/dificultades` | Tipología Washington Group nacional |
| `/api/v1/dashboard/brecha` | Brecha entre grupos étnicos |
| `/api/v1/dashboard/prevalencia/departamento` | Mapa de calor nacional |
| `/api/v1/dashboard/intercensal` | Comparativo 2005-2018 nacional |
| `/api/v1/dashboard/proyecciones` | 832 escenarios nacionales |
| `/api/v1/dashboard/panorama-kpis` | KPIs portada |
| `/api/v1/dashboard/filtros` | Cascada geográfica para selectores |
| `/api/v1/demografia/...` | Pirámides nacionales |
| `/api/v1/geo/macrorregiones` | 5 macrorregiones ONIC |
| `/api/v1/geo/smt/macrorregiones` | Idem |
| `/api/v1/formulario/territorios/macros` | Catálogo macros para selector |

## Roles de usuario

| Rol | Capacidades |
|---|---|
| `admin` | Todo · gestión de usuarios |
| `coordinador` | Lectura completa · puede generar informes y descargas |
| `dinamizador` | Lectura completa + escritura del formulario de captura territorial |

## Implementación

- Hash de password: SHA-256 con salt aleatorio (16 bytes hex) · ver `app/services/auth.py`.
- Token JWT de 64 caracteres URL-safe, vida útil 12 horas.
- Schema de almacenamiento: `smt.usuarios`, `smt.sesion_tokens`, `smt.respuestas_formulario`.
- Cierre del endpoint: `dependencies=[Depends(get_current_user)]` en el decorador de la ruta.

## Pruebas

- `backend/tests/test_auth_matrix.py` valida la matriz contra runtime.
- Smoke test 6 (`infra/smoke_tests.sh`) verifica que `/pueblos/` sin token retorna 401.

---

© EtniConsulting SAS — 2026
