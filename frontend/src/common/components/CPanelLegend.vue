<script setup lang="ts">
/**
 * Legend wrapper for map with functions for managing grid size.
 */

import * as d3 from 'd3'
import { onMounted, nextTick, reactive, watch } from 'vue'
import embed, { type VisualizationSpec } from 'vega-embed'

import * as util from '../lib/util'

import spec from '../../assets/template.vg.json' with { type: "json" }

var numGridOptions = 3
const locale =
  navigator.languages && navigator.languages.length ? navigator.languages[0] : navigator.language
var defaultOpacity = 0.3
var versionSpec = JSON.parse(JSON.stringify(spec))
var visEl: any
var offscreenEl: any
var visView: any
var totalArea: number
var totalValue: number

const props = withDefaults(
  defineProps<{
    mapID: string
    currentMapName: string
    stringKey: string
    versionKey: string
    versions: { [key: string]: any }
    showGrid?: boolean
    affineScale?: any
  }>(),
  {
    showGrid: true,
    affineScale: [1, 1]
  }
)

const state = reactive({
  version: props.versions[props.versionKey],
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
  scalePowerOf10: 1 as number
})

watch(
  () => props.versionKey,
  (type, prevType) => {
    state.version = props.versions[props.versionKey]
    switchVersion()
  }
)

watch(
  () => props.affineScale,
  (type, prevType) => {
    formatLegendValue()
  },
  { deep: true }
)

defineExpose({
  updateView: resizeViewWidth,
  getData,
  getCurrentScale,
  updateGridIndex
})

const emit = defineEmits(['gridChanged'])

onMounted(async () => {
  if (!state.version) return

  versionSpec.data[0].url = util.getGeojsonURL(props.currentMapName, props.stringKey, 'data.csv')
  versionSpec.data[1].url = util.getGeojsonURL(props.currentMapName, props.stringKey, state.version.name + '.json')
  const headers = Object.values(props.versions).map(item => item.header.replace('.', '\\.'))
  versionSpec.data[2].transform[1].values.push(...headers)

  const tooltipFormat = Object.values(props.versions).map(item => `"${item.name}": datum["${item.header}"] + " ${item.unit}"`).join(', ');
  versionSpec.marks[0].encode.update.tooltip.signal =
    '{title: datum.Region + " (" + datum.Abbreviation + ")", ' + tooltipFormat + '}'

  visEl = d3.select('#' + props.mapID + '-vis')
  offscreenEl = d3.select('#' + props.mapID + '-offscreen')
  let container = await embed('#' + props.mapID + '-vis', <VisualizationSpec> versionSpec, { renderer: 'svg', "actions": false })
  visView = container.view
  let [area, sum] = util.getTotalAreasAndValuesForVersion(state.version.header, visView.data('geo_1'), visView.data('source_csv'))
  totalArea = area
  totalValue = sum

  visView.addResizeListener(function() {
    totalArea = util.getTotalAreas(visView.data('geo_1'))
    update()
  })

  update()
})

async function switchVersion() {
  versionSpec.data[1].url = util.getGeojsonURL(props.currentMapName, props.stringKey, state.version.name + '.json')

  let container = await embed('#' + props.mapID + '-offscreen', <VisualizationSpec> versionSpec, { renderer: 'svg', "actions": false })
  var transitions = 0

  function finalize() {
    container.view.initialize('#' + props.mapID + '-vis').runAsync()
    visView = container.view
    update()
  }

  visEl.selectAll('path[aria-roledescription="geoshape"]').each(function (this: any) {
    let geoID = d3.select(this).attr('aria-label')
    let labelID = geoID.replace("geoshape", "geolabel")

    let newD = offscreenEl.select('path[aria-label="' + geoID + '"]').attr('d')
    d3.select(this).transition().ease(d3.easeCubic).duration(1000).attr('d', newD)
      .on("start", function() { transitions++ })
      .on( "end", function() { if( --transitions === 0 ) finalize() })

    let labelEl =  offscreenEl.select('text[aria-label="' + labelID + '"]')
    let newLabelPos = labelEl.attr('transform')
    let newLabelOpacity = labelEl.attr('opacity')
    visEl.select('text[aria-label="' + labelID + '"]').transition().ease(d3.easeCubic).duration(1000)
      .attr('transform', newLabelPos).attr('opacity', newLabelOpacity)
      .on("start", function() { transitions++ })
      .on( "end", function() { if( --transitions === 0 ) finalize() })
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
  const valuePerPixel = totalValue / totalArea
  // Each square to be in the whereabouts of 1% of totalValue.
  let valuePerSquare = totalValue / 100
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
}

function getData(dataname: string): any {
  return visView.data(dataname)
}

function getCurrentScale() {
  return (
    state.gridData[state.currentGridIndex].scaleNiceNumber /
    (props.affineScale[0] * props.affineScale[1])
  )
}

async function changeTo(key: number) {
  state.currentGridIndex = key
  state.gridDataKeys = [state.currentGridIndex]
  await nextTick()

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
}

function formatLegendValue() {
  let value = state.gridData[state.currentGridIndex].scaleNiceNumber
  value = value / (props.affineScale[0] * props.affineScale[1])
  state.legendUnit = formatLegendText(value, state.scalePowerOf10)
}

function formatLegendText(value: number, scalePowerOf10: number): string {
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
  let stroke_opacity = props.showGrid ? defaultOpacity : 0
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
  <div class="d-flex flex-column card-body p-0">
    <div class="d-flex position-absolute z-1">
      <svg
        v-if="state.gridData[numGridOptions]"
        v-bind:id="props.mapID + '-slider'"
        v-bind:width="state.gridData[numGridOptions].width + 15"
        height="30px"
        style="cursor: pointer; top: -15px"
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
        <span v-html="state.legendUnit"></span>
        {{ state.version?.unit }}
        <div>Total: <span v-html="state.legendTotal"></span></div>
      </div>
    </div>

    <div v-bind:id="props.mapID" class="d-flex flex-fill">
      <div>
        <div v-bind:id="props.mapID + '-offscreen'" class="vis-area offscreen"></div>
        <div v-bind:id="props.mapID + '-vis'" class="vis-area"></div>
        <slot></slot>
      </div>
      <svg width="100%" height="100%" v-bind:id="props.mapID + '-grid-area'">
        <defs>
          <pattern v-bind:id="props.mapID + '-grid'" patternUnits="userSpaceOnUse">
            <path fill="none" stroke="#5A5A5A" stroke-width="2" stroke-opacity="0.3"></path>
          </pattern>
        </defs>
        <rect
          v-if="props.showGrid"
          width="100%"
          height="100%"
          v-bind:fill="'url(#' + props.mapID + '-grid)'"
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
  mix-blend-mode: multiply;
}

.vis-area.offscreen {
  opacity: 0;
}
</style>
