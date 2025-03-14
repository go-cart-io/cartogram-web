import { formatValue } from 'vega-tooltip'

const LOCALE =
  navigator.languages && navigator.languages.length ? navigator.languages[0] : navigator.language

export const RESERVE_FIELDS = [
  'Region',
  'RegionLabel',
  'Color',
  'ColorGroup',
  'Inset',
  'Geographic Area'
]
export const NUM_RESERVED_FILEDS = RESERVE_FIELDS.length
export const COL_COLOR = 2
export const COL_INSET = 4
export const COL_AREA = 5
export const OPTIONS_INSET = [
  { text: 'C (center)', value: 'C' },
  { text: 'L (left)', value: 'L' },
  { text: 'R (right)', value: 'R' },
  { text: 'T (top)', value: 'T' },
  { text: 'D (down)', value: 'D' }
]

export const tooltipOptions = {
  theme: 'dark',
  formatTooltip: (value: any, sanitize: any) => {
    // Create a shallow copy of the value object with formatted numbers.
    const newValues: any = {}
    let region

    for (const [key, val] of Object.entries(value)) {
      // Skip the 'ColorGroup' key.
      if (key === 'ColorGroup') {
        continue
      }
      if (key === 'Region') {
        region = val
        continue
      }
      if (key === 'RegionLabel') {
        newValues[val] = region
        continue
      }
      if (key.startsWith('Geographic Area')) {
        newValues['Area'] =
          new Intl.NumberFormat(LOCALE, {
            notation: 'compact',
            compactDisplay: 'short',
            maximumFractionDigits: 3
          }).format(val) + ' km²'
        continue
      }
      // Check if value is null or undefined.
      if (val == null) {
        continue
      }
      const num = Number(val)
      if (!isNaN(num)) {
        let unit = ''
        const baseKey = key
          .replace(/\s*\(([^)]+)\)/, (_, p1) => {
            unit = ' ' + p1
            return ''
          })
          .trim()
        newValues[baseKey] =
          new Intl.NumberFormat(LOCALE, {
            notation: 'compact',
            compactDisplay: 'short',
            maximumFractionDigits: 3
          }).format(num) + unit
      } else {
        newValues[key] = val
      }
    }

    // Delegate to the default formatter to keep their HTML structure.
    return formatValue(newValues, sanitize, 0)
  }
}
