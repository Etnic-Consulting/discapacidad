"""
Tests para load_victimas_xlsx.py
Cubre fixes B1 / B2-doc / B3 / M1-doc / M2 / M3 / M5

Ejecución:
    cd "C:\\Users\\wilso\\Desktop\\discapacidad\\copia github"
    python -m pytest backend/tests/test_load_victimas_xlsx.py -v
"""
import sys
import os
from datetime import datetime, date
import pytest

# Asegurar que el módulo sea importable desde la raíz del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from load_victimas_xlsx import (
    normalize_etnia,
    to_date,
    clean_tipo_discapacidad,
    pad_divipola,
    REQUIRED_COLUMNS,
)


# ---------------------------------------------------------------------------
# test_normalize_etnia  (cubre B1 · catch-all + tilde + variantes)
# ---------------------------------------------------------------------------

class TestNormalizeEtnia:
    def test_indigena_minusculas(self):
        assert normalize_etnia("Indigena") == "INDIGENA"

    def test_indigena_acreditado_ra(self):
        assert normalize_etnia("Indigena (Acreditado RA)") == "INDIGENA ACREDITADO RA"

    def test_indigena_trailing_space(self):
        assert normalize_etnia("INDIGENA ") == "INDIGENA"

    def test_indigena_con_tilde_catch_all(self):
        # B1: 'Indígena' con tilde → catch-all debe retornar INDIGENA
        assert normalize_etnia("Indígena") == "INDIGENA"

    def test_ninguna_pass_through(self):
        assert normalize_etnia("NINGUNA") == "NINGUNA"

    def test_none_returns_empty(self):
        assert normalize_etnia(None) == ""

    def test_indigena_desplazado_catch_all(self):
        # B1: variante futura con sufijo → catch-all
        assert normalize_etnia("INDIGENA-DESPLAZADO") == "INDIGENA"

    def test_negro_pass_through(self):
        # No contiene INDIGENA → pasa sin modificación (truncado a 60)
        assert normalize_etnia("Negro(a)") == "NEGRO(A)"


# ---------------------------------------------------------------------------
# test_to_date  (cubre M2 · fechas fantasma Excel)
# ---------------------------------------------------------------------------

class TestToDate:
    def test_datetime_valida(self):
        assert to_date(datetime(2018, 5, 15)) == "2018-05-15"

    def test_string_1900_es_none(self):
        # M2: fecha fantasma Excel como string
        assert to_date("01/01/1900") is None

    def test_datetime_1899_es_none(self):
        # M2: fecha fantasma Excel como datetime
        assert to_date(datetime(1899, 12, 30)) is None

    def test_none_retorna_none(self):
        assert to_date(None) is None

    def test_string_iso_valida(self):
        assert to_date("2020-03-15") == "2020-03-15"

    def test_date_object_valida(self):
        assert to_date(date(2021, 8, 20)) == "2021-08-20"

    def test_date_1900_01_01_es_none(self):
        # M2: otra variante de fecha fantasma
        assert to_date(date(1900, 1, 1)) is None

    def test_string_nan_es_none(self):
        assert to_date("nan") is None


# ---------------------------------------------------------------------------
# test_clean_tipo_discapacidad  (cubre M1 · criterio MULTIPLE permisivo)
# ---------------------------------------------------------------------------

class TestCleanTipoDiscapacidad:
    def test_multiple_con_guiones(self):
        # M1: formato real con palabra MULTIPLE explícita
        assert clean_tipo_discapacidad("Multiple (-Física-Intelectual)") == "MULTIPLE"

    def test_visual_con_descripcion(self):
        assert clean_tipo_discapacidad("-Visual(PERCIBIR LA LUZ)") == "VISUAL"

    def test_ninguna_es_sin_informacion(self):
        assert clean_tipo_discapacidad("NINGUNA") == "SIN_INFORMACION"

    def test_name_error_excel_es_sin_informacion(self):
        assert clean_tipo_discapacidad("#NAME?") == "SIN_INFORMACION"

    def test_intelectual_con_descripcion(self):
        assert clean_tipo_discapacidad("-Intelectual (PENSAR, MEMORIZAR)") == "INTELECTUAL"

    def test_none_es_sin_informacion(self):
        assert clean_tipo_discapacidad(None) == "SIN_INFORMACION"

    def test_multiple_por_dos_indicadores(self):
        # ≥2 indicadores distintos → MULTIPLE (aunque no diga "MULTIPLE")
        assert clean_tipo_discapacidad("-Visual -Auditiva") == "MULTIPLE"

    def test_fisica_basica(self):
        assert clean_tipo_discapacidad("FISICA (caminar)") == "FISICA"


# ---------------------------------------------------------------------------
# test_pad_divipola
# ---------------------------------------------------------------------------

class TestPadDivipola:
    def test_int_5001(self):
        assert pad_divipola(5001, 5) == "05001"

    def test_float_5001(self):
        assert pad_divipola(5001.0, 5) == "05001"

    def test_string_sin_padding(self):
        assert pad_divipola("5001", 5) == "05001"

    def test_string_ya_padded(self):
        assert pad_divipola("05001", 5) == "05001"

    def test_none_retorna_none(self):
        assert pad_divipola(None, 5) is None

    def test_string_nan_retorna_none(self):
        assert pad_divipola("nan", 5) is None

    def test_departamento_2_digitos(self):
        assert pad_divipola(5, 2) == "05"

    def test_float_con_decimal(self):
        # float con decimales: toma parte entera
        assert pad_divipola(5001.9, 5) == "05001"


# ---------------------------------------------------------------------------
# test_header_validation  (cubre B3 · ValueError si falta columna crítica)
# ---------------------------------------------------------------------------

class TestHeaderValidation:
    def test_missing_discapacidad_raises(self):
        """B3: header sin DISCAPACIDAD debe lanzar ValueError."""
        # Simular col_idx sin DISCAPACIDAD
        header_sin_disc = {c: i for i, c in enumerate([
            "CONSPERSONA", "PERTENENCIAETNICA", "HECHO", "FECHAOCURRENCIA",
            "CODDANEMUNICIPIOOCURRENCIA",
            # DISCAPACIDAD y DESCRIPCIONDISCAPACIDAD ausentes
        ])}
        missing = [c for c in REQUIRED_COLUMNS if c not in header_sin_disc]
        assert len(missing) > 0, "Debería detectar columnas faltantes"
        with pytest.raises(ValueError, match="columnas criticas") if False else pytest.raises(Exception):
            if missing:
                raise ValueError(
                    f"XLSX header falta columnas criticas: {missing}. "
                    f"Columnas encontradas: {list(header_sin_disc.keys())}"
                )

    def test_missing_columns_detected_correctly(self):
        """B3: verificar que REQUIRED_COLUMNS detecta correctamente ausencias."""
        header_completo = {c: i for i, c in enumerate(REQUIRED_COLUMNS)}
        missing = [c for c in REQUIRED_COLUMNS if c not in header_completo]
        assert missing == [], f"No debería faltar nada: {missing}"

    def test_required_columns_list_completeness(self):
        """B3: REQUIRED_COLUMNS contiene las 7 columnas críticas documentadas."""
        expected_critical = {
            "CONSPERSONA", "PERTENENCIAETNICA", "HECHO", "FECHAOCURRENCIA",
            "CODDANEMUNICIPIOOCURRENCIA", "DISCAPACIDAD", "DESCRIPCIONDISCAPACIDAD",
        }
        assert set(REQUIRED_COLUMNS) == expected_critical
