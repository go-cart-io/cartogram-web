<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'

import type { GridData } from '../lib/viewInterface'
import * as config from '../../common/config'

const legendSvgEl = ref()
let handlePointerId = -1
let handlePointerPosition = 0

const props = defineProps<{
  panelID: string
  gridIndex: number
  gridData: GridData
}>()

const state = reactive({
  handlePosition: 0 as number
})

defineExpose({
  setHandlePosition
})

const emit = defineEmits(['change'])

function setHandlePosition(position: number) {
  state.handlePosition = position
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
  state.handlePosition = Math.max(0, Math.min(pos, props.gridData[config.NUM_GRID_OPTIONS].width))
  handlePointerPosition = event.pageX
}

function onHandleUp(event: any) {
  if (handlePointerId !== event.pointerId) return
  legendSvgEl.value.releasePointerCapture(event.pointerId)
  handlePointerId = -1

  let key = 0
  let minDiff = Number.MAX_VALUE
  for (let i = 0; i <= config.NUM_GRID_OPTIONS; i++) {
    const diff = Math.abs(state.handlePosition - props.gridData[i]['width'])
    if (diff < minDiff) {
      minDiff = diff
      key = i
    }
  }
  emit('change', key)
}
</script>

<template>
  <svg
    v-if="props.gridData[config.NUM_GRID_OPTIONS]"
    ref="legendSvgEl"
    class="d-flex position-absolute z-2"
    style="cursor: pointer; top: -15px; touch-action: none"
    height="30px"
    stroke="#AAAAAA"
    stroke-width="2px"
    v-bind:id="props.panelID + '-slider'"
    v-bind:width="props.gridData[config.NUM_GRID_OPTIONS].width + 15"
    v-on:pointerdown.stop.prevent="onHandleDown"
    v-on:pointermove.stop.prevent="onHandleMove"
    v-on:pointerup.stop.prevent="onHandleUp"
  >
    <line x1="0" y1="15" v-bind:x2="props.gridData[config.NUM_GRID_OPTIONS].width" y2="15"></line>
    <line
      v-for="(grid, index) in props.gridData"
      v-bind:x1="grid.width"
      y1="8"
      v-bind:x2="grid.width"
      y2="16"
      v-bind:key="index"
    ></line>
    <circle id="handle" r="5" v-bind:cx="state.handlePosition" cy="15" stroke-width="0px" />
  </svg>
  <svg
    v-if="props.gridData[config.NUM_GRID_OPTIONS]"
    v-bind:id="props.panelID + '-legend'"
    style="cursor: pointer; opacity: 0.5"
    v-bind:width="props.gridData[gridIndex].width + 2"
    v-bind:height="props.gridData[gridIndex].width + 2"
  >
    <g stroke-width="2px" fill="#EEEEEE" stroke="#AAAAAA">
      <rect
        x="1"
        y="1"
        v-bind:width="props.gridData[gridIndex].width"
        v-bind:height="props.gridData[gridIndex].width"
      ></rect>
    </g>
  </svg>
</template>
