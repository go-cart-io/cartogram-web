<script setup lang="ts">
/**
 * The main app with functions for managing components (between map panel, chart, and progress bar).
 */

import { reactive, ref, onBeforeMount, nextTick } from 'vue'
import { Toast } from 'bootstrap'

import CMenuBar from './CMenuBar.vue'
import CPanel from './CPanel.vue'
import CChart from './CChart.vue'
import CProgressBar from './CProgressBar.vue'
import HTTP from '../lib/http'
import * as util from '../lib/util'
import CartMap from '../lib/cartMap'
import type { MapHandlers, Mappack, DataTable } from '../lib/interface'

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

// Elements
const chartEl = ref()
// Vars
var map: CartMap = new CartMap()
var tempDataTable: any = null
var mappack: Mappack | null = null

onBeforeMount(() => {
  store.currentMapName = props.mapName
  store.stringKey = props.mapDataKey
})

/**
 * Switchs the current map in the application (e.g., From Singapore to Thailand).
 * It initializes the new map, updates the current version, and triggers a redraw of the map.
 * @param {Mappack} newmappack The new map pack to switch to.
 */
async function switchMap(newmappack: Mappack) {
  mappack = newmappack
  map = new CartMap()
  store.currentVersionName = map.init(mappack)
  store.versions = map.versions
  state.mapkey = Date.now()

  redraw()
}

/**
 * Redraws the map and updating the current component to 'map'.
 * It uses the nextTick function to ensure that the DOM has been updated before redrawing the map.
 */
async function redraw() {
  state.currentComponent = 'map'

  await nextTick()
  map.drawVersion('0-base', 'map-area', ['map-area', 'cartogram-area'])
  map.drawVersion(store.currentVersionName, 'cartogram-area', ['map-area', 'cartogram-area'])
  tempDataTable = null
}

/**
 * Switchs the current version of the map in the application (e.g., from Area to Population).
 * It takes a version parameter and updates the current version name in the store.
 * It also calls the switchVersion method of the CartMap instance to switch the version of the map being displayed.
 * @param {String} version The new version of the map to switch to.
 */
function switchVersion(version: string) {
  if (!version) return
  map.switchVersion(store.currentVersionName, version, 'cartogram-area')
  store.currentVersionName = version
}

/**
 * Updates the state and triggering the drawing of a pie chart based on the provided data
 * to let users confirm that the data makes sense.
 * @param {DataTable} data A DataTable object containing the data for the pie chart.
 */
async function confirmData(data: DataTable) {
  tempDataTable = data
  state.currentComponent = 'chart'
  await nextTick()

  chartEl.value.drawPieChart(data)
}

/**
 * Generates a cartogram with the given dataset, and updates the progress bar with progress
 * information from the backend.
 */
async function getGeneratedCartogram() {
  var stringKey = util.generateShareKey(32)
  var newmappack = await new Promise<Mappack>(function (resolve, reject) {
    var req_body =
      'data=' +
      JSON.stringify({
        handler: store.currentMapName,
        values: tempDataTable,
        stringKey: stringKey
      })

    var progressUpdater = window.setInterval(
      (function (key) {
        return function () {
          HTTP.get('/getprogress?key=' + encodeURIComponent(key) + '&time=' + Date.now()).then(
            function (progress: any) {
              if (progress.progress === null) {
                store.loadingProgress = 8
                return
              }

              store.loadingProgress = Math.floor(progress.progress * 100)
              // state.error += progress.stderr
            }
          )
        }
      })(stringKey),
      500
    )

    HTTP.post('/cartogram', req_body, {
      'Content-type': 'application/x-www-form-urlencoded'
    }).then(
      function (response: any) {
        store.loadingProgress = 100
        window.clearInterval(progressUpdater)
        resolve(response)
      },
      function (error: any) {
        window.clearInterval(progressUpdater)
        reject(error)
      }
    )
  }).catch(function (error: any) {
    state.currentComponent = 'map'
    state.error = error
    tempDataTable = null
    Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
    redraw()
    return
  })

  state.currentComponent = 'map'
  if (newmappack) store.stringKey = newmappack.stringKey
  await nextTick()
  if (newmappack) switchMap(newmappack)
  tempDataTable = null
}
</script>

<template>
  <c-menu-bar
    v-bind:isEmbed="props.mode === 'embed'"
    v-bind:maps="props.maps"
    v-bind:map="map"
    v-on:map_changed="switchMap"
    v-on:version_changed="switchVersion"
    v-on:confirm_data="confirmData"
  ></c-menu-bar>
  <c-progress-bar v-on:change="(isLoading: boolean) => (state.isLoading = isLoading)" />
  <div v-if="!state.isLoading" class="d-flex flex-fill p-2">
    <c-chart
      v-if="state.currentComponent === 'chart'"
      ref="chartEl"
      v-on:confirm="getGeneratedCartogram"
      v-on:cancel="redraw"
    />

    <c-panel v-else v-bind:key="state.mapkey" v-bind:map="map" v-bind:mode="props.mode" />
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
