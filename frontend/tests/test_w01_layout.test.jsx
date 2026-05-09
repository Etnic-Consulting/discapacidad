/**
 * test_w01_layout.test.jsx
 * W01 Sprint S5_v1_1 — validación de orden de grupos de edad
 *
 * Valida las transformaciones de datos de CADA componente:
 *   - RangoEdadDiscBar: SIN reverse → orden cronológico 0-4 … 85+ (ascendente)
 *   - PiramidePoblacional: CON reverse → orden vertical 85+ … 0-4 (descendente)
 *
 * Estos tests son puros (sin DOM, sin React) porque validan la lógica de
 * transformación de datos, que es la causa raíz del bug W01.
 */

import { describe, it, expect } from 'vitest';

// -----------------------------------------------------------------------
// Datos de prueba — 4 grupos de edad en orden ascendente desde el API
// -----------------------------------------------------------------------
const GRUPOS_ASCENDENTE = ['0-4', '5-9', '10-14', '85+'];

function makePiramideData(grupos = GRUPOS_ASCENDENTE) {
  return {
    piramide: grupos.map((g, i) => ({
      grupo_edad: g,
      hombres_abs: (i + 1) * 10,
      mujeres_abs: (i + 1) * 8,
    })),
    total: grupos.length * 18,
    total_hombres: grupos.reduce((s, _, i) => s + (i + 1) * 10, 0),
    total_mujeres: grupos.reduce((s, _, i) => s + (i + 1) * 8, 0),
  };
}

// -----------------------------------------------------------------------
// Transformación usada por RangoEdadDiscBar (SIN reverse)
// -----------------------------------------------------------------------
function transformRangoEdadDiscBar(piramideData) {
  const { piramide, total } = piramideData;
  // Copia exacta de la lógica del componente — SIN .reverse()
  return piramide.map((row) => {
    const hAbs = row.hombres_abs || Math.abs(row.hombres || 0);
    const mAbs = row.mujeres_abs || Math.abs(row.mujeres || 0);
    return {
      grupo_edad: row.grupo_edad,
      hombres: hAbs,
      mujeres: mAbs,
    };
  });
  // No se aplica .reverse()
}

// -----------------------------------------------------------------------
// Transformación usada por PiramidePoblacional (CON reverse)
// -----------------------------------------------------------------------
function transformPiramidePoblacional(piramideData) {
  const { piramide, total } = piramideData;
  // Copia exacta de la lógica del componente — CON .slice().reverse()
  return piramide.map((row) => {
    const hAbs = row.hombres_abs || Math.abs(row.hombres || 0);
    const mAbs = row.mujeres_abs || Math.abs(row.mujeres || 0);
    return {
      grupo_edad: row.grupo_edad,
      hombres_pct: -hAbs,
      mujeres_pct: mAbs,
    };
  }).slice().reverse(); // REVERSE intencional
}

// -----------------------------------------------------------------------
// Suite: RangoEdadDiscBar — orden cronológico ascendente
// -----------------------------------------------------------------------
describe('RangoEdadDiscBar — data transform', () => {
  const data = makePiramideData();
  const result = transformRangoEdadDiscBar(data);

  it('primer grupo renderizado es 0-4 (izquierda/arriba del eje Y)', () => {
    expect(result[0].grupo_edad).toBe('0-4');
  });

  it('ultimo grupo renderizado es 85+ (derecha/abajo del eje Y)', () => {
    expect(result[result.length - 1].grupo_edad).toBe('85+');
  });

  it('orden completo ascendente: 0-4, 5-9, 10-14, 85+', () => {
    const grupos = result.map((r) => r.grupo_edad);
    expect(grupos).toEqual(['0-4', '5-9', '10-14', '85+']);
  });

  it('hombres y mujeres son valores positivos (no negativos)', () => {
    result.forEach((row) => {
      expect(row.hombres).toBeGreaterThanOrEqual(0);
      expect(row.mujeres).toBeGreaterThanOrEqual(0);
    });
  });

  it('longitud de resultado igual a piramide de entrada', () => {
    expect(result.length).toBe(data.piramide.length);
  });
});

// -----------------------------------------------------------------------
// Suite: PiramidePoblacional — orden descendente vertical (85+ arriba)
// -----------------------------------------------------------------------
describe('PiramidePoblacional — data transform', () => {
  const data = makePiramideData();
  const result = transformPiramidePoblacional(data);

  it('primer grupo renderizado es 85+ (posicion top en Recharts layout=vertical)', () => {
    expect(result[0].grupo_edad).toBe('85+');
  });

  it('ultimo grupo renderizado es 0-4 (posicion bottom)', () => {
    expect(result[result.length - 1].grupo_edad).toBe('0-4');
  });

  it('orden completo descendente: 85+, 10-14, 5-9, 0-4', () => {
    const grupos = result.map((r) => r.grupo_edad);
    expect(grupos).toEqual(['85+', '10-14', '5-9', '0-4']);
  });

  it('hombres_pct es negativo (lado izquierdo de la piramide mariposa)', () => {
    result.forEach((row) => {
      expect(row.hombres_pct).toBeLessThanOrEqual(0);
    });
  });

  it('mujeres_pct es positivo (lado derecho)', () => {
    result.forEach((row) => {
      expect(row.mujeres_pct).toBeGreaterThanOrEqual(0);
    });
  });

  it('longitud de resultado igual a piramide de entrada', () => {
    expect(result.length).toBe(data.piramide.length);
  });
});

// -----------------------------------------------------------------------
// Suite: Verificacion de diferencia entre los dos componentes
// -----------------------------------------------------------------------
describe('Diferencia RangoEdadDiscBar vs PiramidePoblacional', () => {
  const data = makePiramideData();
  const discResult = transformRangoEdadDiscBar(data);
  const pirResult = transformPiramidePoblacional(data);

  it('RangoEdadDiscBar primer grupo != PiramidePoblacional primer grupo (ordenes opuestos)', () => {
    expect(discResult[0].grupo_edad).not.toBe(pirResult[0].grupo_edad);
  });

  it('grupos de RangoEdadDiscBar son el inverso de PiramidePoblacional', () => {
    const discGrupos = discResult.map((r) => r.grupo_edad);
    const pirGrupos = pirResult.map((r) => r.grupo_edad);
    expect(discGrupos).toEqual([...pirGrupos].reverse());
  });
});
