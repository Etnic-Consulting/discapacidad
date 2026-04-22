-- ================================================================
-- Migration 002: Auth + Formulario
-- SMT-ONIC — soporte para autenticación de dinamizadores
-- y persistencia de respuestas del formulario de recolección
-- ================================================================

CREATE SCHEMA IF NOT EXISTS smt;

-- ----------------------------------------------------------------
-- TABLA: smt.usuarios
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS smt.usuarios (
    id                  SERIAL PRIMARY KEY,
    username            VARCHAR(80) UNIQUE NOT NULL,
    password_hash       VARCHAR(128) NOT NULL,
    salt                VARCHAR(32) NOT NULL,
    nombre              VARCHAR(200) NOT NULL,
    email               VARCHAR(200),
    rol                 VARCHAR(40) NOT NULL DEFAULT 'dinamizador'
                        CHECK (rol IN ('admin', 'dinamizador', 'monitor', 'coordinador')),
    pueblo_asignado     VARCHAR(10),
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login          TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_usuarios_username ON smt.usuarios (username);
CREATE INDEX IF NOT EXISTS ix_usuarios_rol ON smt.usuarios (rol);

-- ----------------------------------------------------------------
-- TABLA: smt.sesion_tokens
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS smt.sesion_tokens (
    id           SERIAL PRIMARY KEY,
    token        VARCHAR(64) UNIQUE NOT NULL,
    usuario_id   INTEGER NOT NULL REFERENCES smt.usuarios(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked      BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_sesion_tokens_token ON smt.sesion_tokens (token);
CREATE INDEX IF NOT EXISTS ix_sesion_tokens_usuario ON smt.sesion_tokens (usuario_id);

-- ----------------------------------------------------------------
-- TABLA: smt.respuestas_formulario
-- Guarda todo el payload del formulario como JSONB para flexibilidad
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS smt.respuestas_formulario (
    id                    SERIAL PRIMARY KEY,
    usuario_id            INTEGER NOT NULL REFERENCES smt.usuarios(id) ON DELETE RESTRICT,
    cod_pueblo            VARCHAR(10),
    cod_dpto              VARCHAR(5),
    cod_mpio              VARCHAR(10),
    nombre_comunidad      VARCHAR(200),
    documento_persona     VARCHAR(40),
    fecha_envio           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    datos                 JSONB NOT NULL,
    cpli_consentimiento   VARCHAR(10) NOT NULL DEFAULT 'no'
                          CHECK (cpli_consentimiento IN ('si', 'no')),
    notas                 TEXT
);

CREATE INDEX IF NOT EXISTS ix_respuestas_usuario ON smt.respuestas_formulario (usuario_id);
CREATE INDEX IF NOT EXISTS ix_respuestas_pueblo ON smt.respuestas_formulario (cod_pueblo);
CREATE INDEX IF NOT EXISTS ix_respuestas_mpio ON smt.respuestas_formulario (cod_mpio);
CREATE INDEX IF NOT EXISTS ix_respuestas_fecha ON smt.respuestas_formulario (fecha_envio);
CREATE INDEX IF NOT EXISTS ix_respuestas_datos ON smt.respuestas_formulario USING GIN (datos);
