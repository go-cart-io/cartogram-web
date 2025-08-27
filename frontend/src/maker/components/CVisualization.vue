<script setup lang="ts">
import { nextTick, reactive, watch } from 'vue'

import type { FeatureCollection } from 'geojson'
import * as visualization from '../../common/visualization'
import * as config from '../../common/config'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

let visView: any
let currentGeojsonData: FeatureCollection | null
let currentGeojsonRegionCol: string

const state = reactive({
  isInit: false,
  currentColorCol: 'Region'
})

defineExpose({
  reset,
  refresh,
  init,
  updateData,
  setDataItem,
  resolveRegionIssues
})

watch(
  () => store.cartoColorScheme,
  (newValue, oldValue) => {
    updateColorAndDataTable(newValue, oldValue)
  }
)

function reset() {
  state.isInit = false
  document.getElementById('map-vis')!.innerHTML = ''
  document.getElementById('legend')!.innerHTML = ''
  currentGeojsonData = null
  currentGeojsonRegionCol = ''
}

function refresh() {
  if (currentGeojsonData) init(currentGeojsonData, currentGeojsonRegionCol)
}

async function init(geojsonData: FeatureCollection, geojsonRegionCol: string) {
  reset()
  store.updateChoroSpec()
  currentGeojsonData = geojsonData
  currentGeojsonRegionCol = geojsonRegionCol

  const customScaleSpec = JSON.parse(store.choroSettings.spec)
  const container = await visualization.initWithValues(
    'map-vis',
    store.dataTable.items,
    geojsonData,
    geojsonRegionCol,
    state.currentColorCol,
    store.cartoColorScheme,
    customScaleSpec
  )
  visView = container.view

  await visualization.initLegendWithValues(
    store.dataTable.items,
    state.currentColorCol,
    store.cartoColorScheme,
    customScaleSpec
  )
  state.isInit = true
}

async function updateData() {
  await nextTick() // Ensure that dataTable is updated
  refresh()
}

function setDataItem(row: string, col: string, value: string) {
  const changeset = visView.changeset().modify((item: any) => item.Region === row, col, value)
  visView.change('source_csv', changeset).run()
}

function updateColorAndDataTable(scheme: string, oldScheme: string) {
  if (scheme === oldScheme || !visView || !store.dataTable.fields) return
  if (scheme === 'custom') {
    // Copy colors from Vega to the data table **only if no color is already assigned**
    // The condition is crucial because csv uploading populates the color column before applies the custom scheme
    const colorScale = visView.scale('color_group')
    for (let i = 0; i < store.dataTable.items.length; i++) {
      if (!store.dataTable.items[i]['Color'])
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

async function resolveRegionIssues() {
  if (store.regionWarnings.size <= 0) return
  if (
    !window.confirm(
      'Click "OK" to apply changes. The changes cannot be undone unless re-uploading the data.'
    )
  )
    return

  // Apply changes
  for (const index of store.regionWarnings) {
    const actionEl = document.getElementById('dtable-region-' + index) as HTMLSelectElement
    const action = actionEl?.value

    if (action === 'dropRegion') {
      deleteRegion(index)
    } else if (store.dataTable.items[index].Region !== action) {
      renameRegion(index, action)
    }
  }

  // Clear warnings
  store.regionWarnings.clear()
  store.regionData = []

  updateData()
}

function deleteRegion(rIndex: number) {
  const region = store.dataTable.items[rIndex].Region
  store.dataTable.items[rIndex].Region = null

  if (!currentGeojsonData) return
  const filteredFeatures = currentGeojsonData.features.filter((feature) => {
    return feature.properties && feature.properties[currentGeojsonRegionCol] !== region
  })
  currentGeojsonData = { ...currentGeojsonData, features: filteredFeatures }
}

function renameRegion(rIndex: number, action: string) {
  const oldName = store.dataTable.items[rIndex].Region
  const baseItem = store.dataTable.items[rIndex]
  const newItem = store.regionData[parseInt(action)]
  store.dataTable.items[rIndex] = { ...baseItem, ...newItem }
  const newName = store.dataTable.items[rIndex].Region

  if (!currentGeojsonData) return
  currentGeojsonData.features.forEach((feature) => {
    if (feature.properties && feature.properties[currentGeojsonRegionCol] === oldName) {
      feature.properties[currentGeojsonRegionCol] = newName
    }
  })
}
</script>

<template>
  <div
    class="row border p-2 m-2 bg-light"
    v-bind:style="{ visibility: state.isInit ? 'visible' : 'hidden' }"
  >
    <div class="col-2 d-flex align-items-center">
      <strong class="text-truncate">{{ store.title }}</strong>
    </div>

    <div class="col-5 col-lg-4">
      <div class="input-group flex-nowrap">
        <span class="input-group-text">By</span>
        <select
          id="color-options"
          class="form-select"
          title="Select map/cartogram color strategy"
          v-model="state.currentColorCol"
          v-on:change="refresh"
        >
          <option value="Region">Region</option>
          <option disabled>Data:</option>
          <option
            disabled
            v-if="!store.visTypes['choropleth'] || !store.visTypes['choropleth'].length"
          >
            &nbsp;&nbsp;No choropleth column
          </option>
          <option
            v-for="label in store.visTypes['choropleth']"
            v-bind:value="label"
            v-bind:key="label"
          >
            &nbsp;&nbsp;{{ label }}
          </option>
        </select>
      </div>
    </div>

    <div class="col-5 col-lg-6 p-0">
      <div id="legend" class="d-block"></div>
    </div>
  </div>

  <div class="position-absolute">
    <small v-if="store.dataTable.items.length > 0">
      Preview may be outdated after geometric changes (e.g., insets). Final output is unaffected.
    </small>
  </div>
  <div id="map-vis" class="vis-area p-2"></div>
</template>

<style scoped>
.vis-area {
  width: 100%;
  height: 300px;
}

#legend,
#legend svg {
  height: 100%;
}
</style>
