<script setup lang="ts">
import type { View } from 'vega'
import { onMounted, reactive } from 'vue'

import * as visualization from '../lib/visualization'
import { useTransform } from '../composables/useTransform'
import CTouchVis from './CTouchVis.vue'

const SUPPORT_TOUCH = 'ontouchstart' in window || navigator.maxTouchPoints
let visView = null as View | null

// Props: colorFields (available color columns), currentColorCol (selected column)
const props = defineProps<{
  panelID: string
}>()

const transform = useTransform(props.panelID)

const state = reactive({
  cursor: 'grab',
  isLockRatio: true,
  stretchDirection: 'x'
})

// Emits: 'transformChanged' event when transformation matrix changes
const emit = defineEmits(['transformChanged'])

// Expose methods for parent components
defineExpose({
  transform,
  view,
  reset,
  initWithURL,
  initWithValues,
  resize
})

function view(): View | null {
  return visView
}

function reset(): void {
  visualization.reset(props.panelID + '-vis')
  visualization.reset(props.panelID + '-offscreen')
}

/**
 * Initialize visualization using a URL (delegates to visualization helper)
 */
async function initWithURL(...args: Parameters<typeof visualization.initWithURL>) {
  visView = await visualization.initWithURL(...args)
}

/**
 * Initialize visualization using explicit values (delegates to visualization helper)
 */
async function initWithValues(...args: Parameters<typeof visualization.initWithValues>) {
  visView = await visualization.initWithValues(...args)
}

/**
 * Resize the legend to fit its container
 */
async function resize() {
  if (!visView || !visView.container()) return
  await visView.resize()
  await visView.width(visView.container()!.offsetWidth).runAsync()
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
</script>

<template>
  <div class="position-relative w-100 h-100">
    <c-touch-vis
      v-bind:key="transform.stateLastMove.value"
      v-bind:touchInfo="transform.touchInfo"
      v-bind:touchLenght="transform.stateTouchLenght.value"
    />

    <div
      class="position-absolute w-100 h-100"
      style="touch-action: none"
      v-bind:id="props.panelID"
      v-bind:style="{ cursor: state.cursor }"
      v-on:pointerdown.stop.prevent="
        ($event) => {
          transform.onPointerdown($event)
          emit('transformChanged', transform)
        }
      "
      v-on:pointermove.stop.prevent="
        ($event) => {
          transform.onPointermove($event, state.isLockRatio)
          emit('transformChanged', transform)
        }
      "
      v-on:pointerup.stop.prevent="
        ($event) => {
          transform.onPointerup($event)
          emit('transformChanged', transform)
        }
      "
      v-on:pointercancel.stop.prevent="
        ($event) => {
          transform.onPointerup($event)
          emit('transformChanged', transform)
        }
      "
      v-on:wheel.stop.prevent="
        ($event) => {
          transform.onWheel($event, state.isLockRatio, state.stretchDirection)
          emit('transformChanged', transform)
        }
      "
    >
      <div style="mix-blend-mode: multiply">
        <div v-bind:id="props.panelID + '-vis'" class="vis-area w-100 h-100"></div>
        <div v-bind:id="props.panelID + '-offscreen'" class="vis-area offscreen w-100 h-100"></div>
      </div>
      <slot></slot>
    </div>

    <div class="position-absolute end-0" style="width: 2.5rem">
      <button
        class="btn btn-secondary w-100 my-1"
        v-on:click="switchMode()"
        v-bind:title="state.isLockRatio ? 'Switch to free transform' : 'Switch to lock ratio'"
      >
        <i v-if="transform.stateTouchLenght.value === 3" class="fas fa-unlock"></i>
        <i v-else-if="state.isLockRatio" class="fas fa-lock"></i>
        <i v-else-if="SUPPORT_TOUCH" class="fas fa-unlock"></i>
        <i v-else-if="state.stretchDirection === 'x'" class="fas fa-arrows-alt-h"></i>
        <i v-else class="fas fa-arrows-alt-v"></i>
      </button>
      <button class="btn btn-secondary w-100 my-1" v-on:click="transform.reset()" title="Reset">
        <i class="fas fa-crosshairs"></i>
      </button>
    </div>
  </div>
</template>

<style>
.vis-area {
  position: absolute !important;
  min-height: 100px;
  user-select: none;
}

.vis-area.offscreen {
  opacity: 0;
  pointer-events: none;
}

g.root {
  transform-origin: center;
}
</style>
