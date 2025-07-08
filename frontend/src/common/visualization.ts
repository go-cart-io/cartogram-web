import type { VisualizationSpec } from 'vega-embed'
import embed from 'vega-embed'

import spec from '../assets/template.vg.json' with { type: 'json' }
import specLegend from '../assets/template_legend.vg.json' with { type: 'json' }
import * as config from './config'

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
  versionSpec.signals[3]['value'] =
    !cartoColorScheme || cartoColorScheme === 'custom' ? 'pastel1' : cartoColorScheme

  if (choroSpec && choroSpec.scales)
    versionSpec.scales = versionSpec.scales.concat(choroSpec.scales)

  versionSpec.signals[4].value =
    currentColorCol !== 'Region'
      ? currentColorCol
      : cartoColorScheme === 'custom'
        ? 'Color'
        : 'ColorGroup'

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
  cartoColorScheme: string,
  choroSpec: any
) {
  const versionSpec = JSON.parse(JSON.stringify(specLegend)) // copy the template
  versionSpec.data[0].url = csvUrl

  return await initLegend(versionSpec, currentColorCol, cartoColorScheme, choroSpec)
}

export async function initLegendWithValues(
  csvValues: any,
  currentColorCol: string,
  cartoColorScheme: string,
  choroSpec: any
) {
  const versionSpec = JSON.parse(JSON.stringify(specLegend)) // copy the template
  versionSpec.data[0].values = csvValues
  versionSpec.data[0].format = 'json'

  return await initLegend(versionSpec, currentColorCol, cartoColorScheme, choroSpec)
}

export async function initLegend(
  versionSpec: any,
  currentColorCol: string,
  cartoColorScheme: string,
  choroSpec: any
) {
  reset('legend')

  // For color
  versionSpec.signals[2]['value'] =
    !cartoColorScheme || cartoColorScheme === 'custom' ? 'pastel1' : cartoColorScheme

  if (choroSpec && choroSpec.scales)
    versionSpec.scales = versionSpec.scales.concat(choroSpec.scales)

  versionSpec.signals[3].value =
    currentColorCol !== 'Region'
      ? currentColorCol
      : cartoColorScheme === 'custom'
        ? 'Color'
        : 'ColorGroup'
  versionSpec.legends[0].fill = currentColorCol === 'Region' ? 'color_group' : currentColorCol

  const container = await embed('#legend', <VisualizationSpec>versionSpec, {
    renderer: 'svg',
    actions: false
  })
  return container
}
