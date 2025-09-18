<script setup lang="ts">
import { nextTick, reactive, ref, watch } from 'vue'

import type { FeatureCollection } from 'geojson'
import * as config from '@/common/lib/config'
import CColorLegend from '@/common/components/CColorLegend.vue'
import CVisualizationArea from '@/common/components/CVisualizationArea.vue'

import * as datatable from '../lib/datatable'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

let currentGeojsonData: FeatureCollection | null
let currentGeojsonRegionCol: string
const colorLegendEl = ref()
const visAreaEl = ref()

const state = reactive({
  isInit: false,
  colorFields: [] as string[]
})

defineExpose({
  reset,
  refresh,
  init,
  updateColorFields,
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

watch(
  () => store.title,
  async () => {
    await colorLegendEl.value.resize()
  }
)

function reset() {
  state.isInit = false
  currentGeojsonData = null
  currentGeojsonRegionCol = ''
  visAreaEl.value.reset()
  colorLegendEl.value.reset()
}

function refresh() {
  if (currentGeojsonData) init(currentGeojsonData, currentGeojsonRegionCol)
}

async function init(geojsonData: FeatureCollection, geojsonRegionCol: string) {
  reset()
  currentGeojsonData = geojsonData
  currentGeojsonRegionCol = geojsonRegionCol

  const customScaleSpec = JSON.parse(store.choroSettings.spec)
  await visAreaEl.value.initWithValues(
    'preview-vis',
    store.dataTable.items,
    geojsonData,
    geojsonRegionCol,
    store.currentColorCol,
    store.cartoColorScheme,
    customScaleSpec
  )

  await colorLegendEl.value.initColorLegendWithValues(
    store.dataTable.items,
    store.currentColorCol,
    customScaleSpec
  )
  state.isInit = true
}

function updateColorFields(needRefresh = true) {
  state.colorFields = datatable.getColsByVisType(store.dataTable, 'choropleth')
  datatable.updateChoroSpec()

  if (!state.colorFields.includes(store.currentColorCol)) {
    store.currentColorCol = 'Region'
    if (needRefresh) refresh()
  }
}

async function updateData() {
  await nextTick() // Ensure that dataTable is updated
  updateColorFields(false)
  refresh()
}

function setDataItem(row: string, col: string, value: string) {
  if (!visAreaEl.value.view()) return
  const changeset = visAreaEl.value
    .view()
    .changeset()
    .modify((item: any) => item.Region === row, col, value)
  visAreaEl.value.view().change('source_csv', changeset).run()
}

function updateColorAndDataTable(scheme: string, oldScheme: string) {
  if (scheme === oldScheme || !visAreaEl.value.view() || !store.dataTable.fields) return
  if (scheme === 'custom') {
    // Copy colors from Vega to the data table **only if no color is already assigned**
    // The condition is crucial because csv uploading populates the color column before applies the custom scheme
    const colorScale = visAreaEl.value.view().scale('color_group')
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
    visAreaEl.value.view().signal('color_scheme', scheme).runAsync()
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
  store.dataTable.items[rIndex].Region = undefined

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
    class="d-flex flex-wrap flex-sm-nowrap align-items-center w-100 bg-light border p-2 m-2 gap-2"
    v-bind:style="{ visibility: state.isInit ? 'visible' : 'hidden' }"
  >
    <div class="flex-shrink-0 text-truncate" style="min-width: 0; max-width: 50%">
      <strong>{{ store.title }}</strong>
    </div>

    <div class="flex-grow-1">
      <c-color-legend
        ref="colorLegendEl"
        v-bind:colorFields="state.colorFields"
        v-bind:currentColorCol="store.currentColorCol"
        v-on:change="
          (col: string) => {
            store.currentColorCol = col
            refresh()
          }
        "
      />
    </div>
  </div>

  <div class="position-absolute px-2">
    <small v-if="store.dataTable.items.length > 0">
      Preview may be outdated after geometric changes (e.g., insets). Final output is unaffected.
    </small>
  </div>

  <div class="position-relative w-100" style="height: 300px">
    <c-visualization-area ref="visAreaEl" panelID="preview"></c-visualization-area>
  </div>
</template>
