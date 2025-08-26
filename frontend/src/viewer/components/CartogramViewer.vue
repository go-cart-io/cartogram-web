<script setup lang="ts">
/**
 * The main app with functions for managing components (between map panel, chart, and progress bar).
 */

import { reactive, onBeforeMount } from 'vue'

import CMenuBar from './CMenuBar.vue'
import CPanel from './CPanel.vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

const state = reactive({
  mapkey: -1,
  versionKeys: [] as Array<string>
})

onBeforeMount(() => {
  store.currentMapName = CARTOGRAM_CONFIG.mapName ? CARTOGRAM_CONFIG.mapName : ''
})

/**
 * Switchs the current map in the application (e.g., From Singapore to Thailand).
 * It triggers a redraw of the map.
 */
async function switchMap() {
  state.mapkey = Date.now()
  state.versionKeys = Object.keys(CARTOGRAM_CONFIG.cartoVersions)
}
</script>

<template>
  <c-menu-bar v-on:map_changed="switchMap"></c-menu-bar>

  <div
    id="cartogram"
    class="d-flex flex-fill card-group position-relative mx-2"
    v-if="state.versionKeys.length > 0"
    v-bind:key="state.mapkey"
  >
    <c-panel
      v-for="index in store.options.numberOfPanels"
      v-bind:panelID="'c-area' + index.toString()"
      v-bind:defaultVersionKey="
        store.options.numberOfPanels === 1
          ? state.versionKeys[state.versionKeys.length - 1]
          : index === 1
            ? state.versionKeys[0]
            : state.versionKeys[state.versionKeys.length - 1]
      "
      v-bind:key="index"
    />
  </div>
</template>
