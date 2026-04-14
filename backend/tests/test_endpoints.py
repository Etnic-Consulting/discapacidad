"""
SMT-ONIC API Endpoint Tests
============================
Runs against the live API at http://localhost:8080.
Uses the requests library (no pytest required).

Usage:
    python tests/test_endpoints.py

Tests:
    - Every endpoint returns 200 (or expected error code)
    - Response structure matches expected format
    - Data quality: no prevalence > 200 per mil for pueblos with n>=100
    - Geo endpoints return valid GeoJSON
    - Filtering parameters work correctly
"""

import sys
import json
import requests

BASE = "http://localhost:8080/api/v1"

passed = 0
failed = 0
errors = []


def report(test_name: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS  {test_name}")
    else:
        failed += 1
        msg = f"  FAIL  {test_name}"
        if detail:
            msg += f"  -- {detail}"
        print(msg)
        errors.append(f"{test_name}: {detail}")


def check_status(name: str, resp: requests.Response, expected: int = 200) -> bool:
    ok = resp.status_code == expected
    report(
        f"{name} -> HTTP {expected}",
        ok,
        f"got {resp.status_code}" if not ok else "",
    )
    return ok


def check_geojson(name: str, data: dict) -> bool:
    """Validate GeoJSON FeatureCollection structure."""
    ok = (
        data.get("type") == "FeatureCollection"
        and isinstance(data.get("features"), list)
    )
    report(f"{name} is valid GeoJSON FeatureCollection", ok,
           f"type={data.get('type')}, features={type(data.get('features')).__name__}" if not ok else "")
    if ok and len(data["features"]) > 0:
        f0 = data["features"][0]
        has_struct = (
            f0.get("type") == "Feature"
            and "geometry" in f0
            and "properties" in f0
        )
        report(f"{name} features have correct structure", has_struct)
        return has_struct
    return ok


# ============================================================
# 1. HEALTH
# ============================================================
print("\n=== HEALTH ===")
try:
    r = requests.get(f"{BASE}/health", timeout=10)
    check_status("GET /health", r)
    d = r.json()
    report("/health returns status=ok", d.get("status") == "ok", f"got {d}")
except Exception as e:
    report("GET /health", False, str(e))

# ============================================================
# 2. DASHBOARD
# ============================================================
print("\n=== DASHBOARD ===")

# 2a. Resumen nacional
try:
    r = requests.get(f"{BASE}/dashboard/", timeout=10)
    check_status("GET /dashboard/", r)
    d = r.json()
    report("/dashboard/ has 'data' list", isinstance(d.get("data"), list) and len(d["data"]) > 0,
           f"data length={len(d.get('data', []))}")
    # Check structure
    if d.get("data"):
        row = d["data"][0]
        expected_keys = {"grupo_etnico", "pob_total", "pob_disc", "prevalencia_pct", "tasa_x_1000"}
        has_keys = expected_keys.issubset(set(row.keys()))
        report("/dashboard/ row has expected keys", has_keys,
               f"missing={expected_keys - set(row.keys())}" if not has_keys else "")
except Exception as e:
    report("GET /dashboard/", False, str(e))

# 2b. Prevalencia por departamento
try:
    r = requests.get(f"{BASE}/dashboard/prevalencia/departamento", timeout=10)
    check_status("GET /dashboard/prevalencia/departamento", r)
    d = r.json()
    report("/prevalencia/departamento has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0)
    # Test filter
    r2 = requests.get(f"{BASE}/dashboard/prevalencia/departamento", params={"grupo_etnico": "Indigena"}, timeout=10)
    check_status("GET /prevalencia/departamento?grupo_etnico=Indigena", r2)
    d2 = r2.json()
    if d2.get("data"):
        all_indigena = all(row["grupo_etnico"] == "Indigena" for row in d2["data"])
        report("grupo_etnico filter works", all_indigena,
               "" if all_indigena else "found non-Indigena rows")
except Exception as e:
    report("GET /dashboard/prevalencia/departamento", False, str(e))

# 2c. Prevalencia por municipio
try:
    r = requests.get(f"{BASE}/dashboard/prevalencia/municipio", timeout=10)
    check_status("GET /dashboard/prevalencia/municipio", r)
    d = r.json()
    report("/prevalencia/municipio has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0)
    # Check n>=30 filter is applied
    if d.get("data"):
        all_above_30 = all(row.get("pob_indigena", 0) >= 30 for row in d["data"])
        report("n>=30 filter applied on municipio prevalencia", all_above_30,
               "" if all_above_30 else "found municipios with pob_indigena < 30")
except Exception as e:
    report("GET /dashboard/prevalencia/municipio", False, str(e))

# 2d. Dificultades radar
try:
    r = requests.get(f"{BASE}/dashboard/dificultades", timeout=10)
    check_status("GET /dashboard/dificultades", r)
    d = r.json()
    report("/dificultades has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0)
except Exception as e:
    report("GET /dashboard/dificultades", False, str(e))

# 2e. Salud embudo
try:
    r = requests.get(f"{BASE}/dashboard/salud", timeout=10)
    check_status("GET /dashboard/salud", r)
    d = r.json()
    report("/salud has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0)
except Exception as e:
    report("GET /dashboard/salud", False, str(e))

# 2f. Intercensal
try:
    r = requests.get(f"{BASE}/dashboard/intercensal", timeout=10)
    check_status("GET /dashboard/intercensal", r)
    d = r.json()
    report("/dashboard/intercensal has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0,
           f"data length={len(d.get('data', []))}")
    if d.get("data"):
        row = d["data"][0]
        expected_keys = {"grupo_etnico", "periodo", "pob_total", "pob_disc", "prevalencia_pct", "tasa_x_1000"}
        has_keys = expected_keys.issubset(set(row.keys()))
        report("/intercensal row has expected keys", has_keys,
               f"missing={expected_keys - set(row.keys())}" if not has_keys else "")
    # Test filter
    r2 = requests.get(f"{BASE}/dashboard/intercensal", params={"grupo_etnico": "Indigena"}, timeout=10)
    check_status("GET /dashboard/intercensal?grupo_etnico=Indigena", r2)
    d2 = r2.json()
    if d2.get("data"):
        all_indigena = all(row["grupo_etnico"] == "Indigena" for row in d2["data"])
        report("intercensal grupo_etnico filter works", all_indigena,
               "" if all_indigena else "found non-Indigena rows")
except Exception as e:
    report("GET /dashboard/intercensal", False, str(e))

# 2g. SMT Resumen
try:
    r = requests.get(f"{BASE}/dashboard/smt-resumen", timeout=10)
    check_status("GET /dashboard/smt-resumen", r)
    d = r.json()
    report("/dashboard/smt-resumen has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0,
           f"data length={len(d.get('data', []))}")
    if d.get("data"):
        row = d["data"][0]
        expected_keys = {"dimension", "categoria", "valor", "pct"}
        has_keys = expected_keys.issubset(set(row.keys()))
        report("/smt-resumen row has expected keys", has_keys,
               f"missing={expected_keys - set(row.keys())}" if not has_keys else "")
    # Test dimension filter
    r2 = requests.get(f"{BASE}/dashboard/smt-resumen", params={"dimension": "region"}, timeout=10)
    check_status("GET /dashboard/smt-resumen?dimension=region", r2)
    d2 = r2.json()
    if d2.get("data"):
        all_region = all(row["dimension"] == "region" for row in d2["data"])
        report("smt-resumen dimension filter works", all_region,
               "" if all_region else "found non-region rows")
except Exception as e:
    report("GET /dashboard/smt-resumen", False, str(e))

# ============================================================
# 3. PUEBLOS
# ============================================================
print("\n=== PUEBLOS ===")

# 3a. Listar pueblos
try:
    r = requests.get(f"{BASE}/pueblos/", timeout=10)
    check_status("GET /pueblos/", r)
    d = r.json()
    report("/pueblos/ has 'data' list", isinstance(d.get("data"), list) and len(d["data"]) > 0,
           f"count={len(d.get('data', []))}")
    # Structure check
    if d.get("data"):
        row = d["data"][0]
        expected_keys = {"cod_pueblo", "pueblo", "con_discapacidad", "total", "tasa_x_1000", "confiabilidad"}
        has_keys = expected_keys.issubset(set(row.keys()))
        report("/pueblos/ row has confiabilidad field", has_keys,
               f"missing={expected_keys - set(row.keys())}" if not has_keys else "")
        # n>=30 filter
        all_above_30 = all(row.get("total", 0) >= 30 for row in d["data"])
        report("n>=30 filter applied on pueblos list", all_above_30)
except Exception as e:
    report("GET /pueblos/", False, str(e))

# 3b. Data quality: no prevalence > 200 per mil for pueblos with n>=100
try:
    r = requests.get(f"{BASE}/pueblos/", timeout=10)
    d = r.json()
    bad_rates = []
    for row in d.get("data", []):
        if row.get("total", 0) >= 100 and row.get("tasa_x_1000") is not None:
            if float(row["tasa_x_1000"]) > 200:
                bad_rates.append(f"{row['pueblo']}: {row['tasa_x_1000']}")
    report(
        "No prevalence > 200 per mil for pueblos with n>=100",
        len(bad_rates) == 0,
        f"found {len(bad_rates)}: {', '.join(bad_rates[:5])}" if bad_rates else "",
    )
except Exception as e:
    report("Data quality check", False, str(e))

# 3c. Perfil pueblo (Wayuu = 720)
try:
    r = requests.get(f"{BASE}/pueblos/720/perfil", timeout=10)
    check_status("GET /pueblos/720/perfil", r)
    d = r.json()
    expected_sections = {"prevalencia", "sexo", "piramide_edad", "limitaciones",
                         "tratamiento", "causas", "enfermedad", "confiabilidad"}
    has_sections = expected_sections.issubset(set(d.keys()))
    report("/pueblos/720/perfil has all sections + confiabilidad", has_sections,
           f"missing={expected_sections - set(d.keys())}" if not has_sections else "")
    # Check prevalencia sub-structure has confiabilidad
    if d.get("prevalencia"):
        has_conf = "confiabilidad" in d["prevalencia"]
        report("perfil prevalencia includes confiabilidad", has_conf)
except Exception as e:
    report("GET /pueblos/720/perfil", False, str(e))

# 3d. Perfil pueblo 404 for non-existent
try:
    r = requests.get(f"{BASE}/pueblos/ZZZ/perfil", timeout=10)
    check_status("GET /pueblos/ZZZ/perfil -> 404", r, 404)
except Exception as e:
    report("GET /pueblos/ZZZ/perfil -> 404", False, str(e))

# 3e. Territorios pueblo
try:
    r = requests.get(f"{BASE}/pueblos/720/territorios", timeout=10)
    check_status("GET /pueblos/720/territorios", r)
    d = r.json()
    report("/pueblos/720/territorios has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0)
    # Check confiabilidad in territory rows
    if d.get("data"):
        has_conf = "confiabilidad" in d["data"][0]
        report("territorios rows include confiabilidad", has_conf)
except Exception as e:
    report("GET /pueblos/720/territorios", False, str(e))

# 3f. Territorios 404 for non-existent
try:
    r = requests.get(f"{BASE}/pueblos/ZZZ/territorios", timeout=10)
    check_status("GET /pueblos/ZZZ/territorios -> 404", r, 404)
except Exception as e:
    report("GET /pueblos/ZZZ/territorios -> 404", False, str(e))

# 3g. Pueblos en municipio
try:
    r = requests.get(f"{BASE}/pueblos/por-municipio/05001", timeout=10)
    check_status("GET /pueblos/por-municipio/05001", r)
    d = r.json()
    report("/pueblos/por-municipio has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0)
except Exception as e:
    report("GET /pueblos/por-municipio/05001", False, str(e))

# ============================================================
# 4. CONFLICTO
# ============================================================
print("\n=== CONFLICTO ===")

# 4a. Victimas resumen
try:
    r = requests.get(f"{BASE}/conflicto/victimas/resumen", timeout=10)
    check_status("GET /conflicto/victimas/resumen", r)
    d = r.json()
    report("/victimas/resumen has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0)
except Exception as e:
    report("GET /conflicto/victimas/resumen", False, str(e))

# 4b. Victimas hechos
try:
    r = requests.get(f"{BASE}/conflicto/victimas/hechos", timeout=10)
    check_status("GET /conflicto/victimas/hechos", r)
    d = r.json()
    report("/victimas/hechos has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0)
    # Test filter by departamento
    r2 = requests.get(f"{BASE}/conflicto/victimas/hechos", params={"cod_dpto": "05"}, timeout=10)
    check_status("GET /victimas/hechos?cod_dpto=05", r2)
    d2 = r2.json()
    if d2.get("data"):
        all_05 = all(row.get("cod_dpto") == "05" for row in d2["data"])
        report("cod_dpto filter works on hechos", all_05)
except Exception as e:
    report("GET /conflicto/victimas/hechos", False, str(e))

# 4c. Victimas por pueblo - by code
try:
    r = requests.get(f"{BASE}/conflicto/victimas/pueblo/720", timeout=10)
    check_status("GET /conflicto/victimas/pueblo/720 (by code)", r)
    d = r.json()
    report("/victimas/pueblo/720 has data", d.get("total", 0) > 0,
           f"total={d.get('total', 0)}")
    report("/victimas/pueblo response has 'pueblo' field", "pueblo" in d,
           f"keys={list(d.keys())}" if "pueblo" not in d else "")
except Exception as e:
    report("GET /conflicto/victimas/pueblo/720", False, str(e))

# 4d. Victimas por pueblo - by name
try:
    r = requests.get(f"{BASE}/conflicto/victimas/pueblo/Wayuu", timeout=10)
    check_status("GET /conflicto/victimas/pueblo/Wayuu (by name)", r)
    d = r.json()
    report("/victimas/pueblo/Wayuu finds data", d.get("total", 0) > 0,
           f"total={d.get('total', 0)}")
except Exception as e:
    report("GET /conflicto/victimas/pueblo/Wayuu", False, str(e))

# 4e. Victimas por pueblo - 404 for non-existent
try:
    r = requests.get(f"{BASE}/conflicto/victimas/pueblo/NOEXISTE_XYZ_999", timeout=10)
    check_status("GET /conflicto/victimas/pueblo/NOEXISTE -> 404", r, 404)
except Exception as e:
    report("GET /conflicto/victimas/pueblo/NOEXISTE -> 404", False, str(e))

# ============================================================
# 5. GEO
# ============================================================
print("\n=== GEO ===")

# 5a. Departamentos GeoJSON
try:
    r = requests.get(f"{BASE}/geo/departamentos", timeout=30)
    check_status("GET /geo/departamentos", r)
    d = r.json()
    check_geojson("/geo/departamentos", d)
    report("/geo/departamentos has >0 features", len(d.get("features", [])) > 0,
           f"count={len(d.get('features', []))}")
except Exception as e:
    report("GET /geo/departamentos", False, str(e))

# 5b. Departamentos with prevalencia
try:
    r = requests.get(f"{BASE}/geo/departamentos", params={"incluir_prevalencia": True}, timeout=30)
    check_status("GET /geo/departamentos?incluir_prevalencia=true", r)
    d = r.json()
    if d.get("features"):
        props = d["features"][0].get("properties", {})
        has_prev = "tasa_x_1000" in props or "prevalencia_pct" in props
        report("departamentos+prevalencia has rate fields", has_prev,
               f"keys={list(props.keys())}" if not has_prev else "")
except Exception as e:
    report("GET /geo/departamentos?incluir_prevalencia", False, str(e))

# 5c. Municipios GeoJSON
try:
    r = requests.get(f"{BASE}/geo/municipios", params={"cod_dpto": "05"}, timeout=30)
    check_status("GET /geo/municipios?cod_dpto=05", r)
    d = r.json()
    check_geojson("/geo/municipios?cod_dpto=05", d)
except Exception as e:
    report("GET /geo/municipios", False, str(e))

# 5d. Resguardos list
try:
    r = requests.get(f"{BASE}/geo/resguardos", timeout=10)
    check_status("GET /geo/resguardos", r)
    d = r.json()
    report("/geo/resguardos has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0,
           f"count={len(d.get('data', []))}")
except Exception as e:
    report("GET /geo/resguardos", False, str(e))

# 5e. SMT Macrorregiones GeoJSON
try:
    r = requests.get(f"{BASE}/geo/smt/macrorregiones", timeout=30)
    check_status("GET /geo/smt/macrorregiones", r)
    d = r.json()
    check_geojson("/geo/smt/macrorregiones", d)
    report("macrorregiones has 5 features", len(d.get("features", [])) == 5,
           f"count={len(d.get('features', []))}")
except Exception as e:
    report("GET /geo/smt/macrorregiones", False, str(e))

# 5f. SMT Resguardos GeoJSON
try:
    r = requests.get(f"{BASE}/geo/smt/resguardos", timeout=60)
    check_status("GET /geo/smt/resguardos", r)
    d = r.json()
    check_geojson("/geo/smt/resguardos", d)
    report("smt/resguardos has >100 features", len(d.get("features", [])) > 100,
           f"count={len(d.get('features', []))}")
except Exception as e:
    report("GET /geo/smt/resguardos", False, str(e))

# 5g. SMT Comunidades GeoJSON
try:
    r = requests.get(f"{BASE}/geo/smt/comunidades", timeout=60)
    check_status("GET /geo/smt/comunidades", r)
    d = r.json()
    check_geojson("/geo/smt/comunidades", d)
except Exception as e:
    report("GET /geo/smt/comunidades", False, str(e))

# 5h. SMT Comunidades with filter
try:
    r = requests.get(f"{BASE}/geo/smt/comunidades", params={"cod_dpto": "05"}, timeout=30)
    check_status("GET /geo/smt/comunidades?cod_dpto=05", r)
except Exception as e:
    report("GET /geo/smt/comunidades?cod_dpto=05", False, str(e))

# ============================================================
# 6. INDICADORES
# ============================================================
print("\n=== INDICADORES ===")

# 6a. Listar definiciones
try:
    r = requests.get(f"{BASE}/indicadores/", timeout=10)
    check_status("GET /indicadores/", r)
    d = r.json()
    report("/indicadores/ has 'data'", isinstance(d.get("data"), list) and len(d["data"]) > 0,
           f"count={len(d.get('data', []))}")
    if d.get("data"):
        row = d["data"][0]
        expected_keys = {"codigo", "nombre", "grupo", "formula", "unidad"}
        has_keys = expected_keys.issubset(set(row.keys()))
        report("indicador definition has expected keys", has_keys)
        # Get a code for further testing
        test_codigo = d["data"][0]["codigo"]
except Exception as e:
    report("GET /indicadores/", False, str(e))
    test_codigo = None

# 6b. Valores
try:
    r = requests.get(f"{BASE}/indicadores/valores", timeout=10)
    check_status("GET /indicadores/valores", r)
    d = r.json()
    report("/indicadores/valores has 'data'", isinstance(d.get("data"), list))
except Exception as e:
    report("GET /indicadores/valores", False, str(e))

# 6c. Valores with filter
try:
    r = requests.get(f"{BASE}/indicadores/valores", params={"periodo": "2018", "nivel_geo": "nacional"}, timeout=10)
    check_status("GET /indicadores/valores?periodo=2018&nivel_geo=nacional", r)
    d = r.json()
    if d.get("data"):
        all_nacional = all(row["nivel_geo"] == "nacional" for row in d["data"])
        report("nivel_geo filter works on valores", all_nacional)
except Exception as e:
    report("GET /indicadores/valores filtered", False, str(e))

# 6d. Serie tiempo
try:
    if test_codigo:
        r = requests.get(f"{BASE}/indicadores/serie-tiempo/{test_codigo}", timeout=10)
        check_status(f"GET /indicadores/serie-tiempo/{test_codigo}", r)
        d = r.json()
        report("serie-tiempo has 'indicador' and 'serie'",
               "indicador" in d and "serie" in d,
               f"keys={list(d.keys())}")
    else:
        report("GET /indicadores/serie-tiempo (skipped)", False, "no test_codigo available")
except Exception as e:
    report("GET /indicadores/serie-tiempo", False, str(e))

# 6e. Serie tiempo 404 for non-existent
try:
    r = requests.get(f"{BASE}/indicadores/serie-tiempo/NOEXISTE-000", timeout=10)
    check_status("GET /indicadores/serie-tiempo/NOEXISTE -> 404", r, 404)
except Exception as e:
    report("GET /indicadores/serie-tiempo/NOEXISTE -> 404", False, str(e))


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 60)

if errors:
    print("\nFailed tests:")
    for e in errors:
        print(f"  - {e}")

sys.exit(0 if failed == 0 else 1)
