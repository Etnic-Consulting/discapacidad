/* ============================================
   SMT-ONIC v2.0 — Age Group Utilities
   Sort and merge age groups for pyramid charts.
   Merges 85-89, 90-94, 95-99, 100+ into "85+".
   ============================================ */

/**
 * Sort and merge age groups for age pyramid charts.
 * Groups with start age >= 85 are merged into a single "85+" category.
 *
 * @param {Array} data - Array of objects with age group labels and values
 * @param {string} labelKey - Key for the age group label (default: 'grupo_edad')
 * @param {string} valueKey - Key for the value (default: 'valor')
 * @returns {Array} Sorted and merged array
 */
export function sortAndMergeAgeGroups(data, labelKey = 'grupo_edad', valueKey = 'valor') {
  if (!data || data.length === 0) return [];

  const merged = {};
  for (const row of data) {
    const label = row[labelKey];
    // Extract the first number from the group label: "00-04" -> 0, "10-14" -> 10, "85+" -> 85
    const digits = (label || '').replace(/[^0-9]/g, '');
    const startAge = parseInt(digits.substring(0, 2)) || 0;
    const key = startAge >= 85 ? '85+' : label;
    if (!merged[key]) {
      merged[key] = { [labelKey]: key, [valueKey]: 0, _sortOrder: startAge >= 85 ? 85 : startAge };
    }
    merged[key][valueKey] += (row[valueKey] || 0);
  }

  return Object.values(merged)
    .sort((a, b) => a._sortOrder - b._sortOrder)
    .map(({ _sortOrder, ...rest }) => rest);
}
