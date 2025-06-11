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
  { text: 'L (left)', value: 'L' },
  { text: 'R (right)', value: 'R' },
  { text: 'T (top)', value: 'T' },
  { text: 'B (bottom)', value: 'B' }
]

export const tooltipOptions = {
  theme: 'dark',
  formatTooltip: (values: any, sanitize: any) => {
    if (typeof values !== 'object') return formatValue(values, sanitize, 0)

    // Create a shallow copy of the value object with formatted numbers.
    const newValues: { [key: string]: string } = {}

    for (const [key, value] of Object.entries(values) as [string, any][]) {
      if (!value || key === 'ColorGroup') continue // Skip the 'ColorGroup' key.

      const num = Number(value)
      if (isNaN(num)) {
        if (key === 'RegionLabel') {
          newValues[value] = newValues['Region']
          delete newValues['Region']
        } else newValues[key] = value
      } else {
        let unit = ''
        let baseKey = key
          .replace(/\s*\(([^)]+)\)/, (_, p1) => {
            unit = ' ' + p1
            return ''
          })
          .trim()

        if (baseKey === 'Geographic Area') {
          baseKey = 'Area'
          unit = ' sq. km'
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
