<script setup lang="ts">
/**
 * The map panel with functions for interactivity to manipulate viewport.
 */

import * as d3 from 'd3'
import { ref, reactive, watch, nextTick } from 'vue'

import TouchInfo from '../lib/touchInfo'
import * as util from '../lib/util'
import CTouchVis from './CTouchVis.vue'
import CPanelLegend from './CPanelLegend.vue'
import CPanelModalDownload from './CPanelModalDownload.vue'
import CPanelBtnShare from './CPanelBtnShare.vue'

let touchInfo = new TouchInfo()
var pointerangle: number | boolean, // (A)
  pointerposition: number[] | null, // (B)
  pointerdistance: number | boolean // (C)
var lastTouch = 0
var currentHighlight: string | null = null
const DELAY_THRESHOLD = 300
const SUPPORT_TOUCH = 'ontouchstart' in window || navigator.maxTouchPoints
const DATA_COL = 3

const mapLegendEl = ref()
const cartogramLegendEl = ref()
const modalDownloadEl = ref()

const props = withDefaults(
  defineProps<{
    currentMapName: string
    currentVersionKey: string
    versions: { [key: string]: any }
    stringKey?: string
    showBase?: boolean
    showGrid?: boolean
    mode?: string | null
  }>(),
  {
    stringKey: '',
    showBase: false,
    showGrid: true,
    mode: 'full'
  }
)

const state = reactive({
  cursor: 'grab',
  isLockRatio: true,
  touchLenght: 0,
  lastMove: 0,
  stretchDirection: 'x',
  affineMatrix: util.getOriginalMatrix(),
  affineScale: [1, 1] // Keep track of scale for scaling grid easily
})

watch(
  () => props.showBase,
  (type, prevType) => {
    nextTick()
    cartogramLegendEl.value.updateView()
  }
)

// https://observablehq.com/@d3/multitouch
function onTouchstart(event: any, id: string) {
  touchInfo.set(event)
  state.touchLenght = touchInfo.length
  var now = new Date().getTime()
  var timesince = now - lastTouch
  if (touchInfo.length === 1 && timesince < DELAY_THRESHOLD && timesince > 0) {
    // Double tap
    transformReset()
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
  if (t.length > 1 && (touchInfo.length === 3 || (touchInfo.length === 2 && !state.isLockRatio))) {
    // rotate
    var pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
    if (pointerangle && typeof pointerangle === 'number') angle = pointerangle2 - pointerangle
    else angle = 0
    pointerangle = pointerangle2
    matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(angle))

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
  } else if (t.length > 1) {
    // (B) rotate
    if (pointerangle && typeof pointerangle === 'number') {
      var pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
      angle = pointerangle2 - pointerangle
      pointerangle = pointerangle2
      matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(angle))
    }
    // (C) scale
    if (pointerdistance && typeof pointerdistance === 'number') {
      var pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
      scale[0] = pointerdistance2 / pointerdistance
      scale[1] = pointerdistance2 / pointerdistance
      state.affineScale[0] *= scale[0]
      state.affineScale[1] *= scale[1]
      pointerdistance = pointerdistance2
      if (scale[0] !== 0 && scale[1] !== 0)
        matrix = util.multiplyMatrix(matrix, util.getScaleMatrix(scale[0], scale[1]))
    }
  }

  var timesince = now - lastTouch
  if (touchInfo.length > 1 || (touchInfo.length === 1 && timesince > DELAY_THRESHOLD)) {
    // (A) translate
    var pointerposition2 = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0]
    position[0] = pointerposition2[0] - pointerposition[0]
    position[1] = pointerposition2[1] - pointerposition[1]
    pointerposition = pointerposition2
    matrix = util.multiplyMatrix(matrix, util.getTranslateMatrix(position[0], position[1]))
  }

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
}

function transformVersion(matrix1: Array<Array<number>>, matrix2: Array<Array<number>>) {
  state.affineMatrix = util.multiplyMatrix(matrix1, matrix2)

  d3.selectAll('#cartogram-area g.root').attr(
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

function highlight(item: { mapID: string; highlightID: string }) {
  if (currentHighlight === item.highlightID) return
  if (item.mapID === 'map-area') cartogramLegendEl.value.highlight(item.highlightID)
  else if (item.mapID === 'cartogram-area') mapLegendEl.value.highlight(item.highlightID)
  currentHighlight = item.highlightID
}
</script>

<template>
  <div class="pointervis">
    <c-touch-vis
      v-bind:key="state.lastMove"
      v-bind:touchInfo="touchInfo"
      v-bind:touchLenght="state.touchLenght"
    />
  </div>

  <div id="cartogram" class="d-flex flex-fill card-group">
    <div class="card w-100" v-if="props.showBase">
      <div class="d-flex flex-column card-body">
        <c-panel-legend
          ref="mapLegendEl"
          mapID="map-area"
          v-bind:currentMapName="props.currentMapName"
          v-bind:stringKey="props.stringKey"
          v-bind:versionKey="Object.keys(props.versions)[0]"
          v-bind:versions="props.versions"
          v-bind:showGrid="props.showGrid"
          v-on:highlight="highlight"
        >
        </c-panel-legend>
      </div>

      <div class="card-footer d-flex justify-content-between">
        <div class="text-nowrap overflow-hidden">Equal-Area Map</div>
        <div class="text-nowrap">
          <button
            v-if="mode !== 'embed'"
            class="btn btn-primary mx-1"
            id="map-download"
            v-on:click="
              modalDownloadEl.generateSVGDownloadLinks(
                'map-area',
                JSON.stringify(mapLegendEl.getData('geo_1'))
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
        <c-panel-legend
          ref="cartogramLegendEl"
          mapID="cartogram-area"
          v-bind:currentMapName="props.currentMapName"
          v-bind:stringKey="props.stringKey"
          v-bind:versionKey="props.currentVersionKey"
          v-bind:versions="props.versions"
          v-bind:showGrid="props.showGrid"
          v-bind:affineScale="state.affineScale"
          v-on:gridChanged="snapToBetterNumber"
          v-bind:style="{ cursor: state.cursor }"
          v-on:mousedown="onTouchstart($event, 'cartogram-area')"
          v-on:touchstart="onTouchstart($event, 'cartogram-area')"
          v-on:mousemove="onTouchmove($event, 'cartogram-area')"
          v-on:touchmove="onTouchmove($event, 'cartogram-area')"
          v-on:mouseup="onTouchend"
          v-on:touchend="onTouchend"
          v-on:wheel="onWheel"
          v-on:highlight="highlight"
        >
          <img class="position-absolute bottom-0 end-0 z-3" src="/static/img/by.svg" alt="cc-by" />
        </c-panel-legend>
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
                modalDownloadEl.generateSVGDownloadLinks(
                  'cartogram-area',
                  JSON.stringify(cartogramLegendEl.getData('geo_1'))
                )
              "
              data-bs-toggle="modal"
              data-bs-target="#downloadModal"
              title="Download cartogram"
            >
              <i class="fas fa-download"></i>
            </button>
            <c-panel-btn-share
              v-bind:stringKey="props.stringKey"
              v-bind:currentMapName="props.currentMapName"
            />
          </span>
        </div>
      </div>
    </div>

    <c-panel-modal-download ref="modalDownloadEl" />
  </div>
</template>

<style>
#map-area,
#cartogram-area {
  position: relative;
}
</style>
