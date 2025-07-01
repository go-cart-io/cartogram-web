<script setup lang="ts">
import { onMounted } from 'vue'
import * as visualization from '../../common/visualization'
import * as util from '../lib/util'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

onMounted(async () => {
  await updateVis()
})

async function updateVis() {
  let csvUrl = util.getCsvURL(store.currentMapName, CARTOGRAM_CONFIG.mapDBKey)
  await visualization.initLegend(
    csvUrl,
    store.currentColorCol,
    CARTOGRAM_CONFIG.cartoColorScheme,
    CARTOGRAM_CONFIG.choroSpec
  )
}
</script>

<template>
  <div class="d-flex flex-fill py-2 pe-2" style="min-width: 400px">
    <!-- Color selection -->
    <div class="input-group pe-2" style="max-width: 200px">
      <span class="input-group-text">By</span>
      <select
        id="color-options"
        class="form-select"
        title="Select map/cartogram color strategy"
        v-model="store.currentColorCol"
        v-on:change="updateVis"
      >
        <option value="Region">Region</option>
        <option
          v-for="(versionItem, versionKey) in CARTOGRAM_CONFIG.choroVersions"
          v-bind:value="versionItem.header"
          v-bind:key="versionKey"
        >
          {{ versionItem.name }}
        </option>
      </select>
    </div>

    <div id="legend" class="flex-grow-1"></div>
  </div>
</template>
