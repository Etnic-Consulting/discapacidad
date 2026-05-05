--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg110+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg110+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: macro_dptos; Type: TABLE; Schema: geo; Owner: -
--

CREATE TABLE geo.macro_dptos (
    cod_dpto character varying(2) NOT NULL,
    nom_dpto text NOT NULL,
    macro character varying(30),
    es_asamblea boolean DEFAULT false,
    fuente text DEFAULT 'Departamentos.gpkg ONIC 2024'::text
);


--
-- Name: macro_dptos macro_dptos_pkey; Type: CONSTRAINT; Schema: geo; Owner: -
--

ALTER TABLE ONLY geo.macro_dptos
    ADD CONSTRAINT macro_dptos_pkey PRIMARY KEY (cod_dpto);


--
-- Name: idx_macro_dptos_macro; Type: INDEX; Schema: geo; Owner: -
--

CREATE INDEX idx_macro_dptos_macro ON geo.macro_dptos USING btree (macro);


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg110+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg110+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: macro_dptos; Type: TABLE DATA; Schema: geo; Owner: -
--

INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('05', 'ANTIOQUIA', 'OCCIDENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('08', 'ATLÁNTICO', 'NORTE', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('11', 'BOGOTÁ, D.C.', 'CENTRO - ORIENTE', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('13', 'BOLÍVAR', 'NORTE', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('15', 'BOYACÁ', 'CENTRO - ORIENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('17', 'CALDAS', 'OCCIDENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('18', 'CAQUETÁ', 'AMAZONIA', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('19', 'CAUCA', 'OCCIDENTE', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('20', 'CESAR', 'NORTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('23', 'CÓRDOBA', 'NORTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('25', 'CUNDINAMARCA', 'CENTRO - ORIENTE', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('27', 'CHOCÓ', 'OCCIDENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('41', 'HUILA', 'OCCIDENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('44', 'LA GUAJIRA', 'NORTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('47', 'MAGDALENA', 'NORTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('50', 'META', 'ORINOQUIA', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('52', 'NARIÑO', 'OCCIDENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('54', 'NORTE DE SANTANDER', 'CENTRO - ORIENTE', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('63', 'QUINDIO', 'OCCIDENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('66', 'RISARALDA', 'OCCIDENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('68', 'SANTANDER', 'CENTRO - ORIENTE', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('70', 'SUCRE', 'NORTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('73', 'TOLIMA', 'CENTRO - ORIENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('76', 'VALLE DEL CAUCA', 'OCCIDENTE', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('81', 'ARAUCA', 'ORINOQUIA', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('85', 'CASANARE', 'ORINOQUIA', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('86', 'PUTUMAYO', 'AMAZONIA', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('88', 'ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA', NULL, false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('91', 'AMAZONAS', 'AMAZONIA', true, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('94', 'GUAINÍA', 'AMAZONIA', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('95', 'GUAVIARE', 'AMAZONIA', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('97', 'VAUPÉS', 'AMAZONIA', false, 'Departamentos.gpkg ONIC 2024');
INSERT INTO geo.macro_dptos (cod_dpto, nom_dpto, macro, es_asamblea, fuente) VALUES ('99', 'VICHADA', 'ORINOQUIA', true, 'Departamentos.gpkg ONIC 2024');


--
-- PostgreSQL database dump complete
--

