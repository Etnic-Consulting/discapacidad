"""
Carga geometrias del SMT-ONIC (SpatiaLite) a PostGIS.
Usa geopandas como puente: lee SpatiaLite, escribe PostGIS.
"""
import os
import sys

import geopandas as gpd
from sqlalchemy import create_engine, text

DB_URL = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql://smt_admin:smt_onic_2026@localhost:5450/smt_onic",
)
SPATIALITE_PATH = os.environ.get(
    "SPATIALITE_PATH",
    "D:/1.Programacion/1.onic-smt-dashboard/my_smt_cmp_gdb_ambito_onic/"
    "my_smt_cmp_gdb_ambito_onic/my_smt_cmp_gdb_ambito_onic.sqlite",
)

LAYERS = [
    {
        "sqlite_table": "my_smt_cmp_macrorregiones_onic_v1",
        "pg_table": "macrorregiones",
        "pg_schema": "smt_geo",
    },
    {
        "sqlite_table": "my_smt_cmp_resguardos_ambito_onic_v1",
        "pg_table": "resguardos",
        "pg_schema": "smt_geo",
    },
    {
        "sqlite_table": "my_smt_cmp_comunidades_v1",
        "pg_table": "comunidades",
        "pg_schema": "smt_geo",
    },
    {
        "sqlite_table": "my_smt_cmp_cluster_viviendas_v1",
        "pg_table": "cluster_viviendas",
        "pg_schema": "smt_geo",
    },
    {
        "sqlite_table": "my_smt_cmp_expectativas_ancestrales_v1",
        "pg_table": "expectativas_ancestrales",
        "pg_schema": "smt_geo",
    },
]


def main():
    print("=" * 60)
    print("  CARGA DE GEOMETRIAS SMT-ONIC -> PostGIS")
    print("  Fuente: SpatiaLite -> geopandas -> PostGIS")
    print("=" * 60)

    if not os.path.exists(SPATIALITE_PATH):
        print(f"ERROR: No se encuentra {SPATIALITE_PATH}")
        sys.exit(1)

    engine = create_engine(DB_URL)

    for layer in LAYERS:
        sqlite_table = layer["sqlite_table"]
        pg_table = layer["pg_table"]
        pg_schema = layer["pg_schema"]

        print(f"\n  Cargando {sqlite_table} -> {pg_schema}.{pg_table}...")

        try:
            # Read from SpatiaLite using geopandas (handles geometry automatically)
            gdf = gpd.read_file(SPATIALITE_PATH, layer=sqlite_table)
            print(f"    Leido: {len(gdf)} filas, CRS={gdf.crs}")

            # Reproject to EPSG:4326 if needed
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
                print(f"    Reproyectado a EPSG:4326")

            # Drop and recreate table (let geopandas define geometry column)
            with engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {pg_schema}.{pg_table} CASCADE"))
                conn.commit()

            # Write to PostGIS (creates table with 'geometry' column)
            gdf.to_postgis(
                name=pg_table,
                con=engine,
                schema=pg_schema,
                if_exists="replace",
                index=False,
            )
            print(f"    OK: {len(gdf)} filas escritas en {pg_schema}.{pg_table}")

        except Exception as e:
            print(f"    ERROR: {e}")
            continue

    # Verify
    print(f"\n{'=' * 60}")
    print("  VERIFICACION")
    print(f"{'=' * 60}")
    with engine.connect() as conn:
        for layer in LAYERS:
            pg_table = layer["pg_table"]
            pg_schema = layer["pg_schema"]
            result = conn.execute(text(
                f"SELECT COUNT(*), SUM(CASE WHEN geometry IS NOT NULL THEN 1 ELSE 0 END) "
                f"FROM {pg_schema}.{pg_table}"
            ))
            total, with_geom = result.fetchone()
            print(f"  {pg_schema}.{pg_table}: {total} filas, {with_geom} con geometria")

    engine.dispose()
    print("\n  Carga de geometrias completada.")


if __name__ == "__main__":
    main()
