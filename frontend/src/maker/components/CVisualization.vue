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
  let deletedIndexTotal = 0 // We need to re-adjust the indexes if we delete an item
  for (const index of store.regionWarnings) {
    // The id of HTML select element remains the same regardless to deleted item
    const actionEl = document.getElementById('regionWarningAction' + index) as HTMLSelectElement
    const action = actionEl?.value

    // Index of data items must be adjusted
    let rIndex = index - deletedIndexTotal
    if (action === 'dropRegion') {
      deleteRegion(rIndex)
      deletedIndexTotal++
    } else if (store.dataTable.items[rIndex].Region !== action) {
      renameRegion(rIndex, action)
    }
  }

  // Clear warnings
  store.regionWarnings.clear()
  store.regionData = []

  updateData()
}

function deleteRegion(rIndex: number) {
  const region = store.dataTable.items.splice(rIndex, 1)

  if (!currentGeojsonData) return
  const filteredFeatures = currentGeojsonData.features.filter((feature) => {
    return feature.properties?.Region !== region[0].Region
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
    if (feature.properties && feature.properties.Region === oldName) {
      feature.properties.Region = newName
    }
  })
}
</script>

<template>
  <div class="row p-2">
    <div class="col-6 col-lg-4" v-bind:style="{ visibility: state.isInit ? 'visible' : 'hidden' }">
      <div class="input-group flex-nowrap">
        <span class="input-group-text">Colored by</span>
        <select
          id="color-options"
          class="form-select"
          title="Select map/cartogram color strategy"
          v-model="state.currentColorCol"
          v-on:change="refresh"
        >
          <option value="Region">Region</option>
          <option
            v-for="label in store.visTypes['choropleth']"
            v-bind:value="label"
            v-bind:key="label"
          >
            {{ label }}
          </option>
        </select>
        <button class="btn btn-outline-secondary" type="button" v-on:click="refresh">
          <i class="btn-icon fa fa-refresh"></i>
        </button>
      </div>
    </div>

    <div class="col-6 col-lg-8 p-0">
      <div v-if="state.isInit && !store.visTypes['choropleth'].length" class="position-absolute">
        Select visualization type as "Choropleth" for more color options.
      </div>
      <div id="legend" class="d-block"></div>
    </div>
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
