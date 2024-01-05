<script setup lang="ts">
import { reactive, ref, onMounted, nextTick } from 'vue'
import { Toast } from 'bootstrap'

import CMenuBar from './CMenuBar.vue'
import CPanel from './CPanel.vue'
import CChart from './CChart.vue'
import CProgressBar from './CProgressBar.vue'
import HTTP from '../lib/http'
import CartMap from '../lib/cartMap'
import type { Mappack } from '../lib/interface'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  defaultHandler: string
  cartogram_handlers: Array<{ id: string; display_name: string }> | null
  cartogram_data: any
  cartogramui_data: any
  mode: string | null
}>()

const state = reactive({
  mapkey: -1,
  currentComponent: 'map',
  isLoading: true,
  error: '',
  extendError: '',
})

// Elements
const chartEl = ref()
// Vars
var map: CartMap = new CartMap()
var cartogramResponse: any = null
var cartogram_data: any = null
var cartogramui_data: any = null
var mappack: Mappack | null = null

onMounted(async () => {
  cartogram_data = props.cartogram_data
  cartogramui_data = props.cartogramui_data
  if (cartogram_data) cartogram_data.tooltip = cartogramui_data.tooltip
  store.currentMapName = props.defaultHandler
})

/**
 * getMapMap returns an HTTP get request for all of the static data (abbreviations, original and population map
 * geometries, etc.) for a map. The progress bar is automatically updated with the download progress.
 *
 * A map pack is a JSON object containing all of this information, which used to be located in separate JSON files.
 * Combining all of this information into one file increases download speed, especially for users on mobile devices,
 * and makes it easier to display a progress bar of map information download progress, which is useful for users
 * with slow Internet connections.
 * @param {string} sysname The sysname of the map
 * @returns {Promise}
 */
async function switchMap(newmappack: Mappack) {
  //store.currentMapName
  mappack = newmappack
  map = new CartMap()  
  store.currentVersionName = map.init(mappack, cartogram_data)  
  store.versions = map.versions
  state.mapkey = Date.now()

  await nextTick()
  map.drawVersion('0-base', 'map-area', ['map-area', 'cartogram-area'])
  map.drawVersion(store.currentVersionName, 'cartogram-area', ['map-area', 'cartogram-area']) 
  cartogram_data = null 
}

function switchVersion(version: string) {
  if (!version) return
  map.switchVersion(store.currentVersionName, version, 'cartogram-area')
  store.currentVersionName = version
}

function confirmData(cartogramui_promise: Promise<any>) {  
  cartogramui_promise
    .then(async function (response: any) {
      cartogramResponse = response
      if (response.error == 'none') {
        state.currentComponent = 'chart'
        await nextTick()
        chartEl.value.drawPieChartFromTooltip(
          map.regions,
          response.tooltip,
          response.color_data
        )
      } else {
        state.error = response.error
        Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
      }
    })
    .catch(function (error: any) {
      state.error = error
      Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
    })
}

/**
 * getGeneratedCartogram generates a cartogram with the given dataset, and updates the progress bar with progress
 * information from the backend.
 * @param {string} sysname The sysname of the map
 * @param {string} areas_string The areas string of the dataset
 * @param {string} unique_sharing_key The unique sharing key returned by CartogramUI
 */
async function getGeneratedCartogram() {
  if (!mappack) return

  var sysname = store.currentMapName
  var areas_string = cartogramResponse.areas_string
  var unique_sharing_key = cartogramResponse.unique_sharing_key
  mappack.colors = cartogramResponse.color_data

  var res = await new Promise(function (resolve, reject) {
    var req_body = HTTP.serializePostVariables({
      handler: sysname,
      values: areas_string,
      unique_sharing_key: unique_sharing_key
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
      })(unique_sharing_key),
      500
    )

    HTTP.post('/cartogram', req_body, {
      'Content-type': 'application/x-www-form-urlencoded'
    }).then(
      function (response: any) {
        store.loadingProgress = 100
        window.clearInterval(progressUpdater)
        resolve(response.cartogram_data)
      },
      function () {
        window.clearInterval(progressUpdater)
        reject(Error('There was an error retrieving the cartogram from the server.'))
      }
    )
  }).catch(function (error: any) {
    state.currentComponent = 'map'
    state.error = error
    cartogramResponse = null
    Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
    return
  })

  cartogram_data = res
  cartogramui_data = cartogramResponse
  cartogram_data.tooltip = cartogramui_data.tooltip
  store.currentVersionName = '99-cartogram'
  state.currentComponent = 'map'  

  await nextTick()
  switchMap(mappack)
  cartogramResponse = null  
}

function clearEditing() {
  state.currentComponent = 'map'
  cartogramResponse = null
}
</script>

<template>
  <c-menu-bar
    v-bind:isEmbed="props.mode === 'embed'"
    v-bind:mapName="props.defaultHandler"
    v-bind:maps="props.cartogram_handlers"
    v-bind:grid_document="mappack?.griddocument"
    v-on:map_changed="switchMap"
    v-on:version_changed="switchVersion"
    v-on:confirm_data="confirmData"
  ></c-menu-bar>
  <c-progress-bar
    v-on:change="(isLoading: boolean) => (state.isLoading = isLoading)"
  />
  <div v-if="!state.isLoading" class="d-flex flex-fill p-2">
    <c-chart
      v-if="state.currentComponent === 'chart'"
      ref="chartEl"
      v-on:confirm="getGeneratedCartogram"
      v-on:cancel="clearEditing"
    />

    <c-panel
      v-else
      v-bind:key="state.mapkey"
      v-bind:map="map"
      v-bind:cartogramui_data="cartogramui_data"
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


