<script setup lang="ts">
import type CartMap from '@/lib/cartMap'
import type { MapVersion } from '@/lib/mapVersion'
import * as d3 from 'd3'
import { onMounted, reactive, watch } from 'vue'

var legendSVGID: string
var version: MapVersion
var versionArea: number
var versionTotalValue: number
const locale =
  navigator.languages && navigator.languages.length ? navigator.languages[0] : navigator.language
var defaultOpacity = 0.3

const props = withDefaults(
  defineProps<{
    mapID: string
    isGridVisible?: boolean
    isLegendResizable?: boolean
    map: CartMap
    sysname: string
    legendID: string
    mapWidth: number
    mapHeight: number
  }>(),
  {
    isGridVisible: false,
    isLegendResizable: false
  }
)

const state = reactive({
  mapWidth: 100 as number,
  mapHeight: 100 as number,
  unit: 'km sq.' as string,
  legendUnit: '' as string,
  legendTotal: '' as string,
  currentGridPath: 'gridA' as string
})

watch(
  () => props.isGridVisible,
  (type, prevType) => {
    let opacity = props.isGridVisible ? defaultOpacity : 0
    d3.selectAll('#map-area-grid path, #cartogram-area-grid path')
      .transition()
      .ease(d3.easeCubic)
      .duration(500)
      .attr('stroke-opacity', opacity)
  }
)

watch(
  () => props.isLegendResizable,
  (type, prevType) => {
    if (props.isLegendResizable) {
      drawResizableLegend()
    } else {
      drawLegend(null, true)
    }
  }
)

watch(
  () => props.sysname,
  (type, prevType) => {
    update(props.map, props.sysname, props.legendID, props.mapWidth, props.mapHeight)
  }
)

onMounted(() => {
  update(props.map, props.sysname, props.legendID, props.mapWidth, props.mapHeight)
})

/**
 * The following draws the static legend for each map
 * @param {CartMap} map
 * @param {string} sysname The sysname of the map version
 * @param {string} legendID The html id used for legend SVG display
 */
function update(
  map: CartMap,
  sysname: string,
  legendID: string,
  mapWidth: number,
  mapHeight: number
) {
  if (!map) return
  state.mapWidth = mapWidth
  state.mapHeight = mapHeight
  state.unit = Object.values(map.regions)[0].getVersion(sysname).unit
  legendSVGID = legendID
  version = map.versions[sysname]

  const [area, sum] = map.getTotalAreasAndValuesForVersion(sysname)
  versionArea = area
  versionTotalValue = sum

  getLegendData(sysname)
  if (props.isLegendResizable) {
    drawResizableLegend()
  } else {
    drawLegend(null, true)
  }

  drawGridLines()
}

/**
 * The following draws the static legend for each map
 * @param {string} old_sysname The previous sysname after map version switch. Optional.
 * @param {boolean} change_map True if the map is displayed for the first time or the map is changed. Optional.
 */
function drawLegend(old_sysname: string | null = null, change_map: boolean = false) {
  const legendSVG = d3.select('#' + legendSVGID)

  // Remove existing child nodes
  legendSVG.selectAll('*').remove()

  // Get the transitionWidth which is previously selected grid path. This value helps in transitioning
  // from static legend to resizable legend.
  let transitionWidth

  // When switching between static and selectable legend.
  if (change_map == true) {
    transitionWidth = version.legendData.gridData.gridA.width
  } else if (old_sysname == null) {
    transitionWidth = version.legendData.gridData.gridC.width
  } else {
    // When switching between versions
    if (props.isLegendResizable) {
      transitionWidth = version.legendData.gridData.gridC.width
    } else {
      transitionWidth = version.legendData['gridData'][state.currentGridPath]['width']
    }
  }

  // Retrive legend information
  const width = version.legendData['gridData'][state.currentGridPath]['width'] || 0
  const scaleNiceNumber =
    version.legendData['gridData'][state.currentGridPath]['scaleNiceNumber'] || 0
  const scalePowerOf10 = version.legendData.scalePowerOf10 || 0

  legendSVG.attr('width', width! + 2).attr('height', width! + 2)
  const legendSquare = legendSVG
    .append('rect')
    .attr('id', legendSVGID + 'A')
    .attr('x', '1') // Padding of 20px on the left
    .attr('y', '1')
    .attr('fill', '#FFFFFF')
    .attr('stroke', '#AAAAAA')
    .attr('stroke-width', '2px')
    .attr('width', transitionWidth)
    .attr('height', transitionWidth)
    .transition()
    .ease(d3.easeCubic)
    .duration(1000)
    .attr('width', width)
    .attr('height', width)

  state.legendUnit = formatLegendText(scaleNiceNumber, scalePowerOf10)

  const totalScalePowerOfTen = Math.floor(Math.log10(versionTotalValue))
  const totalNiceNumber = versionTotalValue / Math.pow(10, totalScalePowerOfTen)
  state.legendTotal = formatLegendText(totalNiceNumber, totalScalePowerOfTen)

  // Verify if legend is accurate
  //verifyLegend(sysname, width, scaleNiceNumber * Math.pow(10, scalePowerOf10))
}

/**
 * The following draws the resizable legend for each map
 * @param {string} sysname The sysname of the map version
 * @param {string} legendSVGID The html id used for legend SVG display
 * @param {string} old_sysname The previous sysname after map version switch. Optional.
 */
function drawResizableLegend(old_sysname: string | null = null) {
  const legendSVG = d3.select('#' + legendSVGID)

  // Remove existing child nodes
  legendSVG.selectAll('*').remove()
  // Retrive legend information
  const scalePowerOf10 = version.legendData.scalePowerOf10 || 0
  const widthA = version.legendData.gridData.gridA.width || 0
  const widthB = version.legendData.gridData.gridB.width || 0
  const widthC = version.legendData.gridData.gridC.width || 0
  const scaleNiceNumberA = version.legendData.gridData.gridA.scaleNiceNumber || 0
  const scaleNiceNumberB = version.legendData.gridData.gridB.scaleNiceNumber || 0
  const scaleNiceNumberC = version.legendData.gridData.gridC.scaleNiceNumber || 0
  // We get currently selected grid path (i.e. whether "gridA", "gridB", or "gridC") and type of legend
  // Get legend width data of previous version/ previous static legend
  let transitionWidthA
  let transitionWidthB
  let transitionWidthC

  if (old_sysname == null) {
    transitionWidthA =
      transitionWidthB =
      transitionWidthC =
        version.legendData['gridData'][state.currentGridPath]['width']
  } else {
    if (props.isLegendResizable) {
      transitionWidthA = version.legendData.gridData.gridA.width
      transitionWidthB = version.legendData.gridData.gridB.width
      transitionWidthC = version.legendData.gridData.gridC.width
    } else {
      transitionWidthA =
        transitionWidthB =
        transitionWidthC =
          version.legendData['gridData'][state.currentGridPath]['width']
    }
  }

  // Create child nodes of SVG element.
  legendSVG.attr('width', widthC + 2).attr('height', widthC + 2)
  const legendSquareC = legendSVG
    .append('rect')
    .attr('id', legendSVGID + 'C')
    .attr('x', '1')
    .attr('y', '1')
    .attr('fill', '#eeeeee')
    .attr('stroke', '#AAAAAA')
    .attr('stroke-width', '2px')
  const legendSquareB = legendSVG
    .append('rect')
    .attr('id', legendSVGID + 'B')
    .attr('x', '1')
    .attr('y', '1')
    .attr('fill', '#EEEEEE')
    .attr('stroke', '#AAAAAA')
    .attr('stroke-width', '2px')
  const legendSquareA = legendSVG
    .append('rect')
    .attr('id', legendSVGID + 'A')
    .attr('x', '1')
    .attr('y', '1')
    .attr('fill', '#FFFFFF')
    .attr('stroke', '#AAAAAA')
    .attr('stroke-width', '2px')

  // Adjust width of square according to chosen nice number and add transition to Legends
  legendSquareA
    .attr('width', transitionWidthA)
    .attr('height', transitionWidthA)
    .transition()
    .ease(d3.easeCubic)
    .duration(1000)
    .attr('width', widthA)
    .attr('height', widthA)
  legendSquareB
    .attr('width', transitionWidthB)
    .attr('height', transitionWidthB)
    .transition()
    .ease(d3.easeCubic)
    .duration(1000)
    .attr('width', widthB)
    .attr('height', widthB)
  legendSquareC
    .attr('width', transitionWidthC)
    .attr('height', transitionWidthC)
    .transition()
    .ease(d3.easeCubic)
    .duration(1000)
    .attr('width', widthC)
    .attr('height', widthC)

  const totalScalePowerOfTen = Math.floor(Math.log10(versionTotalValue))
  const totalNiceNumber = versionTotalValue / Math.pow(10, totalScalePowerOfTen)
  state.legendTotal = formatLegendText(totalNiceNumber, totalScalePowerOfTen)

  // Event for when a different legend size is selected.
  const changeToC = () => {
    // Update currentGridPath in SVG Data
    state.currentGridPath = 'gridC'
    d3.select('#' + legendSVGID + 'C').attr('fill', '#FFFFFF')
    d3.select('#' + legendSVGID + 'B').attr('fill', '#FFFFFF')
    d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')
    state.legendUnit = formatLegendText(scaleNiceNumberC, scalePowerOf10, true)
    updateGridLines(widthC)
  }
  const changeToB = () => {
    // Update currentGridPath in SVG Data
    state.currentGridPath = 'gridB'
    d3.select('#' + legendSVGID + 'C').attr('fill', '#EEEEEE')
    d3.select('#' + legendSVGID + 'B').attr('fill', '#FFFFFF')
    d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')
    state.legendUnit = formatLegendText(scaleNiceNumberB, scalePowerOf10, true)
    updateGridLines(widthB)
  }
  const changeToA = () => {
    // Update currentGridPath in SVG Data
    state.currentGridPath = 'gridA'
    d3.select('#' + legendSVGID + 'C').attr('fill', '#EEEEEE')
    d3.select('#' + legendSVGID + 'B').attr('fill', '#EEEEEE')
    d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')
    state.legendUnit = formatLegendText(scaleNiceNumberA, scalePowerOf10, true)
    updateGridLines(widthA)
  }

  //Update colors of the legend
  if (state.currentGridPath === 'gridA') changeToA()
  else if (state.currentGridPath === 'gridB') changeToB()
  else if (state.currentGridPath === 'gridC') changeToC()

  legendSquareC.attr('cursor', 'pointer').on('click', changeToC)
  legendSquareB.attr('cursor', 'pointer').on('click', changeToB)
  legendSquareA.attr('curser', 'pointer').on('click', changeToA)

  // Add legend square labels
  const c_label = legendSVG
    .append('text')
    .attr('x', 1 + widthC - 13)
    .attr('y', widthC)
    .attr('font-size', 8)
    .attr('cursor', 'pointer')
    .text(scaleNiceNumberC)
    .attr('opacity', 0)
    .on('click', changeToC)
  let b_label_location_shift_x = 10
  let b_label_location_shift_y = 0
  // If there is less space between 'a' square and 'b' square, then we move the b label bit to the right and down
  if (widthB - widthA < 11) {
    b_label_location_shift_y = 2.3
    if (scaleNiceNumberB >= 10) {
      b_label_location_shift_x = 9
    } else {
      b_label_location_shift_x = 7
    }
  }
  const b_label = legendSVG
    .append('text')
    .attr('x', 1 + widthB - b_label_location_shift_x)
    .attr('y', widthB + b_label_location_shift_y)
    .attr('font-size', 8)
    .attr('cursor', 'pointer')
    .text(scaleNiceNumberB)
    .attr('opacity', 0)
    .on('click', changeToB)
  const a_label = legendSVG
    .append('text')
    .attr('x', 1 + widthA - 10)
    .attr('y', widthA)
    .attr('font-size', 8)
    .attr('cursor', 'pointer')
    .text(scaleNiceNumberA)
    .attr('opacity', 0)
    .on('click', changeToA)

  // Add transition to Text elements
  c_label.transition().ease(d3.easeCubic).delay(200).duration(800).attr('opacity', 1)
  b_label.transition().ease(d3.easeCubic).delay(200).duration(800).attr('opacity', 1)
  a_label.transition().ease(d3.easeCubic).delay(200).duration(800).attr('opacity', 1)
  // Verify if legend is accurate
  //verifyLegend(sysname, wi* Math.pow(10, scalePowerOf10))
}

/**
 * The following returns the scaling factors (x and y) of map of specified version.
 * @param {string} sysname The sysname of the map version
 * @returns {number[]} The total polygon area of the specified map version
 */
function getVersionPolygonScale(sysname: string): [number, number] {
  console.log(version)
  const version_width = version.extrema.max_x - version.extrema.min_x
  const version_height = version.extrema.max_y - version.extrema.min_y

  const scale_x = version.dimension.x / version_width
  const scale_y = version.dimension.y / version_height

  return [scale_x, scale_y]
}

/**
 * Calculates legend information of the map version
 * @param {string} sysname The sysname of the map version
 */
function getLegendData(sysname: string) {
  // Obtain the scaling factors, area and total value for this map version.
  const [scaleX, scaleY] = getVersionPolygonScale(sysname)
  const valuePerPixel = versionTotalValue / (versionArea * scaleX * scaleY)
  // Each square to be in the whereabouts of 1% of versionTotalValue.
  let valuePerSquare = versionTotalValue / 100
  let widthA = Math.sqrt(valuePerSquare / valuePerPixel)
  // If width is too small, we increment the percentage.
  while (widthA < 20) {
    valuePerSquare *= 2
    widthA = Math.sqrt(valuePerSquare / valuePerPixel)
  }
  let widthB = widthA
  let widthC = widthA
  // Declare and assign variables for valuePerSquare's power of 10 and "nice number".
  let scalePowerOf10 = Math.floor(Math.log10(valuePerSquare))
  let scaleNiceNumberA = 99
  let scaleNiceNumberB
  let scaleNiceNumberC
  // We find the "nice number" that is closest to valuePerSquare's
  const valueFirstNumber = valuePerSquare / Math.pow(10, scalePowerOf10)
  let valueDiff = Math.abs(valueFirstNumber - scaleNiceNumberA)
  const niceNumbers = [1, 2, 5, 10]
  niceNumbers.forEach(function (n) {
    if (Math.abs(valueFirstNumber - n) < valueDiff) {
      valueDiff = Math.abs(valueFirstNumber - n)
      scaleNiceNumberA = n
    }
  })
  if (scaleNiceNumberA == 1) {
    scaleNiceNumberB = 2
    scaleNiceNumberC = 5
  } else if (scaleNiceNumberA == 2) {
    scaleNiceNumberB = 5
    scaleNiceNumberC = 10
  } else if (scaleNiceNumberA == 5) {
    scaleNiceNumberB = 10
    scaleNiceNumberC = 20
  } else {
    scaleNiceNumberA = 1
    scaleNiceNumberB = 2
    scaleNiceNumberC = 5
    scalePowerOf10 += 1
  }
  widthA *= Math.sqrt((scaleNiceNumberA * Math.pow(10, scalePowerOf10)) / valuePerSquare)
  widthB *= Math.sqrt((scaleNiceNumberB * Math.pow(10, scalePowerOf10)) / valuePerSquare)
  widthC *= Math.sqrt((scaleNiceNumberC * Math.pow(10, scalePowerOf10)) / valuePerSquare)
  // Store legend Information
  version.legendData.gridData.gridA.width = widthA
  version.legendData.gridData.gridB.width = widthB
  version.legendData.gridData.gridC.width = widthC
  version.legendData.gridData.gridA.scaleNiceNumber = scaleNiceNumberA
  version.legendData.gridData.gridB.scaleNiceNumber = scaleNiceNumberB
  version.legendData.gridData.gridC.scaleNiceNumber = scaleNiceNumberC
  version.legendData.scalePowerOf10 = scalePowerOf10
  version.legendData.unit = state.unit
  version.legendData.versionTotalValue = versionTotalValue
}

function formatLegendText(value: number, scalePowerOf10: number, showMultiplier = false) {
  let originalValue = value * Math.pow(10, scalePowerOf10)
  const formatter = Intl.NumberFormat(locale, {
    notation: 'compact',
    compactDisplay: 'short'
  })

  let formated = ''
  if (showMultiplier)
    formated += ' &#xd7; ' + formatter.format(Math.pow(10, scalePowerOf10)) + ' = '
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
  const [scaleX, scaleY] = getVersionPolygonScale(sysname)
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
  const gridWidth = version.legendData['gridData'][state.currentGridPath]['width'] || 20
  updateGridLines(gridWidth)
}

function updateGridLines(gridWidth: number) {
  let stroke_opacity = props.isGridVisible ? defaultOpacity : 0
  const gridPattern = d3.select('#' + props.mapID + '-grid')
  gridPattern.transition().duration(1000).attr('width', gridWidth).attr('height', gridWidth)
  gridPattern
    .select('path')
    .attr('stroke-opacity', stroke_opacity)
    .attr('d', 'M ' + gridWidth * 2 + ' 0 L 0 0 0 ' + gridWidth * 2) // *2 for pretty transition when resize grid
}
</script>

<template>
  <svg width="100%" height="100%" v-bind:id="props.mapID + '-grid-area'">
    <defs>
      <pattern v-bind:id="props.mapID + '-grid'" patternUnits="userSpaceOnUse">
        <path fill="none" stroke="#5A5A5A" stroke-width="2" stroke-opacity="0.4"></path>
      </pattern>
    </defs>
    <rect width="100%" height="100%" v-bind:fill="'url(#' + props.mapID + '-grid)'"></rect>
  </svg>

  <div class="position-absolute top-0 z-3 d-flex">
    <div><svg v-bind:id="props.mapID + '-legend'"></svg></div>
    <div v-bind:id="props.mapID + '-legend-num'" class="flex-fill p-1">
      <span v-html="state.legendUnit"></span>, Total: <span v-html="state.legendTotal"></span>
      {{ state.unit }}
    </div>
  </div>
</template>

<style scoped></style>
