export const fmt2 = (n) =>
  n == null || isNaN(n) ? '--' : new Intl.NumberFormat('es-CO').format(Math.round(n));

export const fmtDec = (n, d = 1) =>
  n == null || isNaN(n) ? '--' : Number(n).toFixed(d);

export const fmtK = (n) => {
  if (n == null || isNaN(n)) return '--';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(n >= 10_000 ? 0 : 1) + 'K';
  return String(Math.round(n));
};
