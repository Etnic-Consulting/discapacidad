"""
test_load_ruv_hechos_municipal.py
K02 · Sprint S3_completitud · SMT-ONIC

3 tests acotados: columnas CSV, pad DIVIPOLA, cast int con strings vacíos.
"""

import sys
import os
import pandas as pd
import pytest

# Helpers copiados del script (no importar el script directamente para evitar
# que el módulo ejecute la carga al importar)

def pad_dpto(val) -> str | None:
    """'5' -> '05', deja '05' como '05'. Recibe string."""
    if val is None or str(val).strip() == "":
        return None
    s = str(int(float(str(val).strip())))
    return s.zfill(2)


def pad_mpio(val) -> str | None:
    """'5001' -> '05001', '11001' -> '11001'."""
    if val is None or str(val).strip() == "":
        return None
    s = str(int(float(str(val).strip())))
    return s.zfill(5)


def safe_int(val) -> int | None:
    """'' -> None, '5' -> 5, '5.0' -> 5, None -> None."""
    if val is None:
        return None
    s = str(val).strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


# ── Tests ─────────────────────────────────────────────────────────────────────

CSV_PATH = r"C:\Users\wilso\Desktop\discapacidad\fuentes_externas\RUV\ruv_hechos_municipal_indigena.csv"

EXPECTED_COLS = {
    "fecha_corte", "nom_rpt", "cod_pais", "pais",
    "cod_estado_depto", "estado_depto",
    "cod_ciudad_muni", "ciudad_municipio",
    "param_hecho", "hecho", "etnia", "sexo",
    "discapacidad", "ciclo_vital",
    "per_ocu", "per_decla", "per_ubic", "per_sa", "eventos",
}


def test_csv_columns_match_expected():
    """El CSV tiene exactamente las 19 columnas esperadas."""
    df = pd.read_csv(CSV_PATH, nrows=0, dtype=str)
    actual = set(df.columns.tolist())
    assert actual == EXPECTED_COLS, (
        f"Columnas faltantes: {EXPECTED_COLS - actual}  |  "
        f"Columnas extra: {actual - EXPECTED_COLS}"
    )


def test_pad_dpto_2chars():
    """pad_dpto normaliza a exactamente 2 chars."""
    assert pad_dpto("5") == "05"
    assert pad_dpto("05") == "05"
    assert pad_dpto("11") == "11"
    assert pad_dpto("99") == "99"
    assert pad_dpto("") is None
    assert pad_dpto(None) is None


def test_pad_mpio_5chars():
    """pad_mpio normaliza a exactamente 5 chars."""
    assert pad_mpio("5001") == "05001"
    assert pad_mpio("05001") == "05001"
    assert pad_mpio("11001") == "11001"
    assert pad_mpio("") is None
    assert pad_mpio(None) is None


def test_int_cast_handles_empty():
    """safe_int maneja strings vacíos, floats y None sin error."""
    assert safe_int("") is None
    assert safe_int(None) is None
    assert safe_int("5") == 5
    assert safe_int("5.0") == 5
    assert safe_int("0") == 0
    assert safe_int("996") == 996
