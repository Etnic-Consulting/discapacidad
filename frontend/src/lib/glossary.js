export const GLOSSARY = {
  CNPV: 'Censo Nacional de Poblacion y Vivienda 2018 (DANE).',
  CG: 'Censo General 2005 (DANE).',
  RUV: 'Registro Unico de Victimas (Unidad para las Victimas).',
  RLCPD: 'Registro para la Localizacion y Caracterizacion de Personas con Discapacidad (MinSalud).',
  SISPRO: 'Sistema Integrado de Informacion de la Proteccion Social (MinSalud).',
  ONIC: 'Organizacion Nacional Indigena de Colombia.',
  SMT: 'Sistema de Monitoreo Territorial - ONIC.',
  WG: 'Grupo de Washington para Estadisticas de Discapacidad (ONU).',
  'WG-SS': 'Grupo de Washington - set corto de 6 preguntas funcionales.',
  CDPD: 'Convencion sobre los Derechos de las Personas con Discapacidad (ONU 2006).',
  DANE: 'Departamento Administrativo Nacional de Estadistica.',
  IBV: 'Indice de Bienestar Vivencial.',
  'por mil': 'Numero de casos por cada 1.000 personas (tasa).',
  prevalencia: 'Proporcion de la poblacion que presenta la condicion en un momento dado.',
  intercensal: 'Comparacion de variables entre dos censos consecutivos (CG 2005 vs CNPV 2018).',
};

export function lookup(term) {
  if (!term) return null;
  return GLOSSARY[term] || GLOSSARY[term.toUpperCase()] || GLOSSARY[term.toLowerCase()] || null;
}
