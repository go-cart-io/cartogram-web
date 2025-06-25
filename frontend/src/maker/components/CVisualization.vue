<script setup lang="ts">
import { nextTick, watch } from 'vue'
import embed, { vega, type VisualizationSpec } from 'vega-embed'

import type { FeatureCollection } from 'geojson'
import * as config from '../../common/config'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

import spec from '../../assets/template.vg.json' with { type: 'json' }
const versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
let visView: any

defineExpose({
  reset,
  init,
  updateData,
  setDataItem
})

watch(
  () => store.colorRegionScheme,
  (newValue, oldValue) => {
    updateColorAndDataTable(newValue, oldValue)
  }
)

function reset() {
  document.getElementById('map-vis')!.innerHTML = ''
}

async function init(geojsonData: FeatureCollection, geojsonRegionCol: string) {
  reset()
  versionSpec.data[1].values = geojsonData
  versionSpec.data[2].transform[2].fields = ['properties.' + geojsonRegionCol]
  versionSpec.data[0].values = store.dataTable.items
  versionSpec.data[0].format = 'json'
  if (store.colorRegionScheme !== 'custom') versionSpec.signals[3].value = store.colorRegionScheme

  const container = await embed('#map-vis', <VisualizationSpec>versionSpec, {
    renderer: 'svg',
    actions: false,
    tooltip: config.tooltipOptions
  })
  visView = container.view
}

function updateData() {
  nextTick() // Ensure that dataTable is updated
  visView.data('source_csv', store.dataTable.items).runAsync()
}

function setDataItem(row: string, col: string, value: string) {
  const changeset = visView.changeset().modify((item: any) => item.Region === row, col, value)
  visView.change('source_csv', changeset).run()
}

function updateColorAndDataTable(scheme: string, oldScheme: string) {
  if (scheme === oldScheme) return
  if (scheme === 'custom') {
    // Copy all color from Vega to data table
    const colorScale = visView.scale('color_group')
    for (let i = 0; i < store.dataTable.items.length; i++) {
      store.dataTable.items[i]['Color'] = colorScale(store.dataTable.items[i]['ColorGroup'])
    }

    store.dataTable.fields[config.COL_COLOR].show = true
  } else {
    for (let i = 0; i < store.dataTable.items.length; i++) {
      delete store.dataTable.items[i]['Color']
    }

    store.dataTable.fields[config.COL_COLOR].show = false
    visView.signal('color_scheme', scheme).runAsync()
  }
}
</script>

<template>
  <div id="map-vis" class="vis-area p-2"></div>
</template>

<style scoped>
.vis-area {
  width: 100%;
  height: 300px;
}
</style>
