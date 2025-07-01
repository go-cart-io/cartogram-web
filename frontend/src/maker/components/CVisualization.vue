<script setup lang="ts">
import { computed, nextTick, reactive, watch } from 'vue'
import embed, { vega, type VisualizationSpec } from 'vega-embed'

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
  setDataItem
})

watch(
  () => store.colorRegionScheme,
  (newValue, oldValue) => {
    updateColorAndDataTable(newValue, oldValue)
  }
)

function reset() {
  state.isInit = false
  document.getElementById('map-vis')!.innerHTML = ''
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
    store.colorRegionScheme,
    customScaleSpec
  )
  visView = container.view
  state.isInit = true
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

  <div v-if="state.isInit" class="position-absolute d-flex p-2" style="max-width: 50%">
    <div class="input-group pe-2">
      <span class="input-group-text">Preview by</span>
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
    </div>
    <button class="btn btn-outline-secondary" type="button" v-on:click="refresh">
      <i class="btn-icon fa fa-refresh"></i>
    </button>
  </div>
</template>

<style scoped>
.vis-area {
  width: 100%;
  height: 300px;
}
</style>
