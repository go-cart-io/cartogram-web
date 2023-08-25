<script setup lang="ts">
import * as d3 from 'd3'
import { nextTick, onMounted, reactive, watch } from 'vue'
import type CartMap from '@/lib/cartMap'
import * as util from '../lib/util'
import shareState from '../lib/state'
import tracker from '../lib/tracker'

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
  }>(),
  {
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
  handlePosition: 0 as number,
  handleTouchPosition: 0 as number,
  scalePowerOf10: 1 as number,
  versionTotalValue: 1 as number
})

// watch(
//   () => props.isLegendResizable,
//   (type, prevType) => {
//     update()
//   }
// )

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

const emit = defineEmits(['gridChanged'])

onMounted(() => {
  const resizeObserver = new ResizeObserver(function () {
    const element = document.getElementById(props.mapID + '-svg')! as HTMLElement
    if (!element) return
    const actual_size = element.getBoundingClientRect()
    if (!actual_size.width || !actual_size.height) return
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

  // if (props.isLegendResizable) {
  //   state.gridDataKeys = [3, 2, 1, 0]
  // } else {
  state.gridDataKeys = [state.currentGridIndex]
  // }
  state.scalePowerOf10 = scalePowerOf10
  state.versionTotalValue = versionTotalValue
}

function getCurrentScale() {
  return (
    state.gridData[state.currentGridIndex].scaleNiceNumber /
    (props.affineScale[0] * props.affineScale[1])
  )
}

async function changeTo(key: number) {
  state.currentGridIndex = key
  // if (!props.isLegendResizable) {
  state.gridDataKeys = [state.currentGridIndex]
  await nextTick()
  // }

  for (let i = 0; i <= numGridOptions; i++) {
    if (i <= key) {
      d3.select('#' + props.mapID + '-legend' + i + ' rect').attr('fill', '#EEEEEE')
    } else d3.select('#' + props.mapID + '-legend' + i + ' rect').attr('fill', '#D6D6D6')
  }
  formatLegendValue()
  updateGridLines(state.gridData[key].width)
}

function handleMove(event: TouchEvent) {
  if (!event.target) return
  var direction = event.touches[0].pageX - state.handleTouchPosition
  var pos = state.handlePosition + direction
  state.handlePosition = Math.max(0, Math.min(pos, state.gridData[numGridOptions].width))
  state.handleTouchPosition = event.touches[0].pageX
  event.preventDefault()
}

function resizeGrid(event: any) {
  var key = 0
  var minDiff = Number.MAX_VALUE
  var pos = event.offsetX ? event.offsetX : state.handlePosition
  for (let i = 0; i <= numGridOptions; i++) {
    var diff = Math.abs(pos - state.gridData[i]['width'])
    if (diff < minDiff) {
      minDiff = diff
      key = i
    }
  }
  changeTo(key)
  emit('gridChanged')

  tracker.push('grid_changed', Math.round(state.gridData[key]['width']) + ' (' + key + ')');
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
  if (isNaN(gridWidth)) return
  let stroke_opacity = shareState.options.showGrid ? defaultOpacity : 0
  const gridPattern = d3.select('#' + props.mapID + '-grid')
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

function updateGridIndex(change: number) {
  var newIndex = state.currentGridIndex + change
  if (newIndex < 0 || newIndex > numGridOptions) return
  changeTo(newIndex)
}
</script>

<template>
  <div class="d-flex position-absolute z-1">
    <svg
      v-if="state.gridData[numGridOptions]"
      v-bind:id="props.mapID + '-legend'"
      style="cursor: pointer; opacity: 0.5"
      v-bind:width="state.gridData[state.currentGridIndex].width + 2"
      v-bind:height="state.gridData[state.currentGridIndex].width + 2"
    >
      <g
        v-for="key in state.gridDataKeys"
        v-bind:id="props.mapID + '-legend' + key"
        stroke-width="2px"
        fill="#EEEEEE"
        stroke="#AAAAAA"
      >
        <rect
          x="1"
          y="1"
          v-bind:width="state.gridData[key].width"
          v-bind:height="state.gridData[key].width"
        ></rect>
      </g>
    </svg>
    <div v-bind:id="props.mapID + '-legend-num'" class="flex-fill p-1">
      <span v-html="state.legendUnit"></span>, Total: <span v-html="state.legendTotal"></span>
      {{ state.unit }}
    </div>
  </div>

  <svg
    v-if="state.gridData[numGridOptions]"
    v-bind:id="props.mapID + '-slider'"
    v-bind:width="state.gridData[numGridOptions].width + 15"
    height="30px"
    style="cursor: pointer; top: 2px; left: 17px"
    stroke="#AAAAAA"
    stroke-width="2px"
    v-on:pointerup="resizeGrid"
    v-on:touchmove="handleMove"
    v-on:touchend="resizeGrid"
    class="d-flex position-absolute z-2"
  >
    <line x1="0" y1="15" v-bind:x2="state.gridData[numGridOptions].width" y2="15"></line>
    <line
      v-for="grid in state.gridData"
      v-bind:x1="grid.width"
      y1="10"
      v-bind:x2="grid.width"
      y2="20"
    ></line>
    <circle id="handle" r="5" v-bind:cx="state.handlePosition" cy="15" stroke-width="0px" />
  </svg>

  <div v-bind:id="props.mapID" class="flex-fill" data-grid-visibility="off">
    <slot></slot>
    <svg width="100%" height="100%" v-bind:id="props.mapID + '-grid-area'">
      <defs>
        <pattern v-bind:id="props.mapID + '-grid'" patternUnits="userSpaceOnUse">
          <path fill="none" stroke="#5A5A5A" stroke-width="2" stroke-opacity="0.3"></path>
        </pattern>
      </defs>
      <rect
        v-if="shareState.options.showGrid"
        width="100%"
        height="100%"
        v-bind:fill="'url(#' + props.mapID + '-grid)'"
      ></rect>
    </svg>
  </div>
</template>

<style scoped></style>
