<script setup lang="ts">
/**
 * The main app with functions for managing components (between map panel, chart, and progress bar).
 */

import { reactive, onBeforeMount } from 'vue'

import CMenuBar from './CMenuBar.vue'
import CPanel from '../../common/components/CPanel.vue'
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
  mapkey: -1
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
}
</script>

<template>
  <c-menu-bar
    v-bind:isEmbed="props.mode === 'embed'"
    v-bind:maps="props.maps"
    v-on:map_changed="switchMap"
    v-on:version_changed="(version: string) => (store.currentVersionName = version)"
  ></c-menu-bar>

  <c-panel
    v-if="store.versions && store.currentVersionName"
    v-bind:key="state.mapkey"
    v-bind:currentMapName="store.currentMapName"
    v-bind:currentVersionKey="store.currentVersionName"
    v-bind:versions="store.versions"
    v-bind:stringKey="store.stringKey"
    v-bind:showBase="store.options.showBase"
    v-bind:showGrid="store.options.showGrid"
    v-bind:mode="props.mode"
  />
</template>
