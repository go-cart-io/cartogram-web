<script setup lang="ts">
import * as d3 from 'd3'
import { nextTick, onMounted, reactive, watch } from 'vue'
import type CartMap from '@/lib/cartMap'
import * as util from '../lib/util'

var numGridOptions = 3
var versionArea: number
var versionTotalValue: number
const locale =
  navigator.languages && navigator.languages.length ? navigator.languages[0] : navigator.language
var defaultOpacity = 0.3

const props = withDefaults(
  defineProps<{
    mapID: string
    map: CartMap
    sysname: string
    affineScale?: any
    isGridVisible?: boolean
    isLegendResizable?: boolean
  }>(),
  {
    isGridVisible: false,
    isLegendResizable: false,
    affineScale: [1, 1]
  }
)

const state = reactive({
  actualWidth: 100 as number,
  actualHeight: 100 as number,
  unit: 'km sq.' as string,
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
  isDragingHandle: false as boolean,
  handlePosition: 0 as number,
  scalePowerOf10: 1 as number,
  versionTotalValue: 1 as number
})

watch(
  () => props.isLegendResizable,
  (type, prevType) => {
    update()
  }
)

watch(
  () => props.sysname,
  (type, prevType) => {
    update()
  }
)

watch(
  () => props.map.name,
  (type, prevType) => {
    update()
  },
  { deep: true }
)

watch(
  () => props.affineScale,
  (type, prevType) => {
    formatLegendValue()
  },
  { deep: true }
)

defineExpose({
  getCurrentScale,
  updateGridIndex
})

onMounted(() => {
  const resizeObserver = new ResizeObserver(function () {
    const element = document.getElementById(props.mapID + '-svg')! as HTMLElement
    if (!element) return
    const actual_size = element.getBoundingClientRect()
    state.actualWidth = actual_size.width || element.offsetWidth
    state.actualHeight = actual_size.height || element.offsetHeight

    update()
  })
  resizeObserver.observe(document.getElementById(props.mapID + '-svg')!)
})

async function update() {
  if (!props.map) return
  state.unit = Object.values(props.map.regions)[0].getVersion(props.sysname).unit
  versionArea = props.map.versions[props.sysname].legendData.versionOriginalArea || 0
  versionTotalValue = props.map.versions[props.sysname].legendData.versionTotalValue || 0

  getLegendData()
  await nextTick()
  changeTo(state.currentGridIndex)
  const totalScalePowerOfTen = Math.floor(Math.log10(versionTotalValue))
  const totalNiceNumber = versionTotalValue / Math.pow(10, totalScalePowerOfTen)
  state.legendTotal = formatLegendText(totalNiceNumber, totalScalePowerOfTen)

  drawGridLines()
}

/**
 * The following returns the scaling factors (x and y) of map of specified version.
 * @param {string} sysname The sysname of the map version
 * @returns {number[]} The total polygon area of the specified map version
 */
function getVersionPolygonScale(): number {
  var scale_x: number, scale_y: number
  if (state.actualWidth === 0 || state.actualHeight === 0) return 1

  scale_x = state.actualWidth / props.map.max_width
  scale_y = state.actualHeight / props.map.max_height

  return Math.min(scale_x, scale_y) // viewBox maintains the ratio, thus scale using min factor
}

/**
 * Calculates legend information of the map version
 */
function getLegendData() {
  // Obtain the scaling factors, area and total value for this map version.
  const scale = getVersionPolygonScale()
  const valuePerPixel = versionTotalValue / (versionArea * scale * scale)
  // Each square to be in the whereabouts of 1% of versionTotalValue.
  let valuePerSquare = versionTotalValue / 100
  let baseWidth = Math.sqrt(valuePerSquare / valuePerPixel)
  // If width is too small, we increment the percentage.
  while (baseWidth < 20) {
    valuePerSquare *= 2
    baseWidth = Math.sqrt(valuePerSquare / valuePerPixel)
  }
  let width = [] as Array<number>
  let [scaleNiceNumber0, scalePowerOf10] = util.findNearestNiceNumber(valuePerSquare)
  let niceIndex = util.NICE_NUMBERS.indexOf(scaleNiceNumber0)
  let beginIndex = niceIndex === 0 ? niceIndex : niceIndex - 1
  let endIndex = beginIndex + numGridOptions + 1
  while (endIndex >= util.NICE_NUMBERS.length && beginIndex > 0) {
    endIndex--
    beginIndex--
  }
  let scaleNiceNumber = util.NICE_NUMBERS.slice(beginIndex, endIndex)

  for (let i = 0; i <= numGridOptions; i++) {
    width[i] =
      baseWidth * Math.sqrt((scaleNiceNumber[i] * Math.pow(10, scalePowerOf10)) / valuePerSquare)
  }

  // Store legend Information
  for (let i = 0; i <= numGridOptions; i++) {
    state.gridData[i] = {
      width: width[i],
      scaleNiceNumber: scaleNiceNumber[i]
    }
  }

  if (props.isLegendResizable) {
    state.gridDataKeys = [3, 2, 1, 0]
  } else {
    state.gridDataKeys = [state.currentGridIndex]
  }
  state.scalePowerOf10 = scalePowerOf10
  state.versionTotalValue = versionTotalValue
}

function getCurrentScale() {
  return (
    state.gridData[state.currentGridIndex].scaleNiceNumber /
    (props.affineScale[0] * props.affineScale[1])
  )
}

function changeTo(key: number) {
  state.currentGridIndex = key
  if (!props.isLegendResizable) state.gridDataKeys = [state.currentGridIndex]

  for (let i = 0; i <= numGridOptions; i++) {
    if (i <= key) d3.select('#' + props.mapID + '-legend' + i + ' rect').attr('fill', '#EEEEEE')
    else d3.select('#' + props.mapID + '-legend' + i + ' rect').attr('fill', '#D6D6D6')
  }
  formatLegendValue()
  updateGridLines(state.gridData[key].width)
}

function handleMove(event: any) {
  if (state.isDragingHandle) state.handlePosition = event.offsetX
}

function resizeGrid(event: any) {
  var key = 0
  var minDiff = Number.MAX_VALUE
  for (let i = 0; i <= numGridOptions; i++) {
    var diff = Math.abs(state.handlePosition - state.gridData[i]['width'])
    if (diff < minDiff) {
      minDiff = diff
      key = i
    }
  }
  changeTo(key)
  state.isDragingHandle = false
}

function formatLegendValue() {
  let value = state.gridData[state.currentGridIndex].scaleNiceNumber
  value = value / (props.affineScale[0] * props.affineScale[1])

  state.legendUnit = formatLegendText(value, state.scalePowerOf10)
}

function formatLegendText(value: number, scalePowerOf10: number) {
  let originalValue = value * Math.pow(10, scalePowerOf10)
  const formatter = Intl.NumberFormat(locale, {
    notation: 'compact',
    compactDisplay: 'short'
  })

  let formated = ''
  formated += formatter.format(originalValue)

  return formated
}

function drawGridLines() {
  const gridWidth = state.gridData[state.currentGridIndex]['width'] || 20
  updateGridLines(gridWidth)
}

function updateGridLines(gridWidth: number) {
  let stroke_opacity = props.isGridVisible ? defaultOpacity : 0
  const gridPattern = d3.select('#' + props.mapID + '-grid')
  gridPattern.attr('width', gridWidth).attr('height', gridWidth)
  gridPattern
    .select('path')
    .attr('stroke-opacity', stroke_opacity)
    .attr('d', 'M ' + gridWidth * 5 + ' 0 L 0 0 0 ' + gridWidth * 5) // *5 for pretty transition when resize grid

  state.handlePosition = gridWidth
}

function updateGridIndex(change: number) {
  var newIndex = state.currentGridIndex + change
  if (newIndex < 0 || newIndex > numGridOptions) return
  changeTo(newIndex)
}
</script>

<template>
  <div class="d-flex">
    <!--svg
      v-if="state.gridData[numGridOptions]"
      v-bind:id="props.mapID + '-legend'"
      style="cursor: pointer"
      v-bind:width="
        props.isLegendResizable
          ? state.gridData[numGridOptions].width + 2
          : state.gridData[state.currentGridIndex].width + 2
      "
      v-bind:height="
        props.isLegendResizable
          ? state.gridData[numGridOptions].width + 2
          : state.gridData[state.currentGridIndex].width + 2
      "
    >
      <g v-for="key in state.gridDataKeys" v-bind:id="props.mapID + '-legend' + key">
        <rect
          x="1"
          y="1"
          fill="#EEEEEE"
          stroke="#AAAAAA"
          stroke-width="2px"
          v-bind:width="state.gridData[key].width"
          v-bind:height="state.gridData[key].width"
          v-on:click="changeTo(key)"
        ></rect>
      </g>
    </svg-->
    <svg
      v-if="state.gridData[numGridOptions]"
      v-bind:id="props.mapID + '-legend'"
      v-bind:width="state.gridData[numGridOptions].width + 15"
      height="30px"
      style="cursor: pointer"
      stroke="#AAAAAA"
      stroke-width="2px"
      v-on:pointerdown="state.isDragingHandle = true"
      v-on:pointermove="handleMove"
      v-on:pointerup="resizeGrid"
      v-on:pointerleave="resizeGrid"
    >
      <line x1="0" y1="15" v-bind:x2="state.gridData[numGridOptions].width" y2="15"></line>
      <line
        v-for="grid in state.gridData"
        v-bind:x1="grid.width"
        y1="10"
        v-bind:x2="grid.width"
        y2="20"
      ></line>
      <line x1="1" y1="10" x2="1" y2="20" stroke="#000000"></line>
      <line
        x1="0"
        y1="15"
        v-bind:x2="state.gridData[state.currentGridIndex].width"
        y2="15"
        stroke="#000000"
      ></line>
      <circle id="handle" r="5" v-bind:cx="state.handlePosition" cy="15" stroke-width="0px" />
    </svg>
    <div v-bind:id="props.mapID + '-legend-num'" class="flex-fill p-1">
      <span v-html="state.legendUnit"></span>, Total: <span v-html="state.legendTotal"></span>
      {{ state.unit }}
    </div>
  </div>

  <div v-bind:id="props.mapID" class="flex-fill" data-grid-visibility="off">
    <slot></slot>
    <svg width="100%" height="100%" v-bind:id="props.mapID + '-grid-area'">
      <defs>
        <pattern v-bind:id="props.mapID + '-grid'" patternUnits="userSpaceOnUse">
          <path fill="none" stroke="#5A5A5A" stroke-width="2" stroke-opacity="0.3"></path>
        </pattern>
      </defs>
      <rect
        v-if="props.isGridVisible"
        width="100%"
        height="100%"
        v-bind:fill="'url(#' + props.mapID + '-grid)'"
      ></rect>
    </svg>
  </div>

  <div class="d-flex">
    <label v-bind:for="props.mapID + '-grid-range'" class="form-label">GridSize:</label>
    <input
      type="range"
      class="form-range ps-2"
      v-bind:id="props.mapID + '-grid-range'"
      min="0"
      v-bind:max="numGridOptions"
      step="1"
      v-model="state.currentGridIndex"
      v-on:change="changeTo(state.currentGridIndex)"
    />
  </div>
</template>

<style scoped></style>
