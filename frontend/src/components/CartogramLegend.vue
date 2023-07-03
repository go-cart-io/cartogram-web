<script setup lang="ts">
import type CartMap from '@/lib/cartMap'
import type { MapVersion } from '@/lib/mapVersion'
import * as d3 from 'd3'
import { nextTick, onMounted, reactive, watch } from 'vue'

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
  () => props.affineScale,
  (type, prevType) => {
    formatLegendValue()
  },
  { deep: true }
)

onMounted(() => {
  const resizeObserver = new ResizeObserver(function () {
    const actual_size = document.getElementById(props.mapID + '-svg')!.getBoundingClientRect()
    state.actualWidth =
      actual_size.width || document.getElementById(props.mapID + '-svg')!.offsetWidth
    state.actualHeight =
      actual_size.height || document.getElementById(props.mapID + '-svg')!.offsetHeight

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
    drawLegend(null, true)
  }

  drawGridLines()
}

/**
 * The following returns the scaling factors (x and y) of map of specified version.
 * @param {string} sysname The sysname of the map version
 * @returns {number[]} The total polygon area of the specified map version
 */
function getVersionPolygonScale(): [number, number] {
  var scale_x: number, scale_y: number
  if (state.actualWidth === 0 || state.actualHeight === 0) return [1, 1]

  if (props.map.max_width > props.map.max_height) {
    scale_x = scale_y = state.actualWidth / props.map.max_width
  } else {
    scale_x = scale_y = state.actualHeight / props.map.max_height
  }

  return [scale_x, scale_y]
}

/**
 * Calculates legend information of the map version
 */
function getLegendData() {
  // Obtain the scaling factors, area and total value for this map version.
  const [scaleX, scaleY] = getVersionPolygonScale()
  const valuePerPixel = versionTotalValue / (versionArea * scaleX * scaleY)
  // Each square to be in the whereabouts of 1% of versionTotalValue.
  let valuePerSquare = versionTotalValue / 100

  let baseWidth = Math.sqrt(valuePerSquare / valuePerPixel)
  // If width is too small, we increment the percentage.
  while (baseWidth < 20) {
    valuePerSquare *= 2
    baseWidth = Math.sqrt(valuePerSquare / valuePerPixel)
  }
  let width = [baseWidth, baseWidth, baseWidth] as Array<number>

  // Declare and assign variables for valuePerSquare's power of 10 and "nice number".
  let scalePowerOf10 = Math.floor(Math.log10(valuePerSquare))
  let scaleNiceNumber = [99, 99, 99]

  // We find the "nice number" that is closest to valuePerSquare's
  const valueFirstNumber = valuePerSquare / Math.pow(10, scalePowerOf10)
  let valueDiff = Math.abs(valueFirstNumber - scaleNiceNumber[0])
  const niceNumbers = [1, 2, 5, 10]
  niceNumbers.forEach(function (n) {
    if (Math.abs(valueFirstNumber - n) < valueDiff) {
      valueDiff = Math.abs(valueFirstNumber - n)
      scaleNiceNumber[0] = n
    }
  })
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
  if (props.isLegendResizable) {
    for (let i = 0; i <= numGridOptions; i++) {
      state.gridData[i] = { width: width[i], scaleNiceNumber: scaleNiceNumber[i] }
    }
    state.gridDataKeys = [2, 1, 0]
  } else {
    state.gridData = {}
    state.gridData[state.currentGridIndex] = {
      width: width[state.currentGridIndex],
      scaleNiceNumber: scaleNiceNumber[state.currentGridIndex]
    }
    state.gridDataKeys = [state.currentGridIndex]
  }
  state.scalePowerOf10 = scalePowerOf10
  state.versionTotalValue = versionTotalValue
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

  formatLegendValue()

  const totalScalePowerOfTen = Math.floor(Math.log10(versionTotalValue))
  const totalNiceNumber = versionTotalValue / Math.pow(10, totalScalePowerOfTen)
  state.legendTotal = formatLegendText(totalNiceNumber, totalScalePowerOfTen)

  // Verify if legend is accurate
  //verifyLegend(sysname, width, scaleNiceNumber * Math.pow(10, scalePowerOf10))
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

  // Event for when a different legend size is selected.
  const changeTo = (key: number) => {
    state.currentGridIndex = key
    for (let i = 0; i <= numGridOptions; i++) {
      if (i <= key) d3.select('#' + props.mapID + '-legend' + i + ' rect').attr('fill', '#EEEEEE')
      else d3.select('#' + props.mapID + '-legend' + i + ' rect').attr('fill', '#D6D6D6')
    }
    formatLegendValue()
    updateGridLines(state.gridData[key].width)
  }

  // Adjust width of square according to chosen nice number and add transition to Legends
  for (let i = 0; i <= numGridOptions; i++) {
    d3.select('#' + props.mapID + '-legend' + i + ' rect')
      .attr('width', state.gridData[i]['width'])
      .attr('height', state.gridData[i]['width'])
      .on('click', () => changeTo(i))
  }
  changeTo(state.currentGridIndex)

  const totalScalePowerOfTen = Math.floor(Math.log10(versionTotalValue))
  const totalNiceNumber = versionTotalValue / Math.pow(10, totalScalePowerOfTen)
  state.legendTotal = formatLegendText(totalNiceNumber, totalScalePowerOfTen)

  // Verify if legend is accurate
  //verifyLegend(sysname, wi* Math.pow(10, scalePowerOf10))
}

function formatLegendValue() {
  let value = state.gridData[state.currentGridIndex].scaleNiceNumber
  console.log(props.affineScale)
  value = value / (props.affineScale[0] * props.affineScale[1])

  state.legendUnit = formatLegendText(value, state.scalePowerOf10, props.isLegendResizable)
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

/**
 * Determines if the computed legend area and value is correct
 * @param sysname
 * @param width
 * @param value
 */
function verifyLegend(sysname: string, squareWidth: number, valuePerSquare: number) {
  const [scaleX, scaleY] = getVersionPolygonScale()
  // const tolerance = 0.001
  // const legendTotalValue =
  //   (valuePerSquare * (versionArea * scaleX * scaleY)) / (squareWidth * squareWidth)
  // if (!(Math.abs(versionTotalValue - legendTotalValue) < tolerance)) {
  //   console.warn(
  //     `The legend value (${valuePerSquare}) and width (${squareWidth}px) for ${sysname} is not correct. Calculating the total value from the legend yields ${legendTotalValue}, but it should be ${versionTotalValue}`
  //   )
  // } else {
  //   console.log(
  //     `The legend value (${valuePerSquare}) and width (${squareWidth}px) for ${sysname} is correct (calculated total value=${legendTotalValue}, actual total value=${versionTotalValue})`
  //   )
  // }
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
