<script setup lang="ts">
import * as d3 from 'd3'
import { ref, reactive, onMounted, nextTick } from 'vue'

import { MapVersionData, MapVersion } from '../lib/mapVersion'
import TouchInfo from '../lib/touchInfo'
import shareState from '../lib/state'
import tracker from '../lib/tracker'
import * as util from '../lib/util'
import type { Mappack } from '../lib/interface'
import type { Region } from '../lib/region'
import CartMap from '../lib/cartMap'
import CartogramLegend from './CartogramLegend.vue'
import CartogramDownload from './CartogramDownload.vue'
import CartogramShare from './CartogramShare.vue'
import TouchVis from './TouchVis.vue'

var map: CartMap
var touchInfo = new TouchInfo()
var pointerangle: number | boolean, // (A)
  pointerposition: number[] | null, // (B)
  pointerdistance: number | boolean // (C)
var lastTouch = 0
var timePan = 0,
  timeScale = 0,
  timeRotate = 0,
  timeStretch3f = 0,
  timeStretch2f = 0,
  totalPan = [0, 0],
  totalRotate = 0
const DELAY_THRESHOLD = 300
const SUPPORT_TOUCH = 'ontouchstart' in window || navigator.maxTouchPoints

const mapLegendEl = ref()
const cartogramLegendEl = ref()
const cartogramDownloadEl = ref()

const props = withDefaults(
  defineProps<{
    handler?: string
    cartogram_data?: any
    cartogramui_data?: any
    mappack: Mappack | null
    mode?: string | null
  }>(),
  {
    handler: 'usa',
    mode: 'full'
  }
)

const state = reactive({
  isLoading: true,
  cursor: 'grab',
  isLockRatio: true,
  touchLenght: 0,
  lastMove: 0,
  stretchDirection: 'x',
  affineMatrix: util.getOriginalMatrix(),
  affineScale: [1, 1] // Keep track of scale for scaling grid easily
})

onMounted(() => {
  if (!props.mappack) return
  //TODO: check windows size for default shareState.options.showBase

  if (!props.cartogram_data) {
    switchMap(props.mappack)
  } else {
    props.cartogram_data.tooltip = props.cartogramui_data.tooltip
    var mapVersionData = MapVersionData.mapVersionDataFromMappack(null, props.cartogram_data)
    switchMap(props.mappack, mapVersionData)
  }
})

async function switchMap(mappack: Mappack, mapVersionData: MapVersionData | null = null) {
  state.isLoading = true
  map = new CartMap(props.handler, mappack.config)
  let data_names = mappack.config.data_names || ['original', 'population']
  let current_sysname = '0-base'
  map.addVersion(
    '0-base',
    MapVersionData.mapVersionDataFromMappack(mappack, mappack[data_names[0]]),
    '0-base'
  )
  for (let i = 1; i < data_names.length; i++) {
    current_sysname = i.toString() + '-' + data_names[i]
    map.addVersion(
      current_sysname,
      MapVersionData.mapVersionDataFromMappack(null, mappack[data_names[i]]),
      '0-base'
    )
  }

  if (mapVersionData !== null) {
    map.addVersion('99-cartogram', mapVersionData, '0-base')
    current_sysname = '99-cartogram'
  }
  shareState.current_sysname = current_sysname

  /*
    The keys in the colors.json file are prefixed with id_. We iterate through the regions and extract the color
    information from colors.json to produce a color map where the IDs are plain region IDs, as required by
    CartMap.
    */
  var colors: { [key: string]: string } = {}
  Object.keys(map.regions).forEach(function (region_id) {
    colors[region_id] = mappack.colors['id_' + region_id]
  })
  map.colors = colors
  state.isLoading = false

  await nextTick()
  map.drawVersion('0-base', 'map-area', ['map-area', 'cartogram-area'])
  map.drawVersion(shareState.current_sysname, 'cartogram-area', ['map-area', 'cartogram-area'])
}

function switchVersion(version: string) {
  if (!version) return
  map?.switchVersion(shareState.current_sysname, version, 'cartogram-area')
  shareState.current_sysname = version
  tracker.push('switch_data', version + '-')
}

function getRegions(): { [key: string]: Region } {
  return map?.regions || {}
}

function getVersions(): { [key: string]: MapVersion } {
  return map?.versions || {}
}

// https://observablehq.com/@d3/multitouch
function onTouchstart(event: any, id: string) {
  touchInfo.set(event)
  state.touchLenght = touchInfo.length
  var now = new Date().getTime()
  var timesince = now - lastTouch
  if (touchInfo.length === 1 && timesince < DELAY_THRESHOLD && timesince > 0) {
    // Double tap
    transformReset()
    tracker.push('reset', 'double-tap')
  } else {
    const t = touchInfo.getPoints()
    if (t.length > 0) {
      pointerangle = t.length > 1 && Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (A)
      pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0] // (B)
      pointerdistance = t.length > 1 && Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (C)
    }
  }

  lastTouch = new Date().getTime()
  state.lastMove = lastTouch
  if (event.cancelable) event.preventDefault()
}

function onTouchend(event: any) {
  touchInfo.clear(event)
  state.touchLenght = touchInfo.length

  snapToBetterNumber()
  if (touchInfo.length === 0) {
    pointerposition = null // signals mouse up

    if (timePan || timeScale || timeRotate || timeStretch3f || timeStretch2f) {
      tracker.push('pan', timePan)
      tracker.push('scale', timeScale)
      tracker.push('rotate', timeRotate)
      tracker.push('stretch_3finger', timeStretch3f)
      tracker.push('stretch_2finger', timeStretch2f)
      tracker.push('pan_value', totalPan[0].toFixed(2) + ':' + totalPan[1].toFixed(2))
      tracker.push('rotate_value', totalRotate.toFixed(2))
      tracker.push(
        'scale_value',
        state.affineScale[0].toFixed(2) + ':' + state.affineScale[1].toFixed(2)
      )
    }

    timePan = 0
    timeScale = 0
    timeRotate = 0
    timeStretch3f = 0
    timeStretch2f = 0
  } else {
    const t = touchInfo.getPoints()
    if (t.length > 0) {
      pointerangle = t.length > 1 && Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (A)
      pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0] // (B)
      pointerdistance = t.length > 1 && Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (C)
    }
  }

  if (event.cancelable) event.preventDefault()
}

function onTouchmove(event: any, id: string) {
  touchInfo.update(event)
  if (touchInfo.length < 1 || touchInfo.length > 3 || !pointerposition) return

  const t = touchInfo.getPoints()
  if (t.length < 1) return

  var matrix = util.getOriginalMatrix()
  var angle = 0
  var position = [0, 0]
  var scale = [1, 1]
  var now = new Date().getTime()

  // Order should be rotate, scale, translate
  // https://gamedev.stackexchange.com/questions/16719/what-is-the-correct-order-to-multiply-scale-rotation-and-translation-matrices-f
  if (
    shareState.options.stretchable &&
    t.length > 1 &&
    (touchInfo.length === 3 || (touchInfo.length === 2 && !state.isLockRatio))
  ) {
    // rotate
    var pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
    if (pointerangle && typeof pointerangle === 'number') angle = pointerangle2 - pointerangle
    else angle = 0
    pointerangle = pointerangle2
    matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(angle))
    timeRotate += now - state.lastMove
    totalRotate += angle

    // stretch
    var pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
    if (pointerdistance && typeof pointerdistance === 'number')
      scale[0] = pointerdistance2 / pointerdistance
    else scale[0] = 0
    state.affineScale[0] *= scale[0]
    pointerdistance = pointerdistance2
    if (scale[0] !== 0) {
      matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(pointerangle))
      matrix = util.multiplyMatrix(matrix, util.getScaleMatrix(scale[0], 1))
      matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(-pointerangle))
    }

    if (touchInfo.length === 3) {
      timeStretch3f += now - state.lastMove
    } else {
      timeStretch2f += now - state.lastMove
    }
  } else if (t.length > 1) {
    // (B) rotate
    if (shareState.options.rotatable && pointerangle && typeof pointerangle === 'number') {
      var pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
      angle = pointerangle2 - pointerangle
      pointerangle = pointerangle2
      matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(angle))
      timeRotate += now - state.lastMove
      totalRotate += angle
    }
    // (C) scale
    if (shareState.options.zoomable && pointerdistance && typeof pointerdistance === 'number') {
      var pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
      scale[0] = pointerdistance2 / pointerdistance
      scale[1] = pointerdistance2 / pointerdistance
      state.affineScale[0] *= scale[0]
      state.affineScale[1] *= scale[1]
      pointerdistance = pointerdistance2
      if (scale[0] !== 0 && scale[1] !== 0)
        matrix = util.multiplyMatrix(matrix, util.getScaleMatrix(scale[0], scale[1]))
      timeScale += now - state.lastMove
    }
  }

  // (A) translate
  var pointerposition2 = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0]
  position[0] = pointerposition2[0] - pointerposition[0]
  position[1] = pointerposition2[1] - pointerposition[1]
  pointerposition = pointerposition2
  matrix = util.multiplyMatrix(matrix, util.getTranslateMatrix(position[0], position[1]))
  timePan += now - state.lastMove
  totalPan[0] += position[0]
  totalPan[1] += position[1]

  transformVersion(matrix, state.affineMatrix)
  if (event.cancelable) event.preventDefault()

  state.lastMove = new Date().getTime()
}

function onWheel(event: any) {
  var matrix: Array<Array<number>> = []
  if (event.shiftKey) {
    matrix = util.getRotateMatrix(event.wheelDelta / 1000)
  } else {
    var scale = 1 + event.wheelDelta / 1000
    var scales

    if (state.isLockRatio) {
      scales = [scale, scale]
    } else if (state.stretchDirection === 'x') {
      scales = [scale, 1]
    } else {
      scales = [1, scale]
    }

    state.affineScale[0] *= scales[0]
    state.affineScale[1] *= scales[1]
    matrix = util.getScaleMatrix(scales[0], scales[1])
  }
  transformVersion(matrix, state.affineMatrix)
  if (event.cancelable) event.preventDefault()
}

function switchMode() {
  if (SUPPORT_TOUCH) {
    state.isLockRatio = !state.isLockRatio
  } else if (state.isLockRatio) {
    state.stretchDirection = 'x'
    state.isLockRatio = false
  } else if (state.stretchDirection === 'x') {
    state.stretchDirection = 'y'
  } else {
    state.isLockRatio = true
  }
  tracker.push('lock_ratio', state.isLockRatio)
}

function transformVersion(matrix1: Array<Array<number>>, matrix2: Array<Array<number>>) {
  state.affineMatrix = util.multiplyMatrix(matrix1, matrix2)

  d3.selectAll('#cartogram-area-svg g').attr(
    'transform',
    'matrix(' +
      state.affineMatrix[0][0] +
      ' ' +
      state.affineMatrix[1][0] +
      ' ' +
      state.affineMatrix[0][1] +
      ' ' +
      state.affineMatrix[1][1] +
      ' ' +
      state.affineMatrix[0][2] +
      ' ' +
      state.affineMatrix[1][2] +
      ')'
  )
}

function transformReset() {
  state.affineMatrix = util.getOriginalMatrix()
  state.affineScale = [1, 1]
  totalPan = [0, 0]
  totalRotate = 0
  transformVersion(state.affineMatrix, state.affineMatrix)
}

function snapToBetterNumber() {
  let value = cartogramLegendEl.value.getCurrentScale()
  let [scaleNiceNumber, scalePowerOf10] = util.findNearestNiceNumber(value)
  let targetValue = scaleNiceNumber * Math.pow(10, scalePowerOf10)
  let adjustedScale = Math.sqrt(value / targetValue)

  state.affineScale[0] *= adjustedScale
  state.affineScale[1] *= adjustedScale
  var matrix = util.getScaleMatrix(adjustedScale, adjustedScale)
  transformVersion(matrix, state.affineMatrix)
}

defineExpose({
  switchMap,
  switchVersion,
  getRegions,
  getVersions,
  mapLegendEl,
  cartogramLegendEl
})
</script>

<template>
  <div class="pointervis">
    <TouchVis
      v-bind:key="state.lastMove"
      v-bind:handler="props.handler"
      v-bind:touchInfo="touchInfo"
      v-bind:touchLenght="state.touchLenght"
    />
  </div>

  <div id="cartogram" class="d-flex flex-fill card-group">
    <div class="card w-100" v-bind:class="[shareState.options.showBase ? 'd-flex' : 'd-none']">
      <div class="d-flex flex-column card-body">
        <CartogramLegend
          v-if="!state.isLoading"
          ref="mapLegendEl"
          mapID="map-area"
          v-bind:map="map"
          sysname="0-base"
        >
          <svg id="map-area-svg" class="vis-area"></svg>
        </CartogramLegend>
      </div>

      <div class="card-footer d-flex justify-content-between">
        <div class="text-nowrap overflow-hidden">Equal-Area Map</div>
        <div class="text-nowrap">
          <button
            v-if="mode !== 'embed'"
            class="btn btn-primary mx-1"
            id="map-download"
            v-on:click="
              cartogramDownloadEl.generateSVGDownloadLinks(
                'map-area',
                JSON.stringify(map?.getVersionGeoJSON('0-base'))
              )
            "
            data-bs-toggle="modal"
            data-bs-target="#downloadModal"
            title="Download map"
          >
            <i class="fas fa-download"></i>
          </button>
        </div>
      </div>
    </div>

    <div class="card w-100">
      <div class="d-flex flex-column card-body">
        <CartogramLegend
          v-if="!state.isLoading"
          ref="cartogramLegendEl"
          mapID="cartogram-area"
          v-bind:map="map"
          v-bind:sysname="shareState.current_sysname"
          v-bind:affineScale="state.affineScale"
          v-on:gridChanged="snapToBetterNumber"
        >
          <svg
            id="cartogram-area-svg"
            class="vis-area"
            v-bind:style="{ cursor: state.cursor }"
            v-on:mousedown="onTouchstart($event, 'cartogram-area-svg')"
            v-on:touchstart="onTouchstart($event, 'cartogram-area-svg')"
            v-on:mousemove="onTouchmove($event, 'cartogram-area-svg')"
            v-on:touchmove="onTouchmove($event, 'cartogram-area-svg')"
            v-on:mouseup="onTouchend"
            v-on:touchend="onTouchend"
            v-on:wheel="onWheel"
          ></svg>
          <img class="position-absolute bottom-0 end-0 z-3" src="/static/img/by.svg" alt="cc-by" />
        </CartogramLegend>
        <div class="position-absolute end-0" style="width: 2.5rem">
          <button
            class="btn btn-primary w-100 my-1"
            v-on:click="switchMode()"
            v-bind:title="state.isLockRatio ? 'Switch to free transform' : 'Switch to lock ratio'"
          >
            <i v-if="state.touchLenght === 3" class="fas fa-unlock"></i>
            <i v-else-if="state.isLockRatio" class="fas fa-lock"></i>
            <i v-else-if="SUPPORT_TOUCH" class="fas fa-unlock"></i>
            <i v-else-if="state.stretchDirection === 'x'" class="fas fa-arrows-alt-h"></i>
            <i v-else class="fas fa-arrows-alt-v"></i>
          </button>
          <button
            class="btn btn-primary w-100 my-1"
            v-on:click="
              () => {
                transformReset()
                tracker.push('reset', 'button')
              }
            "
            title="Reset"
          >
            <i class="fas fa-crosshairs"></i>
          </button>
        </div>
      </div>

      <div class="card-footer d-flex justify-content-between">
        <div class="d-none d-sm-block text-nowrap overflow-hidden">Cartogram</div>
        <div class="text-nowrap">
          <span v-if="mode !== 'embed'">
            <button
              class="btn btn-primary mx-1"
              id="cartogram-download"
              v-on:click="
                cartogramDownloadEl.generateSVGDownloadLinks(
                  'cartogram-area',
                  JSON.stringify(map?.getVersionGeoJSON(shareState.current_sysname))
                )
              "
              data-bs-toggle="modal"
              data-bs-target="#downloadModal"
              title="Download cartogram"
            >
              <i class="fas fa-download"></i>
            </button>
            <CartogramShare
              v-bind:sysname="props.handler"
              v-bind:sharing_key="
                props.cartogramui_data ? props.cartogramui_data.unique_sharing_key : null
              "
            />
          </span>
        </div>
      </div>
    </div>

    <p id="tooltip" style="display: none">&nbsp;</p>
    <CartogramDownload ref="cartogramDownloadEl" />
  </div>
</template>

<style>
#map-area,
#cartogram-area {
  position: relative;
}

.vis-area {
  position: absolute;
  width: 100%;
  height: 100%;
  min-height: 100px;
  mix-blend-mode: multiply;
}

.vis-area g {
  transform-box: fill-box;
  transform-origin: center;
}

.vis-area text {
  font-family: sans-serif;
  fill: #000;
  alignment-baseline: middle;
}

.vis-area line {
  stroke: #000;
  stroke-width: 1;
}
</style>

<style scoped>
/* TODO: move to Tooltip component */
#tooltip {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid black;
  width: auto;
  height: auto;
  min-height: 75px;
  padding: 5px;
  position: absolute;
  font-size: small;
  top: 0;
  left: 0;
  z-index: 1000;
}

.pointervis {
  position: fixed;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  z-index: 1001;
  pointer-events: none;
}
</style>
