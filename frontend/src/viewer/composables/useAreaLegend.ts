import { ref } from 'vue'

import * as config from '@/common/lib/config'
import * as numberUtil from '@/common/lib/numberUtil'
import type { GridData } from '../lib/viewInterface'

export const useAreaLegend = () => {
  const stateValue = ref('')
  const stateTotalValue = ref('')
  const stateGridData = ref<GridData>({})

  let totalArea = 0
  let totalValue = 0
  let valueScalePowerOf10 = 1

  // Calculate total areas and values for version
  // The area will change based on window width
  const init = (versionName: string, features: any, data: any): void => {
    totalArea = 0
    totalValue = 0

    const na_names: Array<string> = []
    let na_areas: Array<number> = []

    // Sum the values except the rows with NA values. Keep track of NA rows.
    data.forEach((row: any) => {
      if (
        row[versionName] &&
        row[versionName].toString() !== '' &&
        row[versionName].toString() !== 'NA'
      ) {
        const value =
          typeof row[versionName] === 'string' ? Number(row[versionName]) : row[versionName]
        totalValue += value
      } else {
        na_names.push(row['Region'])
      }
    })

    // Sum the area except the rows with NA values. Keep track of the area with NA values.
    na_areas = Array(na_names.length)
    features.forEach((feature: any) => {
      const na_index = na_names.indexOf(feature['Region'])
      if (na_index > -1) na_areas[na_index] = feature['Area']
      else totalArea += feature['Area']
    })

    // Calculate average density and add them to total value
    // Add NA area to total area - now total area is the sum of all area
    const avg_density = totalValue / totalArea
    na_areas.forEach(function (na_area) {
      totalValue += avg_density * na_area
      totalArea += na_area
    })

    const totalScalePowerOfTen = Math.floor(Math.log10(totalValue))
    const totalNiceNumber = totalValue / Math.pow(10, totalScalePowerOfTen)
    stateTotalValue.value = _formatLegendText(totalNiceNumber, totalScalePowerOfTen)
  }

  const updateLegendValue = (gridIndex: number, affineScale: Array<number>) => {
    if (!stateGridData.value[gridIndex]) {
      stateValue.value = ''
      return
    }

    let value = stateGridData.value[gridIndex].scaleNiceNumber
    value = value / (affineScale[0] * affineScale[1])
    stateValue.value = _formatLegendText(value, valueScalePowerOf10)
  }

  const updateTotalArea = (features: any): void => {
    totalArea = 0
    features.forEach((feature: any) => {
      totalArea += feature['Area']
    })
  }

  // Calculates grid information of the map version
  const updateGridData = () => {
    if (totalValue === 0 || totalArea === 0) return

    const valuePerPixel = totalValue / totalArea
    // Each square to be in the whereabouts of 1% of totalValue.
    let valuePerSquare = totalValue / 100
    let baseWidth = Math.sqrt(valuePerSquare / valuePerPixel)
    // If width is too small, we increment the percentage.
    while (baseWidth < 20) {
      valuePerSquare *= 2
      baseWidth = Math.sqrt(valuePerSquare / valuePerPixel)
    }

    const [scaleNiceNumber0, scalePowerOf10] = numberUtil.findNearestNiceNumber(valuePerSquare)
    const niceIndex = numberUtil.NICE_NUMBERS.indexOf(scaleNiceNumber0)
    let beginIndex = niceIndex === 0 ? niceIndex : niceIndex - 1
    let endIndex = beginIndex + config.NUM_GRID_OPTIONS + 1
    while (endIndex >= numberUtil.NICE_NUMBERS.length && beginIndex > 0) {
      endIndex--
      beginIndex--
    }
    const scaleNiceNumber = numberUtil.NICE_NUMBERS.slice(beginIndex, endIndex)

    // Store legend Information
    for (let i = 0; i <= config.NUM_GRID_OPTIONS; i++) {
      stateGridData.value[i] = {
        scaleNiceNumber: scaleNiceNumber[i],
        width:
          baseWidth *
          Math.sqrt((scaleNiceNumber[i] * Math.pow(10, scalePowerOf10)) / valuePerSquare)
      }
    }

    valueScalePowerOf10 = scalePowerOf10
  }

  const _formatLegendText = (value: number, scalePowerOf10: number): string => {
    const originalValue = value * Math.pow(10, scalePowerOf10)
    const formatter = Intl.NumberFormat(config.LOCALE, {
      notation: 'compact',
      compactDisplay: 'short'
    })
    let formated = ''
    formated += formatter.format(originalValue)
    return formated
  }

  return {
    stateValue,
    stateTotalValue,
    stateGridData,
    init,
    updateLegendValue,
    updateTotalArea,
    updateGridData
  }
}
