import type { VisualizationSpec } from 'vega-embed'
import embed from 'vega-embed'

import spec from '../assets/template.vg.json' with { type: 'json' }
import specLegend from '../assets/template_legend.vg.json' with { type: 'json' }
import * as config from './config'
import type { View } from 'vega'

function reset(canvasId: string) {
  document.getElementById(canvasId)!.innerHTML = ''
}

export async function initWithURL(
  canvasId: string,
  csvUrl: string,
  jsonUrl: string,
  currentColorCol: string,
  cartoColorScheme: string,
  choroSpec: any
) {
  const versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
  versionSpec.data[0].url = csvUrl
  versionSpec.data[1].url = jsonUrl

  return await init(canvasId, versionSpec, currentColorCol, cartoColorScheme, choroSpec)
}

export async function initWithValues(
  canvasId: string,
  csvValues: any,
  jsonValue: any,
  geojsonRegionCol: string,
  currentColorCol: string,
  cartoColorScheme: string,
  choroSpec: any
) {
  const versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
  versionSpec.data[1].values = jsonValue
  versionSpec.data[2].transform[2].fields = ['properties.' + geojsonRegionCol]
  versionSpec.data[0].values = csvValues
  versionSpec.data[0].format = 'json'

  return await init(canvasId, versionSpec, currentColorCol, cartoColorScheme, choroSpec)
}

export async function init(
  canvasId: string,
  versionSpec: any,
  currentColorCol: string,
  cartoColorScheme: string,
  choroSpec: any
) {
  reset(canvasId)

  // if (store.currentMapName === "world" && state.version.name === 'Geographic Area') {
  //   // Gall–Peters projection
  //   vega.projection('cylindricalEqualArea', geoCylindricalEqualArea)
  //   versionSpec.projections[0].type = "cylindricalEqualArea"
  //   versionSpec.projections[0].reflectY = false
  //   versionSpec.projections[0].parallel = 45
  // }

  // For color
  versionSpec.signals[3]['value'] = cartoColorScheme === 'custom' ? 'pastel1' : cartoColorScheme
  versionSpec.signals[4].value = _getColorFieldSingal(currentColorCol, cartoColorScheme)

  if (choroSpec && choroSpec.scales) {
    const escapedScales = _escapeScales(choroSpec.scales)
    versionSpec.scales = versionSpec.scales.concat(escapedScales)
  }

  const container = await embed('#' + canvasId, <VisualizationSpec>versionSpec, {
    renderer: 'svg',
    actions: false,
    tooltip: config.tooltipOptions
  })
  return container
}

export async function initLegendWithURL(
  csvUrl: string,
  currentColorCol: string,
  choroSpec: any
): Promise<View> {
  const versionSpec = JSON.parse(JSON.stringify(specLegend)) // copy the template
  versionSpec.data[0].url = csvUrl

  return await initLegend(versionSpec, currentColorCol, choroSpec)
}

export async function initLegendWithValues(
  csvValues: any,
  currentColorCol: string,
  choroSpec: any
): Promise<View> {
  const versionSpec = JSON.parse(JSON.stringify(specLegend)) // copy the template
  versionSpec.data[0].values = csvValues
  versionSpec.data[0].format = 'json'

  return await initLegend(versionSpec, currentColorCol, choroSpec)
}

export async function initLegend(
  versionSpec: any,
  currentColorCol: string,
  choroSpec: any
): Promise<View> {
  reset('legend')

  // Color legend don't use color scheme - just fill in the default value to avoid error
  versionSpec.signals[2]['value'] = 'pastel1'
  versionSpec.signals[3].value = _getColorFieldSingal(currentColorCol, 'pastel1')

  if (choroSpec && choroSpec.scales) {
    const escapedScales = _escapeScales(choroSpec.scales)
    versionSpec.scales = versionSpec.scales.concat(escapedScales)
  }

  versionSpec.legends[0].title =
    currentColorCol === 'Region'
      ? ''
      : choroSpec['legend_titles'] && choroSpec['legend_titles'][currentColorCol]
        ? choroSpec['legend_titles'][currentColorCol]
        : currentColorCol
  versionSpec.legends[0].fill = currentColorCol === 'Region' ? 'color_group' : currentColorCol

  const container = await embed('#legend', <VisualizationSpec>versionSpec, {
    renderer: 'svg',
    actions: false
  })
  return container.view
}

// As we allow dot in data name and unit, we need to escape the dot in the field name so vega can process it
function _escapeScales(scales: any) {
  if (!scales) return []

  let escapedScales = JSON.parse(JSON.stringify(scales))
  escapedScales.forEach((scale: any) => {
    if (scale.domain && scale.domain.field) {
      scale.domain.field = scale.domain.field.replace(/\./g, '\\.')
    }
  })

  return escapedScales
}

export function _getColorFieldSingal(currentColorCol: string, cartoColorScheme: string): string {
  return currentColorCol !== 'Region'
    ? currentColorCol
    : cartoColorScheme === 'custom'
      ? 'Color'
      : 'ColorGroup'
}
