/* ============================================
   <DisabilityGlossary /> · Glosario interactivo
   ============================================
   Componente pedagógico que abre un drawer/modal
   con definiciones de términos clave de
   discapacidad indígena en SMT-ONIC.

   Generado: 2026-05-03 · Sprint S1.E "visual pedagógico"
   Doctrina: _docs/DOCTRINA_DISENO_VISUAL_v1.md §6.1
   ============================================ */

import { useState } from 'react';

const TERMS = [
  {
    code: 'cd',
    title: 'Capacidades Diversas (CD)',
    short: 'Término que la ONIC usa en lugar de "discapacidad".',
    full: 'El movimiento indígena colombiano usa "capacidades diversas" en lugar de "discapacidad" para enfatizar que cada persona tiene capacidades distintas, no una falta. La cifra oficial sigue siendo "discapacidad" porque así se nombra en el CNPV 2018, pero el SMT-ONIC adopta CD como término preferido en comunicación.',
    citation: 'Doctrina ONIC · Decreto 1953/2014 (autonomía SISPI)',
  },
  {
    code: 'wg',
    title: 'Washington Group (WG)',
    short: 'Conjunto de 6 preguntas que mide dificultad funcional, no diagnóstico.',
    full: 'Las 6 preguntas WG son el estándar internacional para medir discapacidad en censos. Preguntan sobre dificultad para: ver, oír, caminar, recordar, autocuidado, comunicarse. Cada una tiene 4 niveles (1=no puede, 2=mucha dificultad, 3=alguna dificultad, 4=sin dificultad). Adoptado por DANE en CNPV 2018.',
    citation: 'Washington Group on Disability Statistics · CDPD ONU Art. 31',
  },
  {
    code: 'severidad',
    title: 'Severidad de la dificultad',
    short: 'Las personas con CD no son un grupo uniforme: hay 4 niveles de severidad por tipo.',
    full: 'En CNPV 2018 cada dificultad tiene 4 niveles: nivel 1 ("no puede hacerlo") es el más severo, nivel 4 ("sin dificultad") es la línea base. Los dashboards que reportan "X% con discapacidad" colapsan estos 4 niveles en uno binario, perdiendo información política importante: las intervenciones para nivel 1 son distintas a las de nivel 3.',
    citation: 'Panel EPX línea 567 (recomendación crítica)',
  },
  {
    code: 'prevalencia-cruda',
    title: 'Prevalencia cruda',
    short: 'Número de personas con la condición ÷ población total × 100.',
    full: 'Es la cifra "directa" del censo. Indígenas: 6.0% (60.0 ‰). El problema: no tiene en cuenta la estructura etaria. Si un grupo es más joven, naturalmente tendrá menor prevalencia. Para comparar grupos de forma justa se necesita la prevalencia estandarizada.',
    citation: 'Demografía clásica',
  },
  {
    code: 'prevalencia-estandarizada',
    title: 'Prevalencia estandarizada por edad',
    short: 'Pregunta: ¿cuánta CD habría si el grupo tuviera la estructura etaria estándar?',
    full: 'Aplica la prevalencia por edad del grupo a una población de referencia (Colombia 2018). El resultado permite comparar grupos justamente. Para indígenas, la prevalencia estandarizada es MAYOR que la cruda · porque el grupo es joven · sugiere subregistro o efecto-juventud.',
    citation: 'T_BD02_prevalencia_estandarizada · Sprint S1+',
  },
  {
    code: 'paradoja-epidemiologica',
    title: 'Paradoja epidemiológica indígena',
    short: '¿Por qué indígenas tienen MENOS prevalencia que la población general?',
    full: 'Cifras crudas: indígenas 60.0‰ vs general 71.5‰. La explicación NO es "los indígenas son más sanos". Tres factores: (1) población indígena más joven (menos disc geriátrica), (2) subregistro (barreras lingüísticas/culturales en censo), (3) concepción cultural distinta de "dificultad". La estandarización por edad descarta (1). Para distinguir (2) y (3) se necesita análisis bayesiano.',
    citation: 'CONTEXTO_Y_ROADMAP §8 · panel EPX línea 388',
  },
  {
    code: 'fac',
    title: 'FAC · Factor de Ajuste de Comparabilidad',
    short: 'Cifra que armoniza CG2005 con CNPV2018 (cambio de instrumento).',
    full: 'CG2005 medía "limitaciones permanentes". CNPV2018 mide Washington Group. Las series temporales NO son directamente comparables sin un factor de ajuste. El FAC se calcula por grupo étnico. Indígena FAC = 0.94 (cifras cercanas). Implementado en T11 · poblado en proyecciones.fac · usado por endpoint /intercensal?aplicar_fac=true.',
    citation: 'METODO_FAC_v1.md · Sprint S1.B11',
  },
  {
    code: 'icv',
    title: 'ICV · Índice de Vulnerabilidad Compuesta',
    short: 'Índice 0-100 por municipio: combina prevalencia + NBI + IPM + víctimas.',
    full: 'Pesos: prevalencia 30% + NBI 30% + IPM 20% + víctimas 20%. 100 = más vulnerable. Permite ranking territorial para focalización política. Implementado en T_BD01 · indicadores.icv_municipal.',
    citation: 'ROADMAP_DEMOGRAFICO_V3 §2.1',
  },
  {
    code: 'rlcpd',
    title: 'RLCPD · Registro Localización y Caracterización Personas Discapacidad',
    short: 'Registro oficial de MinSalud · cifra menor a la del CNPV por barreras de acceso.',
    full: 'Registro administrativo voluntario. Solo una minoría de los indígenas con capacidades diversas del CNPV están en RLCPD. La diferencia es la "deuda institucional": el Estado oficialmente no las "ve". Esta brecha es prioridad de política pública. Las cifras exactas vivas se calculan en el endpoint /api/v1/dashboard/brecha.',
    citation: 'Resolución 1239/2022 MinSalud',
  },
  {
    code: 'sispro',
    title: 'SISPRO · Sistema de Información de Protección Social',
    short: 'Plataforma MinSalud · contiene RIPS · BDUA · RLCPD · mortalidad · natalidad.',
    full: 'Acceso restringido. SMT-ONIC envió carta solicitando integración. Cuando se conecte, datos de salud llegarán en tiempo real (no solo censo cada 8 años). RIPS = atención efectiva. BDUA = afiliación. Ver CARTA_SOLICITUD_SISPRO.md.',
    citation: 'Decreto 968/2024 · MinSalud',
  },
  {
    code: 'sispi',
    title: 'SISPI · Sistema Indígena de Salud Propio Intercultural',
    short: 'Sistema oficial de salud propia · Decreto 1953/2014.',
    full: 'Reconoce la medicina propia (jaibanás · mamos · taitas · curanderos) como parte del sistema de salud nacional. Para personas con CD indígenas, las "ayudas ancestrales" son tan válidas como las técnicas occidentales. SMT-ONIC integra ambas dimensiones.',
    citation: 'Decreto 1953/2014 · CDPD ONU Art. 25',
  },
  {
    code: 'cdpd',
    title: 'CDPD · Convención sobre los Derechos de las Personas con Discapacidad',
    short: 'Tratado ONU · Colombia firmó 2007 · marco rector.',
    full: 'Establece derechos de personas con CD: salud (Art. 25) · familia (Art. 23) · accesibilidad (Art. 9) · información (Art. 21) · datos (Art. 31). SMT-ONIC opera bajo este marco. Cada indicador del dashboard se cruza con un artículo CDPD.',
    citation: 'ONU 2006 · Ley 1346/2009 Colombia',
  },
  {
    code: 'convenio-169',
    title: 'Convenio 169 OIT',
    short: 'Tratado de pueblos indígenas · Colombia firmó · marco superior.',
    full: 'Reconoce autonomía territorial · cultural · jurídica de pueblos indígenas. Art. 7 (desarrollo propio) · Art. 14 (tierras) · Art. 25 (salud intercultural). Combinado con CDPD · da el marco doble (étnico + disc) que define SMT-ONIC.',
    citation: 'OIT 1989 · Ley 21/1991 Colombia',
  },
  {
    code: 'd1',
    title: 'D1 · Decisión 1 · 115 pueblos canónicos',
    short: 'SMT-ONIC adopta 115 pueblos (DANE CNPV 2018) como cifra oficial.',
    full: 'Hay 3 cifras circulando: 115 (DANE CNPV 2018), 121 (ONIC oficial), 248 (Visor DANE cruzado). SMT-ONIC adopta 115 porque es la única con cobertura censal completa. Los 6 pueblos ONIC adicionales se visibilizan como "en proceso de caracterización" pero no se cuantifican con datos censales.',
    citation: 'DECISION_PUEBLOS_CANONICOS.md · Sprint S0',
  },
];

const containerStyle = {
  position: 'fixed',
  top: 0,
  right: 0,
  width: 'min(420px, 90vw)',
  height: '100vh',
  background: 'var(--color-gray-100, #F5F5F5)',
  boxShadow: '-8px 0 24px rgba(0,0,0,0.18)',
  zIndex: 1000,
  display: 'flex',
  flexDirection: 'column',
  borderLeft: '4px solid var(--color-green-mid, #02AB44)',
};

const headerStyle = {
  padding: '16px 20px',
  borderBottom: '1px solid #DDD',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  background: 'var(--color-primary, #02432D)',
  color: 'white',
};

const titleStyle = {
  margin: 0,
  fontSize: '1.125rem',
  fontWeight: 600,
};

const closeButtonStyle = {
  background: 'transparent',
  border: 'none',
  color: 'white',
  fontSize: '1.5rem',
  cursor: 'pointer',
  lineHeight: 1,
  padding: '0 8px',
};

const listStyle = {
  flex: 1,
  overflowY: 'auto',
  padding: '8px 0',
};

const itemStyle = (expanded) => ({
  padding: '12px 20px',
  borderBottom: '1px solid #E0E0E0',
  background: expanded ? 'white' : 'transparent',
  cursor: 'pointer',
  transition: 'background 0.15s',
});

const itemTitleStyle = {
  fontSize: '0.95rem',
  fontWeight: 600,
  color: 'var(--color-primary, #02432D)',
  margin: 0,
  marginBottom: '4px',
};

const itemShortStyle = {
  fontSize: '0.8125rem',
  color: 'var(--color-gray-500, #6B6B6B)',
  margin: 0,
  fontStyle: 'italic',
};

const itemFullStyle = {
  fontSize: '0.875rem',
  marginTop: '8px',
  lineHeight: 1.55,
  color: '#333',
};

const itemCitationStyle = {
  fontSize: '0.75rem',
  color: 'var(--color-gray-500, #6B6B6B)',
  marginTop: '8px',
  paddingTop: '8px',
  borderTop: '1px dashed #DDD',
};

const triggerStyle = {
  position: 'fixed',
  bottom: 24,
  right: 24,
  width: 48,
  height: 48,
  borderRadius: '50%',
  background: 'var(--color-green-mid, #02AB44)',
  color: 'white',
  border: 'none',
  cursor: 'pointer',
  fontSize: '1.25rem',
  fontWeight: 600,
  boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  zIndex: 999,
};

export default function DisabilityGlossary() {
  const [open, setOpen] = useState(false);
  const [expandedCode, setExpandedCode] = useState(null);

  return (
    <>
      <button
        type="button"
        style={triggerStyle}
        onClick={() => setOpen(true)}
        aria-label="Abrir glosario de términos de discapacidad"
        title="Glosario · términos clave"
      >
        ℹ
      </button>

      {open && (
        <div style={containerStyle} role="dialog" aria-label="Glosario de términos">
          <div style={headerStyle}>
            <h2 style={titleStyle}>Glosario · términos clave</h2>
            <button
              type="button"
              style={closeButtonStyle}
              onClick={() => setOpen(false)}
              aria-label="Cerrar glosario"
            >
              ×
            </button>
          </div>
          <div style={listStyle}>
            {TERMS.map((t) => {
              const expanded = expandedCode === t.code;
              return (
                <div
                  key={t.code}
                  style={itemStyle(expanded)}
                  onClick={() => setExpandedCode(expanded ? null : t.code)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setExpandedCode(expanded ? null : t.code);
                    }
                  }}
                >
                  <h3 style={itemTitleStyle}>{t.title}</h3>
                  <p style={itemShortStyle}>{t.short}</p>
                  {expanded && (
                    <>
                      <p style={itemFullStyle}>{t.full}</p>
                      <p style={itemCitationStyle}>📖 {t.citation}</p>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
