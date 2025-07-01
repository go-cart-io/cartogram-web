import type { VisualizationSpec } from 'vega-embed'
import embed from 'vega-embed'

import spec from '../../assets/template.vg.json' with { type: 'json' }
import specLegend from '../../assets/template_legend.vg.json' with { type: 'json' }
import * as config from '../../common/config'
import * as util from '../lib/util'

import { useCartogramStore } from '../stores/cartogram'
const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

function reset(canvasId: string) {
  document.getElementById(canvasId)!.innerHTML = ''
}

export async function init(canvasId: string, versionName: string) {
  reset(canvasId)

  const store = useCartogramStore()
  const versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
  versionSpec.data[0].url = util.getCsvURL(store.currentMapName, CARTOGRAM_CONFIG.mapDBKey)
  versionSpec.data[1].url = util.getGeojsonURL(
    store.currentMapName,
    CARTOGRAM_CONFIG.mapDBKey,
    versionName + '.json'
  )

  // if (store.currentMapName === "world" && state.version.name === 'Geographic Area') {
  //   // Gall–Peters projection
  //   vega.projection('cylindricalEqualArea', geoCylindricalEqualArea)
  //   versionSpec.projections[0].type = "cylindricalEqualArea"
  //   versionSpec.projections[0].reflectY = false
  //   versionSpec.projections[0].parallel = 45
  // }

  // For color
  versionSpec.signals[3]['value'] =
    !CARTOGRAM_CONFIG.cartoColorScheme || CARTOGRAM_CONFIG.cartoColorScheme === 'custom'
      ? 'pastel1'
      : CARTOGRAM_CONFIG.cartoColorScheme

  if (CARTOGRAM_CONFIG.choroSpec && CARTOGRAM_CONFIG.choroSpec.scales)
    versionSpec.scales = versionSpec.scales.concat(CARTOGRAM_CONFIG.choroSpec.scales)

  versionSpec.signals[4].value =
    store.currentColorCol && store.currentColorCol !== 'Region'
      ? store.currentColorCol
      : CARTOGRAM_CONFIG.cartoColorScheme === 'custom'
        ? 'Color'
        : 'ColorGroup'

  const container = await embed('#' + canvasId, <VisualizationSpec>versionSpec, {
    renderer: 'svg',
    actions: false,
    tooltip: config.tooltipOptions
  })
  return container
}

export async function initLegend() {
  reset('legend')
  const store = useCartogramStore()
  const versionSpec = JSON.parse(JSON.stringify(specLegend)) // copy the template
  versionSpec.data[0].url = util.getCsvURL(store.currentMapName, CARTOGRAM_CONFIG.mapDBKey)

  // For color
  versionSpec.signals[2]['value'] =
    !CARTOGRAM_CONFIG.cartoColorScheme || CARTOGRAM_CONFIG.cartoColorScheme === 'custom'
      ? 'pastel1'
      : CARTOGRAM_CONFIG.cartoColorScheme

  if (CARTOGRAM_CONFIG.choroSpec && CARTOGRAM_CONFIG.choroSpec.scales)
    versionSpec.scales = versionSpec.scales.concat(CARTOGRAM_CONFIG.choroSpec.scales)

  versionSpec.signals[3].value =
    store.currentColorCol && store.currentColorCol !== 'Region'
      ? store.currentColorCol
      : CARTOGRAM_CONFIG.cartoColorScheme === 'custom'
        ? 'Color'
        : 'ColorGroup'
  versionSpec.legends[0].fill =
    store.currentColorCol === 'Region' ? 'color_group' : store.currentColorCol

  const container = await embed('#legend', <VisualizationSpec>versionSpec, {
    renderer: 'svg',
    actions: false
  })
  return container
}
