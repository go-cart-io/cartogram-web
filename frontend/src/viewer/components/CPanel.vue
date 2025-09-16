<script setup lang="ts">
/**
 * The map panel with functions for interactivity to manipulate viewport and managing grid size.
 */
import { onMounted, nextTick, reactive, watch, ref } from 'vue'

import CVisualizationArea from '@/common/components/CVisualizationArea.vue'

import * as animate from '../lib/animate'
import * as util from '../lib/util'
import { useAreaLegend } from '../composables/useAreaLegend'

import CPanelLegend from './CPanelLegend.vue'
import CPanelSelectVersion from './CPanelSelectVersion.vue'
import CPanelBtnDownload from './CPanelBtnDownload.vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

const legendLineEl = ref()
const visAreaEl = ref()

const props = defineProps<{
  panelID: string
  defaultVersionKey: string
}>()

const areaLegend = useAreaLegend()

const state = reactive({
  versionKey: props.defaultVersionKey,
  currentGridIndex: 1
})

watch(
  () => store.highlightedRegionID,
  (id) => {
    visAreaEl.value.view()?.signal('active', id).runAsync()
  }
)

watch(
  () => store.options.numberOfPanels,
  async () => {
    visAreaEl.value.resize()
    switchGrid(state.currentGridIndex)
  }
)

watch(
  () => store.currentColorCol,
  () => {
    init()
  }
)

onMounted(async () => {
  await init()
  switchGrid(state.currentGridIndex)
})

async function initContainer(canvasId: string) {
  const csvUrl = util.getCsvURL(store.currentMapName, CARTOGRAM_CONFIG.mapDBKey)
  const jsonUrl = util.getGeojsonURL(
    store.currentMapName,
    CARTOGRAM_CONFIG.mapDBKey,
    CARTOGRAM_CONFIG.cartoVersions[state.versionKey].name + '.json'
  )

  let underlyingJsonUrl = null
  const isContiguous = CARTOGRAM_CONFIG.cartoVersions[state.versionKey].type === 'contiguous'
  if (window.CARTOGRAM_CONFIG.cartoEqualAreaBg)
    underlyingJsonUrl = util.getGeojsonURL(
      store.currentMapName,
      CARTOGRAM_CONFIG.mapDBKey,
      isContiguous
        ? CARTOGRAM_CONFIG.cartoVersions[state.versionKey].name + '.json'
        : 'Geographic Area.json'
    )

  await visAreaEl.value.initWithURL(
    canvasId,
    csvUrl,
    jsonUrl,
    underlyingJsonUrl,
    store.currentColorCol,
    CARTOGRAM_CONFIG.cartoColorScheme || 'pastel1',
    CARTOGRAM_CONFIG.choroSpec
  )

  if (isContiguous)
    areaLegend.init(
      CARTOGRAM_CONFIG.cartoVersions[state.versionKey].header,
      visAreaEl.value.view().data('geo_1'),
      visAreaEl.value.view().data('source_csv')
    )
  else
    areaLegend.init(
      CARTOGRAM_CONFIG.cartoVersions['0'].header,
      visAreaEl.value.view().data('equal_area_geojson'),
      visAreaEl.value.view().data('source_csv')
    )
}

async function init() {
  await initContainer(props.panelID + '-vis')
  let visView = visAreaEl.value.view()

  visView.addResizeListener(function () {
    areaLegend.updateTotalArea(visView.data('geo_1'))
    switchGrid(state.currentGridIndex)
  })

  visView.addSignalListener('active', function (name: string, value: any) {
    store.highlightedRegionID = value
  })

  visView.addEventListener('pointerup', function (event: any, item: any) {
    const value = item?.datum.cartogram_data
    visView.tooltip()(visView, event, item, value)
  })
}

async function switchVersion(versionKey: string) {
  state.versionKey = versionKey
  await initContainer(props.panelID + '-offscreen')
  switchGrid(state.currentGridIndex)

  function finalize() {
    let visView = visAreaEl.value.view()
    visView.runAfter(() => visAreaEl.value.transform.applyCurrent())
    visView.initialize('#' + props.panelID + '-vis').runAsync()
  }

  animate.geoTransition(props.panelID, finalize)
}

async function switchGrid(key: number) {
  state.currentGridIndex = key
  areaLegend.updateGridData()
  await nextTick()
  visAreaEl.value.transform.setGridScaleNiceNumber(
    areaLegend.stateGridData.value[state.currentGridIndex]?.scaleNiceNumber
  )
  areaLegend.updateLegendValue(
    state.currentGridIndex,
    visAreaEl.value.transform.stateAffineScale.value
  )
  legendLineEl.value.setHandlePosition(areaLegend.stateGridData.value[key]?.width)
  animate.gridTransition(props.panelID + '-grid', areaLegend.stateGridData.value[key]?.width)
}
</script>

<template>
  <div class="card w-100">
    <div class="d-flex flex-column card-body">
      <div class="d-flex flex-column card-body p-0">
        <div
          class="position-absolute z-1"
          v-bind:class="{
            'd-flex': CARTOGRAM_CONFIG.cartoVersions[state.versionKey]?.type !== 'noncontiguous',
            'd-none': CARTOGRAM_CONFIG.cartoVersions[state.versionKey]?.type === 'noncontiguous'
          }"
        >
          <c-panel-legend
            ref="legendLineEl"
            v-bind:panelID="props.panelID"
            v-bind:gridIndex="state.currentGridIndex"
            v-bind:gridData="areaLegend.stateGridData.value"
            v-on:change="switchGrid"
          />
          <div v-bind:id="props.panelID + '-legend-text'" class="flex-fill p-1">
            <div v-bind:id="props.panelID + '-legend-num'">
              <span v-html="areaLegend.stateValue.value"></span>
              {{ CARTOGRAM_CONFIG.cartoVersions[state.versionKey]?.unit }}
            </div>
            <div v-bind:id="props.panelID + '-legend-total'">
              Total: <span v-html="areaLegend.stateTotalValue.value"></span>
            </div>
          </div>
        </div>

        <c-visualization-area
          ref="visAreaEl"
          v-bind:panelID="props.panelID"
          v-on:transformChanged="
            (transform) =>
              areaLegend.updateLegendValue(state.currentGridIndex, transform.stateAffineScale.value)
          "
        >
          <svg width="100%" height="100%" v-bind:id="props.panelID + '-grid-area'">
            <defs>
              <pattern v-bind:id="props.panelID + '-grid'" patternUnits="userSpaceOnUse">
                <path
                  fill="none"
                  stroke="#5A5A5A"
                  stroke-width="2"
                  v-bind:stroke-opacity="store.options.gridOpacity"
                ></path>
              </pattern>
            </defs>
            <rect
              width="100%"
              height="100%"
              v-bind:fill="'url(#' + props.panelID + '-grid)'"
            ></rect>
          </svg>
        </c-visualization-area>
      </div>
    </div>

    <div class="card-footer d-flex justify-content-between gap-2">
      <c-panel-select-version
        v-bind:panelID="props.panelID"
        v-bind:currentVersionName="state.versionKey"
        v-on:version_changed="(versionKey) => switchVersion(versionKey)"
      />
      <c-panel-btn-download v-bind:versionKey="state.versionKey" v-bind:panelID="props.panelID" />
    </div>
  </div>
</template>

<style>
path {
  mix-blend-mode: multiply;
}
path[aria-label='dividers'] {
  mix-blend-mode: normal;
}
</style>
