<script setup lang="ts">
/**
 * Legend wrapper for map with functions for managing grid size.
 */

import { onMounted, nextTick, reactive, watch, ref } from 'vue'
import * as d3 from 'd3'

import CPanelLegendLine from '../components/CPanelLegendLine.vue'
import { useLegend } from '../composables/useLegend'

import * as config from '../../common/config'
import * as visualization from '../../common/visualization'
import * as animate from '../lib/animate'
import * as util from '../lib/util'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG
const DEFAULT_OPACITY = 0.3

const legendLineEl = ref()
let visEl: any
let offscreenEl: any
let visView: any

const props = withDefaults(
  defineProps<{
    panelID: string
    versionKey: string
    affineScale?: any
  }>(),
  {
    affineScale: [1, 1]
  }
)

const state = reactive({
  version: CARTOGRAM_CONFIG.cartoVersions[props.versionKey],
  currentGridIndex: 1 as number
})

const legend = useLegend()

defineExpose({
  getCurrentScale
})

const emit = defineEmits(['gridChanged', 'versionUpdated'])

watch(
  () => props.versionKey,
  () => {
    state.version = CARTOGRAM_CONFIG.cartoVersions[props.versionKey]
    switchVersion()
  }
)

watch(
  () => store.highlightedRegionID,
  (id) => {
    visView?.signal('active', id).runAsync()
  }
)

watch(
  () => store.options.numberOfPanels,
  async () => {
    await visView.resize()
    await visView.width(visView.container().offsetWidth).runAsync()
    update()
  }
)

watch(
  () => store.currentColorCol,
  () => {
    init()
  }
)

watch(
  () => props.affineScale,
  () => {
    legend.updateLegendValue(state.currentGridIndex, props.affineScale)
  },
  { deep: true }
)

onMounted(async () => {
  if (!state.version) return

  visEl = d3.select('#' + props.panelID + '-vis')
  offscreenEl = d3.select('#' + props.panelID + '-offscreen')

  await init()
  update()
})

async function initContainer(canvasId: string) {
  let csvUrl = util.getCsvURL(store.currentMapName, CARTOGRAM_CONFIG.mapDBKey)
  let jsonUrl = util.getGeojsonURL(
    store.currentMapName,
    CARTOGRAM_CONFIG.mapDBKey,
    state.version.name + '.json'
  )
  const container = await visualization.initWithURL(
    canvasId,
    csvUrl,
    jsonUrl,
    store.currentColorCol,
    CARTOGRAM_CONFIG.cartoColorScheme,
    CARTOGRAM_CONFIG.choroSpec
  )

  legend.init(state.version.header, container.view.data('geo_1'), container.view.data('source_csv'))

  return container
}

async function init() {
  const container = await initContainer(props.panelID + '-vis')
  visView = container.view

  visView.addResizeListener(function () {
    legend.updateTotalArea(visView.data('geo_1'))
    update()
  })

  visView.addSignalListener('active', function (name: string, value: any) {
    store.highlightedRegionID = value
  })

  visView.addEventListener('pointerup', function (event: any, item: any) {
    const value = item?.datum.cartogram_data
    visView.tooltip()(visView, event, item, value)
  })
}

async function switchVersion() {
  const container = await initContainer(props.panelID + '-offscreen')
  update()

  function finalize() {
    container.view.runAfter(() => emit('versionUpdated'))
    container.view.initialize('#' + props.panelID + '-vis').runAsync()
    visView = container.view
  }

  animate.geoTransition(visEl, offscreenEl, finalize)
}

async function update() {
  if (!state.version) return

  legend.updateGridData()
  await nextTick()
  changeTo(state.currentGridIndex)
}

async function changeTo(key: number) {
  state.currentGridIndex = key
  await nextTick()
  legend.updateLegendValue(state.currentGridIndex, props.affineScale)
  animate.gridTransition(props.panelID + '-grid', legend.stateGridData.value[key]?.width)
  legendLineEl.value.setHandlePosition(legend.stateGridData.value[key]?.width)
  emit('gridChanged')
}

function getCurrentScale() {
  return (
    legend.stateGridData.value[state.currentGridIndex]?.scaleNiceNumber /
    (props.affineScale[0] * props.affineScale[1])
  )
}
</script>

<template>
  <div class="d-flex flex-column card-body p-0">
    <div class="d-flex position-absolute z-1">
      <c-panel-legend-line
        ref="legendLineEl"
        v-bind:panelID="props.panelID"
        v-bind:gridIndex="state.currentGridIndex"
        v-bind:gridData="legend.stateGridData.value"
        v-on:change="changeTo"
      />
      <svg
        v-if="legend.stateGridData.value[config.NUM_GRID_OPTIONS]"
        v-bind:id="props.panelID + '-legend'"
        style="cursor: pointer; opacity: 0.5"
        v-bind:width="legend.stateGridData.value[state.currentGridIndex].width + 2"
        v-bind:height="legend.stateGridData.value[state.currentGridIndex].width + 2"
      >
        <g stroke-width="2px" fill="#EEEEEE" stroke="#AAAAAA">
          <rect
            x="1"
            y="1"
            v-bind:width="legend.stateGridData.value[state.currentGridIndex].width"
            v-bind:height="legend.stateGridData.value[state.currentGridIndex].width"
          ></rect>
        </g>
      </svg>
      <div v-bind:id="props.panelID + '-legend-num'" class="flex-fill p-1">
        <span v-html="legend.stateValue.value"></span>
        {{ state.version?.unit }}
        <div>Total: <span v-html="legend.stateTotalValue.value"></span></div>
      </div>
    </div>

    <div v-bind:id="props.panelID" class="d-flex flex-fill position-relative">
      <div style="mix-blend-mode: multiply">
        <div v-bind:id="props.panelID + '-offscreen'" class="vis-area offscreen"></div>
        <div v-bind:id="props.panelID + '-vis'" class="vis-area"></div>
        <slot></slot>
      </div>
      <svg width="100%" height="100%" v-bind:id="props.panelID + '-grid-area'">
        <defs>
          <pattern v-bind:id="props.panelID + '-grid'" patternUnits="userSpaceOnUse">
            <path
              fill="none"
              stroke="#5A5A5A"
              stroke-width="2"
              v-bind:stroke-opacity="store.options.showGrid ? DEFAULT_OPACITY : 0"
            ></path>
          </pattern>
        </defs>
        <rect width="100%" height="100%" v-bind:fill="'url(#' + props.panelID + '-grid)'"></rect>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.vis-area {
  position: absolute !important;
  width: 100%;
  height: 100%;
  min-height: 100px;
}

.vis-area.offscreen {
  opacity: 0;
}
</style>

<style>
path {
  mix-blend-mode: multiply;
}
path[aria-label='dividers'] {
  mix-blend-mode: normal;
}
g.root {
  transform-origin: center;
}
</style>
