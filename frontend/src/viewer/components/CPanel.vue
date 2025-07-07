<script setup lang="ts">
/**
 * The map panel with functions for interactivity to manipulate viewport.
 */

import { ref, reactive } from 'vue'

import CPanelLegend from './CPanelLegend.vue'
import CPanelSelectVersion from './CPanelSelectVersion.vue'
import CPanelBtnDownload from './CPanelBtnDownload.vue'
import CTouchVis from './CTouchVis.vue'
import { useTransform } from '../composables/useTransform'

const SUPPORT_TOUCH = 'ontouchstart' in window || navigator.maxTouchPoints

const legendEl = ref()

const props = defineProps<{
  panelID: string
  defaultVersionKey: string
}>()

const state = reactive({
  versionKey: props.defaultVersionKey,
  cursor: 'grab',
  isLockRatio: true,
  stretchDirection: 'x'
})

const transform = useTransform(legendEl, props.panelID)

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
  <div class="card w-100">
    <div class="d-flex flex-column card-body">
      <c-panel-legend
        ref="legendEl"
        style="touch-action: none"
        v-bind:style="{ cursor: state.cursor }"
        v-bind:panelID="props.panelID"
        v-bind:versionKey="state.versionKey"
        v-bind:affineScale="transform.stateAffineScale.value"
        v-on:gridChanged="transform.snapToBetterNumber"
        v-on:pointerdown.stop.prevent="transform.onPointerdown"
        v-on:pointermove.stop.prevent="transform.onPointermove($event, state.isLockRatio)"
        v-on:pointerup.stop.prevent="transform.onPointerup"
        v-on:pointercancel.stop.prevent="transform.onPointerup"
        v-on:wheel.stop.prevent="
          transform.onWheel($event, state.isLockRatio, state.stretchDirection)
        "
        v-on:versionUpdated="transform.applyCurrent()"
      >
        <img class="position-absolute bottom-0 end-0 z-3" src="/static/img/by.svg" alt="cc-by" />
      </c-panel-legend>
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

    <div class="card-footer d-flex justify-content-between">
      <c-panel-select-version
        v-bind:panelID="props.panelID"
        v-bind:currentVersionName="state.versionKey"
        v-on:version_changed="(version) => (state.versionKey = version)"
      />
      <c-panel-btn-download v-bind:versionKey="state.versionKey" v-bind:panelID="props.panelID" />
    </div>
  </div>

  <c-touch-vis
    v-bind:key="transform.stateLastMove.value"
    v-bind:touchInfo="transform.touchInfo"
    v-bind:touchLenght="transform.stateTouchLenght.value"
  />
</template>
