<script setup lang="ts">
/**
 * Legend wrapper for map with functions for managing grid size.
 */

import { onMounted, nextTick, reactive, ref, watch, inject } from 'vue'
import * as d3 from 'd3'
import embed, { type VisualizationSpec } from 'vega-embed'

import * as config from '../../common/config'

import * as util from '../lib/util'

import spec from '../../assets/template.vg.json' with { type: 'json' }

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const NUM_GRID_OPTIONS = 3
const LOCALE =
  navigator.languages && navigator.languages.length ? navigator.languages[0] : navigator.language
const DEFAULT_OPACITY = 0.3
const COLOR_SCHEME = inject('colorScheme')

const versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
const legendSvgEl = ref()
let visEl: any
let offscreenEl: any
let visView: any
let totalArea: number
let totalValue: number
let handlePointerId = -1
let handlePointerPosition = 0

const props = withDefaults(
  defineProps<{
    panelID: string
    mapDBKey: string
    versionKey: string
    affineScale?: any
  }>(),
  {
    affineScale: [1, 1]
  }
)

const state = reactive({
  version: store.versions[props.versionKey],
  legendUnit: '' as string,
  legendTotal: '' as string,

  currentGridIndex: 1 as number,
  gridDataKeys: [1],
  gridData: {} as {
    [key: number]: {
      width: number
      scaleNiceNumber: number
    }
  },
  handlePosition: 0 as number,
  scalePowerOf10: 1 as number
})

defineExpose({
  getCurrentScale
})

const emit = defineEmits(['gridChanged', 'versionUpdated'])

watch(
  () => props.versionKey,
  () => {
    state.version = store.versions[props.versionKey]
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
  () => props.affineScale,
  () => {
    formatLegendValue()
  },
  { deep: true }
)

onMounted(async () => {
  if (!state.version) return

  versionSpec.signals[3]['value'] =
    !COLOR_SCHEME || COLOR_SCHEME === 'custom' ? 'pastel1' : COLOR_SCHEME
  versionSpec.data[0].url = util.getGeojsonURL(store.currentMapName, props.mapDBKey, 'data.csv')
  versionSpec.data[1].url = util.getGeojsonURL(
    store.currentMapName,
    props.mapDBKey,
    state.version.name + '.json'
  )

  // if (store.currentMapName === "world" && state.version.name === 'Geographic Area') {
  //   // Gall–Peters projection
  //   vega.projection('cylindricalEqualArea', geoCylindricalEqualArea)
  //   versionSpec.projections[0].type = "cylindricalEqualArea"
  //   versionSpec.projections[0].reflectY = false
  //   versionSpec.projections[0].parallel = 45
  // }

  visEl = d3.select('#' + props.panelID + '-vis')
  offscreenEl = d3.select('#' + props.panelID + '-offscreen')
  const container = await embed('#' + props.panelID + '-vis', <VisualizationSpec>versionSpec, {
    renderer: 'svg',
    actions: false,
    tooltip: config.tooltipOptions
  })
  visView = container.view

  const [area, sum] = util.getTotalAreasAndValuesForVersion(
    state.version.header,
    visView.data('geo_1'),
    visView.data('source_csv')
  )
  totalArea = area
  totalValue = sum

  visView.addResizeListener(function () {
    totalArea = util.getTotalAreas(visView.data('geo_1'))
    update()
  })

  visView.addSignalListener('active', function (name: string, value: any) {
    store.highlightedRegionID = value
  })

  visView.addEventListener('pointerup', function (event: any, item: any) {
    const value = item?.datum.cartogram_data
    visView.tooltip()(visView, event, item, value)
  })

  update()
})

async function switchVersion() {
  versionSpec.data[1].url = util.getGeojsonURL(
    store.currentMapName,
    props.mapDBKey,
    state.version.name + '.json'
  )

  let transitions = 0
  const container = await embed(
    '#' + props.panelID + '-offscreen',
    <VisualizationSpec>versionSpec,
    { renderer: 'svg', actions: false, tooltip: config.tooltipOptions }
  )
  const [area, sum] = util.getTotalAreasAndValuesForVersion(
    state.version.header,
    container.view.data('geo_1'),
    container.view.data('source_csv')
  )
  totalArea = area
  totalValue = sum
  update()

  function finalize() {
    container.view.runAfter(() => emit('versionUpdated'))
    container.view.initialize('#' + props.panelID + '-vis').runAsync()
    visView = container.view
  }

  visEl.selectAll('path[aria-roledescription="geoshape"]').each(function (this: any) {
    const geoID = d3.select(this).attr('aria-label')
    const labelID = geoID.replace('geoshape', 'geolabel')

    const newD = offscreenEl.select('path[aria-label="' + geoID + '"]').attr('d')
    d3.select(this)
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('d', newD)
      .on('start', function () {
        transitions++
      })
      .on('end', function () {
        if (--transitions === 0) finalize()
      })

    if (!labelID || labelID === 'dividers') return
    const labelEl = offscreenEl.select('text[aria-label="' + labelID + '"]')
    const newLabelPos = labelEl.attr('transform')
    const newLabelOpacity = labelEl.attr('opacity')
    const newLabelSize = labelEl.attr('font-size')
    visEl
      .select('text[aria-label="' + labelID + '"]')
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('transform', newLabelPos)
      .attr('opacity', newLabelOpacity)
      .attr('font-size', newLabelSize)
      .on('start', function () {
        transitions++
      })
      .on('end', function () {
        if (--transitions === 0) finalize()
      })
  })
}

async function resizeViewWidth() {
  await visView.resize()
  await visView.width(visView.container().offsetWidth).runAsync()
  update()
}

async function update() {
  if (!state.version) return

  getLegendData()
  await nextTick()
  changeTo(state.currentGridIndex)
  const totalScalePowerOfTen = Math.floor(Math.log10(totalValue))
  const totalNiceNumber = totalValue / Math.pow(10, totalScalePowerOfTen)
  state.legendTotal = formatLegendText(totalNiceNumber, totalScalePowerOfTen)
  drawGridLines()
}

/**
 * Calculates legend information of the map version
 */
function getLegendData() {
  if (totalValue === 0 || totalArea === 0) return

  const valuePerPixel = totalValue / totalArea
  // Each square to be in the whereabouts of 1% of totalValue.
  let valuePerSquare = totalValue / 100
  let baseWidth = Math.sqrt(valuePerSquare / valuePerPixel)
  // If width is too small, we increment the percentage.
  while (baseWidth < 20) {
    valuePerSquare *= 2
    baseWidth = Math.sqrt(valuePerSquare / valuePerPixel)
  }
  const width = [] as Array<number>
  const [scaleNiceNumber0, scalePowerOf10] = util.findNearestNiceNumber(valuePerSquare)
  const niceIndex = util.NICE_NUMBERS.indexOf(scaleNiceNumber0)
  let beginIndex = niceIndex === 0 ? niceIndex : niceIndex - 1
  let endIndex = beginIndex + NUM_GRID_OPTIONS + 1
  while (endIndex >= util.NICE_NUMBERS.length && beginIndex > 0) {
    endIndex--
    beginIndex--
  }
  const scaleNiceNumber = util.NICE_NUMBERS.slice(beginIndex, endIndex)
  for (let i = 0; i <= NUM_GRID_OPTIONS; i++) {
    width[i] =
      baseWidth * Math.sqrt((scaleNiceNumber[i] * Math.pow(10, scalePowerOf10)) / valuePerSquare)
  }
  // Store legend Information
  for (let i = 0; i <= NUM_GRID_OPTIONS; i++) {
    state.gridData[i] = {
      width: width[i],
      scaleNiceNumber: scaleNiceNumber[i]
    }
  }

  state.gridDataKeys = [state.currentGridIndex]
  state.scalePowerOf10 = scalePowerOf10
}

function getCurrentScale() {
  return (
    state.gridData[state.currentGridIndex]?.scaleNiceNumber /
    (props.affineScale[0] * props.affineScale[1])
  )
}

async function changeTo(key: number) {
  state.currentGridIndex = key
  state.gridDataKeys = [state.currentGridIndex]
  await nextTick()

  for (let i = 0; i <= NUM_GRID_OPTIONS; i++) {
    if (i <= key) {
      d3.select('#' + props.panelID + '-legend' + i + ' rect').attr('fill', '#EEEEEE')
    } else d3.select('#' + props.panelID + '-legend' + i + ' rect').attr('fill', '#D6D6D6')
  }
  formatLegendValue()
  updateGridLines(state.gridData[key]?.width)
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
  state.handlePosition = Math.max(0, Math.min(pos, state.gridData[NUM_GRID_OPTIONS].width))
  handlePointerPosition = event.pageX
}

function onHandleUp(event: any) {
  if (handlePointerId !== event.pointerId) return
  legendSvgEl.value.releasePointerCapture(event.pointerId)
  handlePointerId = -1

  let key = 0
  let minDiff = Number.MAX_VALUE
  for (let i = 0; i <= NUM_GRID_OPTIONS; i++) {
    const diff = Math.abs(state.handlePosition - state.gridData[i]['width'])
    if (diff < minDiff) {
      minDiff = diff
      key = i
    }
  }
  changeTo(key)
  emit('gridChanged')
}

function formatLegendValue() {
  if (!state.gridData[NUM_GRID_OPTIONS]) return

  let value = state.gridData[state.currentGridIndex].scaleNiceNumber
  value = value / (props.affineScale[0] * props.affineScale[1])
  state.legendUnit = formatLegendText(value, state.scalePowerOf10)
}

function formatLegendText(value: number, scalePowerOf10: number): string {
  const originalValue = value * Math.pow(10, scalePowerOf10)
  const formatter = Intl.NumberFormat(LOCALE, {
    notation: 'compact',
    compactDisplay: 'short'
  })
  let formated = ''
  formated += formatter.format(originalValue)
  return formated
}

function drawGridLines() {
  if (!state.gridData[NUM_GRID_OPTIONS]) return
  const gridWidth = state.gridData[state.currentGridIndex]['width'] || 20
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
        v-if="state.gridData[NUM_GRID_OPTIONS]"
        ref="legendSvgEl"
        class="d-flex position-absolute z-2"
        style="cursor: pointer; top: -15px; touch-action: none"
        height="30px"
        stroke="#AAAAAA"
        stroke-width="2px"
        v-bind:id="props.panelID + '-slider'"
        v-bind:width="state.gridData[NUM_GRID_OPTIONS].width + 15"
        v-on:pointerdown.stop.prevent="onHandleDown"
        v-on:pointermove.stop.prevent="onHandleMove"
        v-on:pointerup.stop.prevent="onHandleUp"
      >
        <line x1="0" y1="15" v-bind:x2="state.gridData[NUM_GRID_OPTIONS].width" y2="15"></line>
        <line
          v-for="(grid, index) in state.gridData"
          v-bind:x1="grid.width"
          y1="8"
          v-bind:x2="grid.width"
          y2="16"
          v-bind:key="index"
        ></line>
        <circle id="handle" r="5" v-bind:cx="state.handlePosition" cy="15" stroke-width="0px" />
      </svg>
      <svg
        v-if="state.gridData[NUM_GRID_OPTIONS]"
        v-bind:id="props.panelID + '-legend'"
        style="cursor: pointer; opacity: 0.5"
        v-bind:width="state.gridData[state.currentGridIndex].width + 2"
        v-bind:height="state.gridData[state.currentGridIndex].width + 2"
      >
        <g
          v-for="key in state.gridDataKeys"
          v-bind:id="props.panelID + '-legend' + key"
          stroke-width="2px"
          fill="#EEEEEE"
          stroke="#AAAAAA"
          v-bind:key="key"
        >
          <rect
            x="1"
            y="1"
            v-bind:width="state.gridData[key].width"
            v-bind:height="state.gridData[key].width"
          ></rect>
        </g>
      </svg>
      <div v-bind:id="props.panelID + '-legend-num'" class="flex-fill p-1">
        <span v-html="state.legendUnit"></span>
        {{ state.version?.unit }}
        <div>Total: <span v-html="state.legendTotal"></span></div>
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
</style>
