<script setup lang="ts">
/**
 * The map panel with functions for interactivity to manipulate viewport.
 */

import * as d3 from 'd3'
import { ref, reactive } from 'vue'

import TouchInfo from '../lib/touchInfo'
import * as util from '../lib/util'
import CTouchVis from './CTouchVis.vue'
import CPanelLegend from './CPanelLegend.vue'
import CPanelSelectVersion from './CPanelSelectVersion.vue'
import CPanelBtnDownload from './CPanelBtnDownload.vue'

const touchInfo = new TouchInfo()
let pointerangle: number | boolean, // (A)
  pointerposition: number[] | null, // (B)
  pointerdistance: number | boolean // (C)
let lastTouch = 0

const DELAY_THRESHOLD = 300
const SUPPORT_TOUCH = 'ontouchstart' in window || navigator.maxTouchPoints

const legendEl = ref()

const props = withDefaults(
  defineProps<{
    panelID: string
    defaultVersionKey: string
    mapDBKey?: string
  }>(),
  {
    mapDBKey: ''
  }
)

const state = reactive({
  versionKey: props.defaultVersionKey,
  cursor: 'grab',
  isLockRatio: true,
  touchLenght: 0,
  lastMove: 0,
  stretchDirection: 'x',
  affineMatrix: util.getOriginalMatrix(),
  affineScale: [1, 1] // Keep track of scale for scaling grid easily
})

// https://observablehq.com/@d3/multitouch
function onPointerdown(event: any) {
  touchInfo.set(event)
  state.touchLenght = touchInfo.length()

  const now = new Date().getTime()
  const timesince = now - lastTouch
  if (touchInfo.length() === 1 && timesince < DELAY_THRESHOLD && timesince > 0) {
    // Double tap
    transformReset()
  } else {
    const t = touchInfo.getMergedPoints()
    if (t.length > 0) {
      pointerangle = t.length > 1 && Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (A)
      pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0] // (B)
      pointerdistance = t.length > 1 && Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (C)
    }
  }

  lastTouch = new Date().getTime()
  state.lastMove = lastTouch
}

function onPointerup(event: any) {
  legendEl.value.$el.releasePointerCapture(event.pointerId)
  touchInfo.clear(event)
  state.touchLenght = touchInfo.length()

  snapToBetterNumber()
  if (touchInfo.length() === 0) {
    pointerposition = null // signals mouse up
  } else {
    const t = touchInfo.getMergedPoints()
    if (t.length > 0) {
      pointerangle = t.length > 1 && Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (A)
      pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0] // (B)
      pointerdistance = t.length > 1 && Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (C)
    }
  }
}

function onPointermove(event: any) {
  touchInfo.update(event)
  if (touchInfo.length() < 1 || touchInfo.length() > 3 || !pointerposition) return

  // Capture pointer so gesture can be beyond the panel
  document.getElementById('vg-tooltip-element')?.classList.remove('visible')
  legendEl.value.$el.setPointerCapture(event.pointerId)

  const t = touchInfo.getMergedPoints()
  let matrix = util.getOriginalMatrix()
  let angle = 0
  const position = [0, 0]
  const scale = [1, 1]
  const now = new Date().getTime()

  // Order should be rotate, scale, translate
  // https://gamedev.stackexchange.com/questions/16719/what-is-the-correct-order-to-multiply-scale-rotation-and-translation-matrices-f
  if (
    t.length > 1 &&
    (touchInfo.length() === 3 || (touchInfo.length() === 2 && !state.isLockRatio))
  ) {
    // rotate
    const pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
    if (pointerangle && typeof pointerangle === 'number') angle = pointerangle2 - pointerangle
    else angle = 0
    pointerangle = pointerangle2
    matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(angle))

    // stretch
    const pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
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
      const pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
      angle = pointerangle2 - pointerangle
      pointerangle = pointerangle2
      matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(angle))
    }
    // (C) scale
    if (pointerdistance && typeof pointerdistance === 'number') {
      const pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
      scale[0] = pointerdistance2 / pointerdistance
      scale[1] = pointerdistance2 / pointerdistance
      state.affineScale[0] *= scale[0]
      state.affineScale[1] *= scale[1]
      pointerdistance = pointerdistance2
      if (scale[0] !== 0 && scale[1] !== 0)
        matrix = util.multiplyMatrix(matrix, util.getScaleMatrix(scale[0], scale[1]))
    }
  }

  const timesince = now - lastTouch
  if (touchInfo.length() > 1 || (touchInfo.length() === 1 && timesince > DELAY_THRESHOLD)) {
    // (A) translate
    const pointerposition2 = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0]
    position[0] = pointerposition2[0] - pointerposition[0]
    position[1] = pointerposition2[1] - pointerposition[1]
    pointerposition = pointerposition2
    matrix = util.multiplyMatrix(matrix, util.getTranslateMatrix(position[0], position[1]))
  }

  transformVersion(matrix, state.affineMatrix)

  state.lastMove = new Date().getTime()
}

function onWheel(event: any) {
  let matrix: Array<Array<number>> = []
  if (event.shiftKey) {
    matrix = util.getRotateMatrix(event.wheelDelta / 1000)
  } else {
    const scale = 1 + event.wheelDelta / 1000
    let scales

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

  d3.selectAll('#' + props.panelID + ' g.root').attr(
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
  const value = legendEl.value.getCurrentScale()
  if (value === 0) return

  const [scaleNiceNumber, scalePowerOf10] = util.findNearestNiceNumber(value)
  const targetValue = scaleNiceNumber * Math.pow(10, scalePowerOf10)
  const adjustedScale = Math.sqrt(value / targetValue)

  state.affineScale[0] *= adjustedScale
  state.affineScale[1] *= adjustedScale
  const matrix = util.getScaleMatrix(adjustedScale, adjustedScale)
  transformVersion(matrix, state.affineMatrix)
}
</script>

<template>
  <div class="card w-100">
    <div class="d-flex flex-column card-body">
      <c-panel-legend
        ref="legendEl"
        style="touch-action: none"
        v-bind:style="{ cursor: state.cursor }"
        v-bind:panelID="props.panelID"
        v-bind:mapDBKey="props.mapDBKey"
        v-bind:versionKey="state.versionKey"
        v-bind:affineScale="state.affineScale"
        v-on:gridChanged="snapToBetterNumber"
        v-on:pointerdown.stop.prevent="onPointerdown"
        v-on:pointermove.stop.prevent="onPointermove"
        v-on:pointerup.stop.prevent="onPointerup"
        v-on:wheel.stop.prevent="onWheel"
        v-on:versionUpdated="transformVersion(state.affineMatrix, util.getOriginalMatrix())"
      >
        <img class="position-absolute bottom-0 end-0 z-3" src="/static/img/by.svg" alt="cc-by" />
      </c-panel-legend>
      <div class="position-absolute end-0" style="width: 2.5rem">
        <button
          class="btn btn-secondary w-100 my-1"
          v-on:click="switchMode()"
          v-bind:title="state.isLockRatio ? 'Switch to free transform' : 'Switch to lock ratio'"
        >
          <i v-if="state.touchLenght === 3" class="fas fa-unlock"></i>
          <i v-else-if="state.isLockRatio" class="fas fa-lock"></i>
          <i v-else-if="SUPPORT_TOUCH" class="fas fa-unlock"></i>
          <i v-else-if="state.stretchDirection === 'x'" class="fas fa-arrows-alt-h"></i>
          <i v-else class="fas fa-arrows-alt-v"></i>
        </button>
        <button class="btn btn-secondary w-100 my-1" v-on:click="transformReset()" title="Reset">
          <i class="fas fa-crosshairs"></i>
        </button>
      </div>
    </div>

    <div class="card-footer d-flex justify-content-between">
      <c-panel-select-version
        v-bind:currentVersionName="state.versionKey"
        v-on:version_changed="(version) => (state.versionKey = version)"
      />
      <c-panel-btn-download
        v-bind:mapDBKey="props.mapDBKey"
        v-bind:versionKey="state.versionKey"
        v-bind:panelID="props.panelID"
      />
    </div>
  </div>

  <c-touch-vis
    v-bind:key="state.lastMove"
    v-bind:touchInfo="touchInfo"
    v-bind:touchLenght="state.touchLenght"
  />
</template>
