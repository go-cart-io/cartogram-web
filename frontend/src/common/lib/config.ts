export const LOCALE =
  navigator.languages && navigator.languages.length ? navigator.languages[0] : navigator.language
export const NUM_GRID_OPTIONS = 3

export const RESERVE_FIELDS = [
  'Region',
  'RegionMap',
  'RegionLabel',
  'Color',
  'ColorGroup',
  'Inset',
  'Geographic Area'
]
export const NUM_RESERVED_FILEDS = RESERVE_FIELDS.length
export const COL_REGIONMAP = 1
export const COL_COLOR = 3
export const COL_INSET = 5
export const COL_AREA = 6
export const OPTIONS_INSET = [
  { text: '', value: '' },
  { text: 'L (left)', value: 'L' },
  { text: 'R (right)', value: 'R' },
  { text: 'T (top)', value: 'T' },
  { text: 'B (bottom)', value: 'B' }
]
