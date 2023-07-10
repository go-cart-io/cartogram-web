<script setup lang="ts">
import * as d3 from 'd3'
import { nextTick, onMounted, reactive, watch } from 'vue'
import type CartMap from '@/lib/cartMap'
import * as util from '../lib/util'

var numGridOptions = 2
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
  if (props.isLegendResizable) {
    drawResizableLegend()
  } else {
    drawLegend()
  }
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
  let width = [baseWidth, baseWidth, baseWidth] as Array<number>

  let [scaleNiceNumber0, scalePowerOf10] = util.findNearestNiceNumber(valuePerSquare)
  let scaleNiceNumber = [scaleNiceNumber0] as Array<number>

  if (scaleNiceNumber[0] == 1) {
    scaleNiceNumber[1] = 2
    scaleNiceNumber[2] = 5
  } else if (scaleNiceNumber[0] == 2) {
    scaleNiceNumber[1] = 5
    scaleNiceNumber[2] = 10
  } else if (scaleNiceNumber[0] == 5) {
    scaleNiceNumber[1] = 10
    scaleNiceNumber[2] = 20
  } else {
    scaleNiceNumber[0] = 1
    scaleNiceNumber[1] = 2
    scaleNiceNumber[2] = 5
    scalePowerOf10 += 1
  }
  for (let i = 0; i <= numGridOptions; i++) {
    width[i] *= Math.sqrt((scaleNiceNumber[i] * Math.pow(10, scalePowerOf10)) / valuePerSquare)
  }

  // Store legend Information
  for (let i = 0; i <= numGridOptions; i++) {
    state.gridData[i] = {
      width: width[i],
      scaleNiceNumber: scaleNiceNumber[i]
    }
  }

  if (props.isLegendResizable) {
    state.gridDataKeys = [2, 1, 0]
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

/**
 * The following draws the static legend for each map
 * @param {string} old_sysname The previous sysname after map version switch. Optional.
 * @param {boolean} change_map True if the map is displayed for the first egendData['time or the map is changed. Optional.
 */
function drawLegend() {
  // Retrive legend information
  const width = state.gridData[state.currentGridIndex]['width'] || 0
  const scaleNiceNumber = state.gridData[state.currentGridIndex]['scaleNiceNumber'] || 0
  const scalePowerOf10 = state.scalePowerOf10 || 0

  const legendSVG = d3
    .select('#' + props.mapID + '-legend')
    .attr('width', width! + 2)
    .attr('height', width! + 2)
  const legendSquare = d3
    .select('#' + props.mapID + '-legend' + state.currentGridIndex + ' rect')
    .attr('width', width)
    .attr('height', width)
    .attr('fill', '#EEEEEE')
}

/**
 * The following draws the resizable legend for each map
 * @param {string} sysname The sysname of the map version
 * @param {string} old_sysname The previous sysname after map version switch. Optional.
 */
function drawResizableLegend() {
  const legendSVG = d3
    .select('#' + props.mapID + '-legend')
    .attr('width', state.gridData[numGridOptions].width + 2)
    .attr('height', state.gridData[numGridOptions].width + 2)

  // Adjust width of square according to chosen nice number and add transition to Legends
  for (let i = 0; i <= numGridOptions; i++) {
    d3.select('#' + props.mapID + '-legend' + i + ' rect')
      .attr('width', state.gridData[i]['width'])
      .attr('height', state.gridData[i]['width'])
      .on('click', () => changeTo(i))
  }
}

function changeTo(key: number) {
  state.currentGridIndex = key
  for (let i = 0; i <= numGridOptions; i++) {
    if (i <= key) d3.select('#' + props.mapID + '-legend' + i + ' rect').attr('fill', '#EEEEEE')
    else d3.select('#' + props.mapID + '-legend' + i + ' rect').attr('fill', '#D6D6D6')
  }
  formatLegendValue()
  updateGridLines(state.gridData[key].width)
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
}

function updateGridIndex(change: number) {
  var newIndex = state.currentGridIndex + change
  if (newIndex < 0 || newIndex > numGridOptions) return
  state.currentGridIndex = newIndex
  changeTo(newIndex)
}
</script>

<template>
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

  <div class="position-absolute top-0 z-3 d-flex">
    <svg v-bind:id="props.mapID + '-legend'" style="cursor: pointer">
      <g v-for="key in state.gridDataKeys" v-bind:id="props.mapID + '-legend' + key">
        <rect x="1" y="1" fill="#EEEEEE" stroke="#AAAAAA" stroke-width="2px"></rect>
      </g>
    </svg>
    <div v-bind:id="props.mapID + '-legend-num'" class="flex-fill p-1">
      <span v-html="state.legendUnit"></span>, Total: <span v-html="state.legendTotal"></span>
      {{ state.unit }}
    </div>
  </div>
</template>

<style scoped></style>
