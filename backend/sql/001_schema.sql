-- ================================================================
-- SMT-ONIC: Sistema de Monitoreo Territorial
-- Modulo de Discapacidad / Capacidades Diversas - Pueblos Indigenas
-- PostgreSQL 16 + PostGIS 3.4
-- ================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- ================================================================
-- SCHEMA: geo (Entidades geograficas con PostGIS)
-- ================================================================
CREATE SCHEMA IF NOT EXISTS geo;

CREATE TABLE geo.departamentos (
    cod_dpto    VARCHAR(2) PRIMARY KEY,
    nom_dpto    VARCHAR(100) NOT NULL,
    geom        GEOMETRY(MultiPolygon, 4326),
    area_km2    NUMERIC(12,2)
);
CREATE INDEX idx_dpto_geom ON geo.departamentos USING GIST (geom);

CREATE TABLE geo.municipios (
    cod_mpio    VARCHAR(5) PRIMARY KEY,
    cod_dpto    VARCHAR(2) NOT NULL REFERENCES geo.departamentos(cod_dpto),
    nom_mpio    VARCHAR(150) NOT NULL,
    geom        GEOMETRY(MultiPolygon, 4326),
    area_km2    NUMERIC(12,2)
);
CREATE INDEX idx_mpio_geom ON geo.municipios USING GIST (geom);
CREATE INDEX idx_mpio_dpto ON geo.municipios(cod_dpto);

CREATE TABLE geo.resguardos (
    cod_resguardo   VARCHAR(10) PRIMARY KEY,
    nombre          VARCHAR(200) NOT NULL,
    cod_mpio        VARCHAR(5),
    nom_departamento VARCHAR(100),
    nom_municipio   VARCHAR(150),
    poblacion_proy  INTEGER,
    geom            GEOMETRY(MultiPolygon, 4326)
);
CREATE INDEX idx_resg_geom ON geo.resguardos USING GIST (geom);
CREATE INDEX idx_resg_mpio ON geo.resguardos(cod_mpio);

-- Un resguardo puede estar en multiples municipios
CREATE TABLE geo.resguardo_municipio (
    cod_resguardo VARCHAR(10) REFERENCES geo.resguardos(cod_resguardo),
    cod_mpio      VARCHAR(5) REFERENCES geo.municipios(cod_mpio),
    poblacion     INTEGER,
    PRIMARY KEY (cod_resguardo, cod_mpio)
);

-- ================================================================
-- SCHEMA: cat (Catalogos / dimensiones)
-- ================================================================
CREATE SCHEMA IF NOT EXISTS cat;

CREATE TABLE cat.grupos_etnicos (
    cod_grupo    SMALLINT PRIMARY KEY,
    nombre       VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO cat.grupos_etnicos VALUES
    (1,'Indigena'),(2,'Gitano_Rrom'),(3,'Raizal'),
    (4,'Palenquero'),(5,'Afrodescendiente'),(6,'Ningun_grupo'),
    (7,'No_informa'),(8,'Total');

CREATE TABLE cat.pueblos_indigenas (
    cod_pueblo  VARCHAR(3) PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL
);

CREATE TABLE cat.dificultades (
    cod_dificultad SMALLINT PRIMARY KEY,
    nombre         VARCHAR(50) NOT NULL
);
INSERT INTO cat.dificultades VALUES
    (1,'Oir'),(2,'Hablar'),(3,'Ver'),(4,'Caminar'),
    (5,'Agarrar'),(6,'Aprender/decidir'),(7,'Comer/vestir'),
    (8,'Actividades diarias'),(9,'Relacionarse'),(0,'No informa');

CREATE TABLE cat.causas_discapacidad (
    cod_causa SMALLINT PRIMARY KEY,
    nombre    VARCHAR(100) NOT NULL
);

CREATE TABLE cat.tratamientos (
    cod_tratamiento SMALLINT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL
);

-- ================================================================
-- SCHEMA: cnpv (Datos ORIGINALES CNPV 2018 - sin modificar)
-- Cada tabla tiene periodo para soportar series de tiempo futuras
-- ================================================================
CREATE SCHEMA IF NOT EXISTS cnpv;
COMMENT ON SCHEMA cnpv IS 'Datos ORIGINALES del CNPV 2018. Fuente censal.';

CREATE TABLE cnpv.prevalencia_etnia_dpto (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    grupo_etnico    VARCHAR(50) NOT NULL,
    pob_total       INTEGER NOT NULL,
    pob_disc        INTEGER NOT NULL,
    pob_no_disc     INTEGER NOT NULL,
    tasa_x_1000     NUMERIC(8,2),
    prevalencia_pct NUMERIC(6,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_dpto, grupo_etnico)
);

CREATE TABLE cnpv.prevalencia_etnia_mpio (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    cod_mpio        VARCHAR(5) NOT NULL,
    grupo_etnico    VARCHAR(50) NOT NULL,
    pob_total       INTEGER NOT NULL,
    pob_disc        INTEGER NOT NULL,
    tasa_x_1000     NUMERIC(8,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_mpio, grupo_etnico)
);

CREATE TABLE cnpv.dificultades_etnia_dpto (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    grupo_etnico    VARCHAR(50) NOT NULL,
    dificultad      VARCHAR(30) NOT NULL,
    pob_total       INTEGER NOT NULL,
    con_dificultad  INTEGER NOT NULL,
    tasa_x_1000     NUMERIC(8,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_dpto, grupo_etnico, dificultad)
);

CREATE TABLE cnpv.salud_etnia_dpto (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    grupo_etnico    VARCHAR(50) NOT NULL,
    variable        VARCHAR(30) NOT NULL,
    categoria       VARCHAR(100) NOT NULL,
    valor           INTEGER NOT NULL,
    pct             NUMERIC(6,2),
    total_grupo     INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_dpto, grupo_etnico, variable, categoria)
);

CREATE TABLE cnpv.disc_edad_dpto (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    grupo_edad      VARCHAR(30) NOT NULL,
    discapacidad    VARCHAR(10) NOT NULL,
    valor           INTEGER NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_dpto, grupo_edad, discapacidad)
);

CREATE TABLE cnpv.disc_sexo_dpto (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    sexo            VARCHAR(20) NOT NULL,
    discapacidad    VARCHAR(10) NOT NULL,
    valor           INTEGER NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_dpto, sexo, discapacidad)
);

CREATE TABLE cnpv.disc_indigena_mpio (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    cod_mpio        VARCHAR(5) NOT NULL,
    pob_indigena    INTEGER NOT NULL,
    con_disc        INTEGER NOT NULL,
    tasa_x_1000     NUMERIC(8,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_mpio)
);

CREATE TABLE cnpv.resumen_nacional_etnico (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    grupo_etnico    VARCHAR(50) NOT NULL,
    pob_total       BIGINT NOT NULL,
    pob_disc        INTEGER NOT NULL,
    prevalencia_pct NUMERIC(6,2),
    tasa_x_1000     NUMERIC(8,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, grupo_etnico)
);

CREATE TABLE cnpv.causa_disc_etnia_dpto (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    grupo_etnico    VARCHAR(50) NOT NULL,
    causa           VARCHAR(100) NOT NULL,
    valor           INTEGER NOT NULL,
    pct             NUMERIC(6,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_dpto, grupo_etnico, causa)
);

CREATE TABLE cnpv.limitacion_ppal_etnia_dpto (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    grupo_etnico    VARCHAR(50) NOT NULL,
    limitacion      VARCHAR(200) NOT NULL,
    valor           INTEGER NOT NULL,
    pct             NUMERIC(6,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_dpto, grupo_etnico, limitacion)
);

-- ================================================================
-- SCHEMA: pueblo (Datos por PUEBLO INDIGENA - REDATAM CNPV 2018)
-- ================================================================
CREATE SCHEMA IF NOT EXISTS pueblo;
COMMENT ON SCHEMA pueblo IS 'Datos por pueblo indigena especifico. Fuente: REDATAM CNPV 2018.';

CREATE TABLE pueblo.disc_nacional (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_pueblo      VARCHAR(3) NOT NULL,
    pueblo          VARCHAR(100) NOT NULL,
    con_discapacidad INTEGER NOT NULL,
    sin_discapacidad INTEGER NOT NULL,
    total           INTEGER NOT NULL,
    prevalencia_pct NUMERIC(6,2),
    tasa_x_1000     NUMERIC(8,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_pueblo)
);

CREATE TABLE pueblo.pueblo_municipio (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_mpio        VARCHAR(5) NOT NULL,
    cod_pueblo      VARCHAR(3) NOT NULL,
    pueblo          VARCHAR(100) NOT NULL,
    poblacion       INTEGER NOT NULL,
    pct_en_mpio     NUMERIC(6,1),
    es_dominante    VARCHAR(2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_mpio, cod_pueblo)
);
CREATE INDEX idx_pm_mpio ON pueblo.pueblo_municipio(cod_mpio);
CREATE INDEX idx_pm_pueblo ON pueblo.pueblo_municipio(cod_pueblo);

CREATE TABLE pueblo.pueblo_dominante_mpio (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_mpio        VARCHAR(5) NOT NULL,
    pueblo_dominante VARCHAR(100) NOT NULL,
    pob_dominante   INTEGER NOT NULL,
    pob_total_indig INTEGER NOT NULL,
    pct_dominante   NUMERIC(6,1),
    n_pueblos       INTEGER,
    confianza       VARCHAR(10) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_mpio)
);

CREATE TABLE pueblo.disc_dpto (
    id              SERIAL PRIMARY KEY,
    periodo         VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_dpto        VARCHAR(2) NOT NULL,
    cod_pueblo      VARCHAR(3) NOT NULL,
    pueblo          VARCHAR(100) NOT NULL,
    con_discapacidad INTEGER NOT NULL,
    sin_discapacidad INTEGER NOT NULL,
    total           INTEGER NOT NULL,
    tasa_x_1000     NUMERIC(8,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_dpto, cod_pueblo)
);

CREATE TABLE pueblo.sexo_nacional (
    id         SERIAL PRIMARY KEY,
    periodo    VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_pueblo VARCHAR(3) NOT NULL,
    pueblo     VARCHAR(100) NOT NULL,
    hombres    INTEGER NOT NULL,
    mujeres    INTEGER NOT NULL,
    total      INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_pueblo)
);

CREATE TABLE pueblo.edad_nacional (
    id         SERIAL PRIMARY KEY,
    periodo    VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_pueblo VARCHAR(3) NOT NULL,
    pueblo     VARCHAR(100) NOT NULL,
    grupo_edad VARCHAR(10) NOT NULL,
    valor      INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_pueblo, grupo_edad)
);

CREATE TABLE pueblo.limitacion_nacional (
    id          SERIAL PRIMARY KEY,
    periodo     VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_pueblo  VARCHAR(3) NOT NULL,
    pueblo      VARCHAR(100) NOT NULL,
    limitacion  VARCHAR(50) NOT NULL,
    valor       INTEGER NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_pueblo, limitacion)
);

CREATE TABLE pueblo.enfermo_nacional (
    id          SERIAL PRIMARY KEY,
    periodo     VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_pueblo  VARCHAR(3) NOT NULL,
    pueblo      VARCHAR(100) NOT NULL,
    enfermo_si  INTEGER NOT NULL,
    enfermo_no  INTEGER NOT NULL,
    no_informa  INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_pueblo)
);

CREATE TABLE pueblo.tratamiento_nacional (
    id           SERIAL PRIMARY KEY,
    periodo      VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_pueblo   VARCHAR(3) NOT NULL,
    pueblo       VARCHAR(100) NOT NULL,
    tratamiento  VARCHAR(100) NOT NULL,
    valor        INTEGER NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_pueblo, tratamiento)
);

CREATE TABLE pueblo.causa_nacional (
    id         SERIAL PRIMARY KEY,
    periodo    VARCHAR(10) NOT NULL DEFAULT '2018',
    cod_pueblo VARCHAR(3) NOT NULL,
    pueblo     VARCHAR(100) NOT NULL,
    causa      VARCHAR(100) NOT NULL,
    valor      INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (periodo, cod_pueblo, causa)
);

-- ================================================================
-- SCHEMA: ext (Fuentes externas - datos originales)
-- ================================================================
CREATE SCHEMA IF NOT EXISTS ext;
COMMENT ON SCHEMA ext IS 'Fuentes externas: RUV, ICBF, RLCPD, ANT. Datos originales.';

CREATE TABLE ext.ruv_hechos_municipal (
    id               SERIAL PRIMARY KEY,
    fecha_corte      DATE,
    cod_dpto         VARCHAR(2),
    estado_depto     VARCHAR(100),
    cod_mpio         VARCHAR(5),
    ciudad_municipio VARCHAR(150),
    hecho            VARCHAR(200),
    etnia            VARCHAR(100),
    sexo             VARCHAR(30),
    discapacidad     VARCHAR(50),
    ciclo_vital      VARCHAR(30),
    per_ocu          INTEGER,
    per_sa           INTEGER,
    eventos          INTEGER,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ruv_mpio ON ext.ruv_hechos_municipal(cod_mpio);
CREATE INDEX idx_ruv_etnia ON ext.ruv_hechos_municipal(etnia);

CREATE TABLE ext.icbf_beneficiarios (
    id                    SERIAL PRIMARY KEY,
    anio                  SMALLINT,
    cod_dpto              VARCHAR(2),
    departamento          VARCHAR(100),
    cod_mpio              VARCHAR(5),
    municipio             VARCHAR(150),
    area_misional         VARCHAR(100),
    nombre_servicio       VARCHAR(200),
    rango_edad            VARCHAR(30),
    sexo                  VARCHAR(20),
    zona_ubicacion        VARCHAR(20),
    agrupacion_etnica     VARCHAR(50),
    grupo_etnico          VARCHAR(50),
    presenta_discapacidad VARCHAR(5),
    victima               VARCHAR(20),
    tipo_beneficiario     VARCHAR(50),
    beneficiarios         INTEGER,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_icbf_mpio ON ext.icbf_beneficiarios(cod_mpio);

CREATE TABLE ext.rlcpd_nacional (
    id                   SERIAL PRIMARY KEY,
    departamento_registro VARCHAR(50),
    municipio_registro   VARCHAR(80),
    cod_mpio_parsed      VARCHAR(5),
    fecha_registro       DATE,
    tipo_alteracion      VARCHAR(100),
    num_personas         INTEGER,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ext.familias_accion (
    id              SERIAL PRIMARY KEY,
    cod_dpto        VARCHAR(2),
    departamento    VARCHAR(100),
    cod_mpio        VARCHAR(5),
    municipio       VARCHAR(150),
    etnia           VARCHAR(50),
    discapacidad    VARCHAR(5),
    genero          VARCHAR(20),
    rango_edad      VARCHAR(30),
    tipo_poblacion  VARCHAR(50),
    beneficiarios   INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================================
-- SCHEMA: smt (Datos propios SMT-ONIC)
-- Con periodo para series de tiempo
-- ================================================================
CREATE SCHEMA IF NOT EXISTS smt;
COMMENT ON SCHEMA smt IS 'Datos del instrumento propio de caracterizacion SMT-ONIC.';

CREATE TABLE smt.caracterizacion (
    id                    SERIAL PRIMARY KEY,
    periodo               VARCHAR(10) NOT NULL DEFAULT '2026-F1',
    fase                  VARCHAR(20),
    macrorregion          VARCHAR(30) NOT NULL,
    organizacion          VARCHAR(100),
    pueblo                VARCHAR(100),
    resguardo_comunidad   VARCHAR(200),
    cod_mpio              VARCHAR(5),
    sexo                  VARCHAR(20),
    edad                  SMALLINT,
    tipo_discapacidad     VARCHAR(50),
    origen                VARCHAR(30),
    certificado           VARCHAR(20),
    cuidador              VARCHAR(20),
    barreras_territorio   TEXT,
    desarmonia_espiritual BOOLEAN,
    medicina_ancestral    BOOLEAN,
    lengua_propia         VARCHAR(50),
    participacion_comunitaria VARCHAR(50),
    raw_data              JSONB,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_smt_periodo ON smt.caracterizacion(periodo);
CREATE INDEX idx_smt_pueblo ON smt.caracterizacion(pueblo);

-- ================================================================
-- SCHEMA: imp (Datos IMPUTADOS / derivados)
-- ================================================================
CREATE SCHEMA IF NOT EXISTS imp;
COMMENT ON SCHEMA imp IS 'Datos imputados. Cada registro tiene metodo, confianza y fuente.';

CREATE TABLE imp.ruv_pueblo (
    id                  SERIAL PRIMARY KEY,
    -- Campos originales RUV
    cod_mpio            VARCHAR(5) NOT NULL,
    hecho               VARCHAR(200),
    sexo                VARCHAR(30),
    discapacidad        VARCHAR(50),
    ciclo_vital         VARCHAR(30),
    eventos             INTEGER,
    -- Imputacion
    cod_pueblo_imputado VARCHAR(3),
    pueblo_imputado     VARCHAR(100),
    pct_asignado        NUMERIC(5,1),
    metodo_imputacion   VARCHAR(50) NOT NULL,
    confianza           VARCHAR(10) NOT NULL,
    pct_dominante       NUMERIC(5,1),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_imp_ruv_pueblo ON imp.ruv_pueblo(cod_pueblo_imputado);
CREATE INDEX idx_imp_ruv_conf ON imp.ruv_pueblo(confianza);

CREATE TABLE imp.icbf_pueblo (
    id                  SERIAL PRIMARY KEY,
    cod_mpio            VARCHAR(5) NOT NULL,
    anio                SMALLINT,
    nombre_servicio     VARCHAR(200),
    rango_edad          VARCHAR(30),
    sexo                VARCHAR(20),
    presenta_discapacidad VARCHAR(5),
    beneficiarios       INTEGER,
    cod_pueblo_imputado VARCHAR(3),
    pueblo_imputado     VARCHAR(100),
    pct_asignado        NUMERIC(5,1),
    metodo_imputacion   VARCHAR(50) NOT NULL,
    confianza           VARCHAR(10) NOT NULL,
    pct_dominante       NUMERIC(5,1),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Log de imputaciones
CREATE TABLE imp.log_imputaciones (
    id                  SERIAL PRIMARY KEY,
    tabla_destino       VARCHAR(100) NOT NULL,
    fecha_ejecucion     TIMESTAMPTZ DEFAULT NOW(),
    registros_generados INTEGER,
    metodo_usado        VARCHAR(50),
    parametros          JSONB,
    notas               TEXT
);

-- ================================================================
-- SCHEMA: indicadores (Indicadores calculados automaticamente)
-- Con periodo para series de tiempo
-- ================================================================
CREATE SCHEMA IF NOT EXISTS indicadores;
COMMENT ON SCHEMA indicadores IS 'Indicadores calculados. Se recalculan al cargar nuevos datos.';

CREATE TABLE indicadores.definiciones (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(30) NOT NULL UNIQUE,
    nombre          VARCHAR(200) NOT NULL,
    grupo           VARCHAR(50) NOT NULL,
    formula         TEXT NOT NULL,
    meta            TEXT,
    fuente_primaria VARCHAR(50),
    fuente_cruce    VARCHAR(50),
    unidad          VARCHAR(30) DEFAULT '%',
    descripcion     TEXT
);

-- Valores calculados por periodo × territorio × pueblo
CREATE TABLE indicadores.valores (
    id              SERIAL PRIMARY KEY,
    cod_indicador   VARCHAR(30) NOT NULL REFERENCES indicadores.definiciones(codigo),
    periodo         VARCHAR(10) NOT NULL,
    nivel_geo       VARCHAR(20) NOT NULL,  -- nacional, dpto, mpio, pueblo
    cod_geo         VARCHAR(10),           -- cod_dpto, cod_mpio, cod_pueblo
    nombre_geo      VARCHAR(150),
    grupo_etnico    VARCHAR(50),
    pueblo          VARCHAR(100),
    valor           NUMERIC(12,4),
    numerador       BIGINT,
    denominador     BIGINT,
    confianza       VARCHAR(10),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (cod_indicador, periodo, nivel_geo, cod_geo, grupo_etnico, pueblo)
);
CREATE INDEX idx_ind_periodo ON indicadores.valores(periodo);
CREATE INDEX idx_ind_indicador ON indicadores.valores(cod_indicador);
CREATE INDEX idx_ind_pueblo ON indicadores.valores(pueblo);

-- ================================================================
-- FUNCION: Calcular todos los indicadores para un periodo
-- ================================================================
CREATE OR REPLACE FUNCTION indicadores.calcular_todos(p_periodo VARCHAR DEFAULT '2018')
RETURNS INTEGER AS $$
DECLARE
    n_generados INTEGER := 0;
    r RECORD;
BEGIN
    -- IND-01: Tasa de registro territorial
    -- (N personas SMT / N personas DANE con discapacidad indigena) x 100
    INSERT INTO indicadores.valores (cod_indicador, periodo, nivel_geo, cod_geo, nombre_geo, valor, numerador, denominador)
    SELECT 'IND-COB-01', p_periodo, 'nacional', '00', 'Colombia',
        CASE WHEN r2.pob_disc > 0 THEN ROUND(100.0 * COALESCE(r1.n_smt, 0) / r2.pob_disc, 4) ELSE 0 END,
        COALESCE(r1.n_smt, 0), r2.pob_disc
    FROM cnpv.resumen_nacional_etnico r2
    LEFT JOIN (SELECT COUNT(*) as n_smt FROM smt.caracterizacion WHERE periodo LIKE p_periodo || '%') r1 ON TRUE
    WHERE r2.grupo_etnico = 'Indigena' AND r2.periodo = p_periodo
    ON CONFLICT (cod_indicador, periodo, nivel_geo, cod_geo, grupo_etnico, pueblo) DO UPDATE
        SET valor = EXCLUDED.valor, numerador = EXCLUDED.numerador, denominador = EXCLUDED.denominador, created_at = NOW();

    -- IND-02: Prevalencia por tipo de discapacidad por pueblo
    INSERT INTO indicadores.valores (cod_indicador, periodo, nivel_geo, cod_geo, nombre_geo, pueblo, valor, numerador, denominador)
    SELECT 'IND-EPI-01', p_periodo, 'pueblo', cod_pueblo, pueblo, pueblo,
        tasa_x_1000, con_discapacidad, total
    FROM pueblo.disc_nacional WHERE periodo = p_periodo
    ON CONFLICT (cod_indicador, periodo, nivel_geo, cod_geo, grupo_etnico, pueblo) DO UPDATE
        SET valor = EXCLUDED.valor, numerador = EXCLUDED.numerador, denominador = EXCLUDED.denominador, created_at = NOW();

    -- IND-03: Indice de feminidad por pueblo
    INSERT INTO indicadores.valores (cod_indicador, periodo, nivel_geo, cod_geo, nombre_geo, pueblo, valor, numerador, denominador)
    SELECT 'IND-EPI-03', p_periodo, 'pueblo', cod_pueblo, pueblo, pueblo,
        CASE WHEN hombres > 0 THEN ROUND(100.0 * mujeres / hombres, 2) ELSE NULL END,
        mujeres, hombres
    FROM pueblo.sexo_nacional WHERE periodo = p_periodo
    ON CONFLICT (cod_indicador, periodo, nivel_geo, cod_geo, grupo_etnico, pueblo) DO UPDATE
        SET valor = EXCLUDED.valor, numerador = EXCLUDED.numerador, denominador = EXCLUDED.denominador, created_at = NOW();

    -- IND-04: % primera infancia (0-4) por pueblo
    INSERT INTO indicadores.valores (cod_indicador, periodo, nivel_geo, cod_geo, nombre_geo, pueblo, valor, numerador, denominador)
    SELECT 'IND-EPI-04', p_periodo, 'pueblo', e.cod_pueblo, e.pueblo, e.pueblo,
        CASE WHEN s.total > 0 THEN ROUND(100.0 * e.valor / s.total, 2) ELSE 0 END,
        e.valor, s.total
    FROM pueblo.edad_nacional e
    JOIN pueblo.sexo_nacional s ON e.cod_pueblo = s.cod_pueblo AND e.periodo = s.periodo
    WHERE e.grupo_edad = '00-04' AND e.periodo = p_periodo
    ON CONFLICT (cod_indicador, periodo, nivel_geo, cod_geo, grupo_etnico, pueblo) DO UPDATE
        SET valor = EXCLUDED.valor, numerador = EXCLUDED.numerador, denominador = EXCLUDED.denominador, created_at = NOW();

    -- IND-05: Prevalencia por departamento × pueblo
    INSERT INTO indicadores.valores (cod_indicador, periodo, nivel_geo, cod_geo, nombre_geo, pueblo, valor, numerador, denominador)
    SELECT 'IND-TERR-01', p_periodo, 'dpto', cod_dpto, '', pueblo,
        tasa_x_1000, con_discapacidad, total
    FROM pueblo.disc_dpto WHERE periodo = p_periodo AND total > 0
    ON CONFLICT (cod_indicador, periodo, nivel_geo, cod_geo, grupo_etnico, pueblo) DO UPDATE
        SET valor = EXCLUDED.valor, numerador = EXCLUDED.numerador, denominador = EXCLUDED.denominador, created_at = NOW();

    GET DIAGNOSTICS n_generados = ROW_COUNT;
    RETURN n_generados;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- Seed indicadores.definiciones
-- ================================================================
INSERT INTO indicadores.definiciones (codigo, nombre, grupo, formula, meta, fuente_primaria, fuente_cruce) VALUES
('IND-COB-01', 'Tasa de registro territorial', 'Cobertura', '(N_SMT / N_DANE_indigena_disc) x 100', 'Incremento anual sostenido', 'SMT-ONIC', 'CNPV 2018'),
('IND-COB-02', 'Cobertura por macrorregion', 'Cobertura', '(N_registros_region / N_esperado_region) x 100', '>60% en todas las macrorregiones', 'SMT-ONIC', NULL),
('IND-COB-03', 'Pueblos sin representacion', 'Cobertura', 'N_pueblos_DANE - N_pueblos_SMT', '0 pueblos sin registro', 'SMT-ONIC', 'CNPV 2018'),
('IND-EPI-01', 'Prevalencia por pueblo', 'Perfil Epidemiologico', '(N_disc / N_total) x 1000 por pueblo', 'Seguimiento anual', 'CNPV 2018', NULL),
('IND-EPI-02', 'Indice de discapacidad multiple', 'Perfil Epidemiologico', 'N_multiple / N_total', 'Complejidad de atencion', 'SMT-ONIC', NULL),
('IND-EPI-03', 'Indice de feminidad por pueblo', 'Perfil Epidemiologico', '(N_mujeres / N_hombres) x 100', 'Referente: 100 = paridad', 'CNPV 2018', NULL),
('IND-EPI-04', 'Primera infancia (0-4) por pueblo', 'Perfil Epidemiologico', '(N_0a4 / N_total) x 100', 'Rutas ICBF', 'CNPV 2018', NULL),
('IND-DER-01', 'Brecha de certificacion', 'Acceso a Derechos', '(N_sin_cert / N_con_respuesta) x 100', '<20% sin certificado al 2027', 'SMT-ONIC', 'RLCPD'),
('IND-DER-02', 'Disparidad regional certificacion', 'Acceso a Derechos', 'Max - Min certificacion por region', 'Reducir brecha', 'SMT-ONIC', NULL),
('IND-DER-03', 'Tasa cobertura de cuidado', 'Acceso a Derechos', '(N_con_cuidador / N_con_resp) x 100', 'Economia del cuidado', 'SMT-ONIC', NULL),
('IND-DER-04', 'Proporcion por conflicto armado', 'Acceso a Derechos', '(N_conflicto / N_total) x 100', 'Reparacion diferencial', 'SMT-ONIC', 'RUV'),
('IND-CAL-01', 'Completitud del registro', 'Calidad', '1 - (N_vacios / N_total) por campo', '>85% en cada campo critico', 'SMT-ONIC', NULL),
('IND-TERR-01', 'Prevalencia pueblo x territorio', 'Territorial', 'Tasa x 1000 por dpto por pueblo', 'Seguimiento territorial', 'CNPV 2018', NULL)
ON CONFLICT (codigo) DO NOTHING;

-- ================================================================
-- SCHEMA: victimas (Registro Unico de Victimas - microdatos)
-- ================================================================
CREATE SCHEMA IF NOT EXISTS victimas;
COMMENT ON SCHEMA victimas IS 'Microdatos RUV - Universo de victimas anonimizado.';

CREATE TABLE victimas.universo (
    id SERIAL PRIMARY KEY,
    idpersona VARCHAR(20),
    idhogar VARCHAR(20),
    pertenencia_etnica VARCHAR(60),
    genero VARCHAR(20),
    fecha_nacimiento DATE,
    hecho VARCHAR(200),
    fecha_ocurrencia DATE,
    cod_mpio_ocurrencia VARCHAR(5),
    cod_mpio_residencia VARCHAR(5),
    zona_ocurrencia VARCHAR(30),
    presunto_actor VARCHAR(100),
    tipo_victima VARCHAR(20),
    estado_victima VARCHAR(30),
    discapacidad VARCHAR(5),
    descripcion_discapacidad TEXT,
    tipo_discapacidad_limpia VARCHAR(30),
    cod_pueblo_imputado VARCHAR(3),
    pueblo_imputado VARCHAR(100),
    confianza_imputacion VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_vic_etnia ON victimas.universo(pertenencia_etnica);
CREATE INDEX idx_vic_disc ON victimas.universo(discapacidad);
CREATE INDEX idx_vic_mpio ON victimas.universo(cod_mpio_ocurrencia);
CREATE INDEX idx_vic_pueblo ON victimas.universo(pueblo_imputado);

-- Vista filtrada: solo indigenas con capacidades diversas
CREATE OR REPLACE VIEW victimas.indigenas_capacidades_diversas AS
SELECT *
FROM victimas.universo
WHERE pertenencia_etnica IN ('INDIGENA', 'INDIGENA ACREDITADO RA')
  AND discapacidad = '1';

-- Tabla pre-agregada: resumen por pueblo x hecho
CREATE TABLE victimas.resumen_pueblo_hecho (
    id SERIAL PRIMARY KEY,
    cod_pueblo_imputado VARCHAR(3),
    pueblo_imputado VARCHAR(100),
    hecho VARCHAR(200),
    tipo_disc_limpia VARCHAR(30),
    cod_dpto VARCHAR(2),
    cod_mpio VARCHAR(5),
    cantidad INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_rph_pueblo ON victimas.resumen_pueblo_hecho(cod_pueblo_imputado);
CREATE INDEX idx_rph_mpio ON victimas.resumen_pueblo_hecho(cod_mpio);

-- ================================================================
-- SCHEMA: smt_geo (Geometrias propias del SMT-ONIC)
-- Fuente: SpatiaLite my_smt_cmp_gdb_ambito_onic
-- ================================================================
CREATE SCHEMA IF NOT EXISTS smt_geo;
COMMENT ON SCHEMA smt_geo IS 'Capas geograficas propias del SMT-ONIC. Fuente: GDB ambito ONIC.';

-- 5 macrorregiones ONIC (polígonos)
CREATE TABLE smt_geo.macrorregiones (
    ogc_fid     INTEGER PRIMARY KEY,
    macro       VARCHAR(30) NOT NULL,
    geom        GEOMETRY(MultiPolygon, 4326)
);
CREATE INDEX idx_macro_geom ON smt_geo.macrorregiones USING GIST (geom);

-- 830 resguardos ambito ONIC (CON pueblo, org, DIVIPOLA, geometría)
CREATE TABLE smt_geo.resguardos (
    ogc_fid         INTEGER PRIMARY KEY,
    dpto_cnmbr      VARCHAR(100),
    mpio_cnmbr      VARCHAR(150),
    dpto_ccdgo      VARCHAR(2),
    mpio_cdpmp      VARCHAR(5),
    macro           VARCHAR(30),
    territorio      VARCHAR(200),
    pueblo_onic     VARCHAR(100),
    ccdgo_terr      VARCHAR(10),
    ccdgo_pblo      VARCHAR(10),
    org_nal         VARCHAR(50),
    org_regnal      VARCHAR(100),
    area_pg_ha      NUMERIC(12,3),
    id_resguar      VARCHAR(10),
    geom            GEOMETRY(MultiPolygon, 4326)
);
CREATE INDEX idx_resg_onic_geom ON smt_geo.resguardos USING GIST (geom);
CREATE INDEX idx_resg_onic_pueblo ON smt_geo.resguardos(pueblo_onic);
CREATE INDEX idx_resg_onic_mpio ON smt_geo.resguardos(mpio_cdpmp);
CREATE INDEX idx_resg_onic_macro ON smt_geo.resguardos(macro);

-- 13,868 comunidades (puntos con personas, viviendas, pueblo)
CREATE TABLE smt_geo.comunidades (
    ogc_fid         INTEGER PRIMARY KEY,
    dpto_cnmbr      VARCHAR(100),
    mpio_cnmbr      VARCHAR(150),
    comun_cnmbr     VARCHAR(200),
    dpto_ccdgo      VARCHAR(2),
    mpio_cdpmp      VARCHAR(5),
    comun_ccdgo     VARCHAR(30),
    macro           VARCHAR(30),
    territorio      VARCHAR(200),
    pueblo_onic     VARCHAR(100),
    ccdgo_terr      VARCHAR(10),
    ccdgo_pblo      VARCHAR(10),
    org_nal         VARCHAR(50),
    org_regnal      VARCHAR(100),
    viviendas       INTEGER,
    familias        INTEGER,
    personas        INTEGER,
    msnm            INTEGER,
    geom            GEOMETRY(Point, 4326)
);
CREATE INDEX idx_comun_geom ON smt_geo.comunidades USING GIST (geom);
CREATE INDEX idx_comun_pueblo ON smt_geo.comunidades(pueblo_onic);
CREATE INDEX idx_comun_mpio ON smt_geo.comunidades(mpio_cdpmp);

-- 1,935 clusters de viviendas (polígonos con densidad)
CREATE TABLE smt_geo.cluster_viviendas (
    ogc_fid         INTEGER PRIMARY KEY,
    dpto_cnmbr      VARCHAR(100),
    mpio_cnmbr      VARCHAR(150),
    dpto_ccdgo      VARCHAR(2),
    mpio_cdpmp      VARCHAR(5),
    macro           VARCHAR(30),
    territorio      VARCHAR(200),
    pueblo_onic     VARCHAR(100),
    ccdgo_terr      VARCHAR(10),
    ccdgo_pblo      VARCHAR(10),
    org_nal         VARCHAR(50),
    org_regnal      VARCHAR(100),
    viviendas       NUMERIC(10,1),
    area_ha         NUMERIC(12,3),
    densidad_viv    NUMERIC(10,2),
    geom            GEOMETRY(MultiPolygon, 4326)
);
CREATE INDEX idx_cluster_geom ON smt_geo.cluster_viviendas USING GIST (geom);

-- 230 expectativas ancestrales (territorios en proceso de titulación)
CREATE TABLE smt_geo.expectativas_ancestrales (
    ogc_fid         INTEGER PRIMARY KEY,
    dpto_cnmbr      VARCHAR(100),
    mpio_cnmbr      VARCHAR(150),
    dpto_ccdgo      VARCHAR(2),
    mpio_cdpmp      VARCHAR(5),
    macro           VARCHAR(30),
    proceso         VARCHAR(50),
    area_ha         NUMERIC(12,1),
    viviendas       NUMERIC(10,1),
    comunidades     NUMERIC(10,1),
    geom            GEOMETRY(MultiPolygon, 4326)
);
CREATE INDEX idx_expect_geom ON smt_geo.expectativas_ancestrales USING GIST (geom);
