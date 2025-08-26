<script setup lang="ts">
import { onMounted } from 'vue'
import * as visualization from '../../common/visualization'
import * as util from '../lib/util'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG
const choroLenght = Object.keys(CARTOGRAM_CONFIG.choroVersions).length

async function updateVis() {
  let csvUrl = util.getCsvURL(store.currentMapName, CARTOGRAM_CONFIG.mapDBKey)
  await visualization.initLegendWithURL(
    csvUrl,
    store.currentColorCol,
    CARTOGRAM_CONFIG.cartoColorScheme,
    CARTOGRAM_CONFIG.choroSpec
  )
}
</script>

<template>
  <div v-if="choroLenght > 0" class="order-last order-sm-2 flex-grow-1" style="min-width: 250px">
    <div class="container">
      <div class="row">
        <!-- Color selection -->
        <div class="col-4 p-0 pe-2">
          <div class="input-group flex-nowrap">
            <span class="input-group-text">By</span>
            <select
              id="color-options"
              class="form-select"
              title="Select map/cartogram color strategy"
              v-model="store.currentColorCol"
              v-on:change="updateVis"
            >
              <option value="Region">Region</option>
              <option disabled>Data:</option>
              <option
                v-for="(versionItem, versionKey) in CARTOGRAM_CONFIG.choroVersions"
                v-bind:value="versionItem.header"
                v-bind:key="versionKey"
              >
                &nbsp;&nbsp;{{ versionItem.header }}
              </option>
            </select>
          </div>
        </div>

        <div id="legend" class="col-8 p-0"></div>
      </div>
    </div>
  </div>
</template>
