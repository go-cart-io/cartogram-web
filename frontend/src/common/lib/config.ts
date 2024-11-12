export const RESERVE_FIELDS_CSV = ['Region', 'Abbreviation', 'Color', 'Inset']
export const RESERVE_FIELDS = [...RESERVE_FIELDS_CSV, 'cartogram_id', 'ColorGroup', 'label']
export const RESERVE_FIELDS_W_INIT_NAMES = [
  ...RESERVE_FIELDS,
  'Land Area (sq.km.)',
  'Population (people)'
]
