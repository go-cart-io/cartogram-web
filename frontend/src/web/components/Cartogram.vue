<script setup lang="ts">
/**
 * The main app with functions for managing components (between map panel, chart, and progress bar).
 */

import { reactive, ref, onBeforeMount, nextTick } from 'vue'
import { Toast } from 'bootstrap'

import CMenuBar from './CMenuBar.vue'
import CPanel from '../../common/components/CPanel.vue'
import CChart from './CChart.vue'
import CProgressBar from './CProgressBar.vue'
import HTTP from '../lib/http'
import type { MapHandlers } from '../../common/lib/interface'
import type { DataTable } from '../lib/interface'

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
var tempDataTable: any = null

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
  tempDataTable = null
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
  // https://stackoverflow.com/questions/1349404/generate-random-string-characters-in-javascript
  function generateShareKey(length: number): string {
    let result = Date.now().toString()
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    const charactersLength = characters.length
    let counter = result.length
    while (counter < length) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength))
      counter += 1
    }
    return result
  }

  var stringKey = generateShareKey(32)
  await new Promise<any>(function (resolve, reject) {
    var req_body =
      'data=' +
      JSON.stringify({
        handler: store.currentMapName,
        values: tempDataTable,
        stringKey: stringKey,
        persist: true
      })

    var progressUpdater = window.setInterval(
      (function (key) {
        return function () {
          HTTP.get(
            '/api/v1/getprogress?key=' + encodeURIComponent(key) + '&time=' + Date.now()
          ).then(function (progress: any) {
            if (progress.progress === null) {
              store.loadingProgress = 8
              return
            }

            store.loadingProgress = Math.floor(progress.progress * 100)
            // state.error += progress.stderr
            console.log(progress.stderr)
          })
        }
      })(stringKey),
      500
    )

    HTTP.post('/api/v1/cartogram', req_body, {
      'Content-type': 'application/x-www-form-urlencoded'
    }).then(
      function (response: any) {
        store.loadingProgress = 100
        window.clearInterval(progressUpdater)
        resolve(response)
        window.location.href = '/cartogram/key/' + response.stringKey + '/preview'
      },
      function (error: any) {
        store.loadingProgress = 100
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
}
</script>

<template>
  <c-menu-bar
    v-bind:isEmbed="props.mode === 'embed'"
    v-bind:maps="props.maps"
    v-on:map_changed="switchMap"
    v-on:version_changed="(version: string) => (store.currentVersionName = version)"
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

    <c-panel
      v-else
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
