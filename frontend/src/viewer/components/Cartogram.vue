<script setup lang="ts">
/**
 * The main app with functions for managing components (between map panel, chart, and progress bar).
 */

import { reactive, onBeforeMount } from 'vue'

import CMenuBar from './CMenuBar.vue'
import CPanel from './CPanel.vue'
import type { MapHandlers } from '../../common/interface'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  maps: MapHandlers
  mapName?: string
  mapTitle?: string
  mapDBKey?: string
  mode?: string
}>()

const state = reactive({
  mapkey: -1,
  versionKeys: [] as Array<string>
})

onBeforeMount(() => {
  store.currentMapName = props.mapName ? props.mapName : ''
})

/**
 * Switchs the current map in the application (e.g., From Singapore to Thailand).
 * It triggers a redraw of the map.
 */
async function switchMap() {
  state.mapkey = Date.now()
  state.versionKeys = Object.keys(store.versions)
}
</script>

<template>
  <c-menu-bar
    v-bind:isEmbed="props.mode === 'embed'"
    v-bind:maps="props.maps"
    v-bind:mapTitle="props.mapTitle"
    v-bind:mapDBKey="props.mapDBKey"
    v-on:map_changed="switchMap"
  ></c-menu-bar>

  <div
    id="cartogram"
    class="d-flex flex-fill card-group"
    v-if="state.versionKeys.length > 0"
    v-bind:key="state.mapkey"
  >
    <c-panel
      v-for="index in store.options.numberOfPanels"
      v-bind:panelID="'c-area' + index.toString()"
      v-bind:defaultVersionKey="
        index === 1 ? state.versionKeys[0] : state.versionKeys[state.versionKeys.length - 1]
      "
      v-bind:stringKey="props.mapDBKey"
    />
  </div>
</template>
