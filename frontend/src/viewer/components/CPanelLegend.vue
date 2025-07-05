<script setup lang="ts">
/**
 * Legend wrapper for map with functions for managing grid size.
 */

import { onMounted, nextTick, reactive, ref, watch } from 'vue'
import * as d3 from 'd3'

import { useLegend } from '../composables/useLegend'

import * as config from '../../common/config'
import * as visualization from '../../common/visualization'
import * as animate from '../lib/animate'
import * as util from '../lib/util'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG
const DEFAULT_OPACITY = 0.3

const legendSvgEl = ref()
let visEl: any
let offscreenEl: any
let visView: any
let handlePointerId = -1
let handlePointerPosition = 0

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
  handlePosition: 0 as number,
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
    highlight(id)
  }
)

watch(
  () => store.options.numberOfPanels,
  () => {
    resizeViewWidth()
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

  animate.transition(visEl, offscreenEl, finalize)
}

async function resizeViewWidth() {
  await visView.resize()
  await visView.width(visView.container().offsetWidth).runAsync()
  update()
}

async function update() {
  if (!state.version) return

  legend.updateGridData()
  await nextTick()
  changeTo(state.currentGridIndex)
  drawGridLines()
}

function getCurrentScale() {
  return (
    legend.stateGridData.value[state.currentGridIndex]?.scaleNiceNumber /
    (props.affineScale[0] * props.affineScale[1])
  )
}

async function changeTo(key: number) {
  state.currentGridIndex = key
  await nextTick()
  legend.updateLegendValue(state.currentGridIndex, props.affineScale)
  updateGridLines(legend.stateGridData.value[key]?.width)
}

function onHandleDown(event: PointerEvent) {
  if (!event.isPrimary) return
  legendSvgEl.value.setPointerCapture(event.pointerId)
  handlePointerId = event.pointerId
  state.handlePosition = event.offsetX
}

function onHandleMove(event: PointerEvent) {
  if (handlePointerId !== event.pointerId) return

  const direction = event.pageX - handlePointerPosition
  const pos = state.handlePosition + direction
  state.handlePosition = Math.max(
    0,
    Math.min(pos, legend.stateGridData.value[config.NUM_GRID_OPTIONS].width)
  )
  handlePointerPosition = event.pageX
}

function onHandleUp(event: any) {
  if (handlePointerId !== event.pointerId) return
  legendSvgEl.value.releasePointerCapture(event.pointerId)
  handlePointerId = -1

  let key = 0
  let minDiff = Number.MAX_VALUE
  for (let i = 0; i <= config.NUM_GRID_OPTIONS; i++) {
    const diff = Math.abs(state.handlePosition - legend.stateGridData.value[i]['width'])
    if (diff < minDiff) {
      minDiff = diff
      key = i
    }
  }
  changeTo(key)
  emit('gridChanged')
}

function drawGridLines() {
  if (!legend.stateGridData.value[config.NUM_GRID_OPTIONS]) return
  const gridWidth = legend.stateGridData.value[state.currentGridIndex]['width'] || 20
  updateGridLines(gridWidth)
}

function updateGridLines(gridWidth: number) {
  if (isNaN(gridWidth)) return
  const stroke_opacity = store.options.showGrid ? DEFAULT_OPACITY : 0
  const gridPattern = d3.select('#' + props.panelID + '-grid')
  gridPattern
    .select('path')
    .attr('stroke-opacity', stroke_opacity)
    .attr('d', 'M ' + gridWidth * 5 + ' 0 L 0 0 0 ' + gridWidth * 5) // *5 for pretty transition when resize grid
  if (gridPattern.attr('width')) {
    // To prevent transition from 0
    gridPattern
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('width', gridWidth)
      .attr('height', gridWidth)
  } else {
    gridPattern.attr('width', gridWidth).attr('height', gridWidth)
  }
  state.handlePosition = gridWidth
}

function highlight(itemID: any) {
  visView?.signal('active', itemID).runAsync()
}
</script>

<template>
  <div class="d-flex flex-column card-body p-0">
    <div class="d-flex position-absolute z-1">
      <svg
        v-if="legend.stateGridData.value[config.NUM_GRID_OPTIONS]"
        ref="legendSvgEl"
        class="d-flex position-absolute z-2"
        style="cursor: pointer; top: -15px; touch-action: none"
        height="30px"
        stroke="#AAAAAA"
        stroke-width="2px"
        v-bind:id="props.panelID + '-slider'"
        v-bind:width="legend.stateGridData.value[config.NUM_GRID_OPTIONS].width + 15"
        v-on:pointerdown.stop.prevent="onHandleDown"
        v-on:pointermove.stop.prevent="onHandleMove"
        v-on:pointerup.stop.prevent="onHandleUp"
      >
        <line
          x1="0"
          y1="15"
          v-bind:x2="legend.stateGridData.value[config.NUM_GRID_OPTIONS].width"
          y2="15"
        ></line>
        <line
          v-for="(grid, index) in legend.stateGridData.value"
          v-bind:x1="grid.width"
          y1="8"
          v-bind:x2="grid.width"
          y2="16"
          v-bind:key="index"
        ></line>
        <circle id="handle" r="5" v-bind:cx="state.handlePosition" cy="15" stroke-width="0px" />
      </svg>
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
            <path fill="none" stroke="#5A5A5A" stroke-width="2" stroke-opacity="0.3"></path>
          </pattern>
        </defs>
        <rect
          v-if="store.options.showGrid"
          width="100%"
          height="100%"
          v-bind:fill="'url(#' + props.panelID + '-grid)'"
        ></rect>
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
