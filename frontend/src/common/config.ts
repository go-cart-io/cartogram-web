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
  formatTooltip: (values: any, sanitize: any) => {
    if (typeof values !== 'object') return formatValue(values, sanitize, 0)

    // Create a shallow copy of the value object with formatted numbers.
    const newValues: { [key: string]: string } = {}
    let region = ''

    for (const [key, value] of Object.entries(values) as [string, any][]) {
      if (key === 'ColorGroup') continue // Skip the 'ColorGroup' key.

      if (typeof value === 'string') {
        if (key === 'Region') region = value
        else if (key === 'RegionLabel') newValues[value == null ? '' : value] = region
        else newValues[key] = value
      } else if (typeof value !== 'number') {
        const num = Number(value)
        let baseKey = 'Area',
          unit = ' km²'

        if (!key.startsWith('Geographic Area')) {
          baseKey = key
            .replace(/\s*\(([^)]+)\)/, (_, p1) => {
              unit = ' ' + p1
              return ''
            })
            .trim()
        }

        newValues[baseKey] =
          new Intl.NumberFormat(LOCALE, {
            notation: 'compact',
            compactDisplay: 'short',
            maximumFractionDigits: 3
          }).format(num) + unit
      }
    }

    // Delegate to the default formatter to keep their HTML structure.
    return formatValue(newValues, sanitize, 0)
  }
}
