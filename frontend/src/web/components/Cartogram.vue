<script setup lang="ts">
/**
 * The main app with functions for managing components (between map panel, chart, and progress bar).
 */

import { reactive, onBeforeMount } from 'vue'

import CMenuBar from './CMenuBar.vue'
import CPanel from '../../common/components/CPanel.vue'
import CProgressBar from './CProgressBar.vue'
import type { MapHandlers } from '../../common/lib/interface'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  mapName: string
  maps: MapHandlers
  mapDataKey: string
  mode: string | null
}>()

const state = reactive({
  mapkey: -1,
  currentComponent: 'map',
  isLoading: true,
  error: '',
  extendError: ''
})

onBeforeMount(() => {
  store.currentMapName = props.mapName
  store.stringKey = props.mapDataKey
})

/**
 * Switchs the current map in the application (e.g., From Singapore to Thailand).
 * It triggers a redraw of the map.
 */
async function switchMap() {
  state.mapkey = Date.now()
  redraw()
}

/**
 * Redraws the map and updating the current component to 'map'.
 * It uses the nextTick function to ensure that the DOM has been updated before redrawing the map.
 */
async function redraw() {
  state.currentComponent = 'map'
}
</script>

<template>
  <c-menu-bar
    v-bind:isEmbed="props.mode === 'embed'"
    v-bind:maps="props.maps"
    v-on:map_changed="switchMap"
    v-on:version_changed="(version: string) => (store.currentVersionName = version)"
  ></c-menu-bar>
  <c-progress-bar v-on:change="(isLoading: boolean) => (state.isLoading = isLoading)" />
  <div v-if="!state.isLoading" class="d-flex flex-fill p-2">
    <c-panel
      v-bind:key="state.mapkey"
      v-bind:currentMapName="store.currentMapName"
      v-bind:currentVersionKey="store.currentVersionName"
      v-bind:versions="store.versions"
      v-bind:stringKey="store.stringKey"
      v-bind:showBase="store.options.showBase"
      v-bind:showGrid="store.options.showGrid"
      v-bind:mode="props.mode"
    />
  </div>

  <div
    id="errorToast"
    class="toast toast position-absolute end-0 bottom-0 m-3 text-bg-danger"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    data-bs-autohide="false"
  >
    <div class="d-flex">
      <div class="toast-body">{{ state.error }}</div>
      <button
        type="button"
        class="btn-close me-2 m-auto"
        data-bs-dismiss="toast"
        aria-label="Close"
      ></button>
    </div>
  </div>
</template>
