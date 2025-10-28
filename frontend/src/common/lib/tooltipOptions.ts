import { formatValue } from 'vega-tooltip'
import { LOCALE } from './config'

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
            minimumSignificantDigits: 3,
            maximumSignificantDigits: 3
          }).format(num) + unit
      }
    }

    // Delegate to the default formatter to keep their HTML structure.
    return formatValue(newValues, sanitize, 0)
  }
}
