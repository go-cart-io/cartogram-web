import type { FeatureCollection } from 'geojson'
import type { VisualizationSpec } from 'vega-embed'
import type { Spec, InitSignal, Text as VegaText, View, Scale } from 'vega'
import embed from 'vega-embed'

// Import Vega specs for main visualization and legend
import spec from '../assets/template.vg.json' with { type: 'json' }
import specLegend from '../assets/template_legend.vg.json' with { type: 'json' }

import type { CSettingSpec, StringObject } from './interface'
import * as config from './config'

/**
 * Reset the inner HTML of the given canvas element.
 * @param canvasId - The DOM id of the canvas to reset.
 */
export function reset(canvasId: string): void {
  const el = document.getElementById(canvasId)
  if (el) el.innerHTML = ''
}

/**
 * Initialize visualization from CSV and GeoJSON URLs.
 */
export async function initWithURL(
  canvasId: string,
  csvUrl: string,
  jsonUrl: string,
  currentColorCol: string,
  cartoColorScheme: string,
  choroSpec: CSettingSpec
): Promise<View> {
  const versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
  versionSpec.data[0].url = csvUrl
  versionSpec.data[1].url = jsonUrl
  return await init(canvasId, versionSpec, currentColorCol, cartoColorScheme, choroSpec)
}

/**
 * Initialize visualization from CSV and GeoJSON values.
 */
export async function initWithValues(
  canvasId: string,
  csvValues: StringObject[],
  jsonValue: FeatureCollection,
  geojsonRegionCol: string,
  currentColorCol: string,
  cartoColorScheme: string,
  choroSpec: CSettingSpec
): Promise<View> {
  const versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
  versionSpec.data[1].values = jsonValue
  versionSpec.data[2].transform[2].fields = ['properties.' + geojsonRegionCol]
  versionSpec.data[0].values = csvValues
  versionSpec.data[0].format = 'json'
  return await init(canvasId, versionSpec, currentColorCol, cartoColorScheme, choroSpec)
}

/**
 * Core initialization for visualization embedding.
 */
export async function init(
  canvasId: string,
  versionSpec: Spec,
  currentColorCol: string,
  cartoColorScheme: string,
  choroSpec: CSettingSpec
): Promise<View> {
  reset(canvasId)
  versionSpec = _setColorSingals(versionSpec, currentColorCol, cartoColorScheme)
  if (choroSpec?.scales && versionSpec.scales) {
    const escapedScales = _escapeScales(choroSpec.scales)
    versionSpec.scales = versionSpec.scales.concat(escapedScales)
  }
  const container = await embed(`#${canvasId}`, versionSpec as VisualizationSpec, {
    renderer: 'svg',
    actions: false,
    tooltip: config.tooltipOptions
  })
  return container.view
}

/**
 * Initialize legend from CSV URL.
 */
export async function initLegendWithURL(
  csvUrl: string,
  currentColorCol: string,
  choroSpec: CSettingSpec
): Promise<View> {
  const versionSpec = JSON.parse(JSON.stringify(specLegend)) // copy the template
  versionSpec.data[0].url = csvUrl
  return await initLegend(versionSpec, currentColorCol, choroSpec)
}

/**
 * Initialize legend from CSV values.
 */
export async function initLegendWithValues(
  csvValues: StringObject[],
  currentColorCol: string,
  choroSpec: CSettingSpec
): Promise<View> {
  const versionSpec = JSON.parse(JSON.stringify(specLegend))
  versionSpec.data[0].values = csvValues
  versionSpec.data[0].format = 'json'
  return await initLegend(versionSpec, currentColorCol, choroSpec)
}

/**
 * Core initialization for legend embedding.
 */
export async function initLegend(
  versionSpec: Spec,
  currentColorCol: string,
  choroSpec: CSettingSpec
): Promise<View> {
  reset('legend')
  // Color legend doesn't use color scheme - fill default to avoid error
  versionSpec = _setColorSingals(versionSpec, currentColorCol, 'pastel1')

  if (choroSpec?.scales && versionSpec.scales) {
    const escapedScales = _escapeScales(choroSpec.scales)
    versionSpec.scales = versionSpec.scales.concat(escapedScales)
  }

  if (versionSpec.legends) {
    const title =
      currentColorCol === 'Region'
        ? ''
        : (choroSpec['legend_titles']?.[currentColorCol] ?? currentColorCol)
    versionSpec.legends[0].title = title as VegaText
    versionSpec.legends[0].fill = currentColorCol === 'Region' ? 'color_group' : currentColorCol
  }

  const container = await embed('#legend', versionSpec as VisualizationSpec, {
    renderer: 'svg',
    actions: false
  })
  return container.view
}

/**
 * Escape dots in scale domain field names for Vega compatibility.
 */
function _escapeScales(scales: Scale[]): Scale[] {
  if (!scales) return []
  const escapedScales: Scale[] = structuredClone(scales)
  escapedScales.forEach((scale) => {
    if (
      scale.domain &&
      typeof scale.domain === 'object' &&
      'field' in scale.domain &&
      typeof scale.domain.field === 'string'
    ) {
      scale.domain.field = scale.domain.field.replace(/\./g, '\\.')
    }
  })
  return escapedScales
}

/**
 * Set color signals in Vega spec for color scheme and column.
 */
export function _setColorSingals(
  versionSpec: Spec,
  currentColorCol: string,
  cartoColorScheme: string
): Spec {
  if (!versionSpec.signals) return versionSpec
  // Set color_scheme signal
  if (versionSpec.signals[3]) {
    ;(versionSpec.signals[3] as InitSignal).value =
      cartoColorScheme === 'custom' ? 'pastel1' : cartoColorScheme
  }
  // Set color_field signal
  if (versionSpec.signals[4]) {
    ;(versionSpec.signals[4] as InitSignal).value =
      currentColorCol !== 'Region'
        ? currentColorCol
        : cartoColorScheme === 'custom'
          ? 'Color'
          : 'ColorGroup'
  }

  return versionSpec
}
