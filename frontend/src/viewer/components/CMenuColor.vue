<script setup lang="ts">
import { onMounted } from 'vue'
import * as visualization from '../lib/visualization'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const choroVersions = window.CARTOGRAM_CONFIG.choroVersions

onMounted(async () => {
  await visualization.initLegend()
})

async function updateVis() {
  await visualization.initLegend()
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
          v-for="(versionItem, versionKey) in choroVersions"
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
