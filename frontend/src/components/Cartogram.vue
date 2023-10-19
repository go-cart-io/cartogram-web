<script setup lang="ts">
import { reactive, ref, onMounted, nextTick } from 'vue'
import { Toast } from 'bootstrap'

import HTTP from '../lib/http'
import CartogramUI from './CartogramUI.vue'
import CartogramUploadBtn from './CartogramUploadBtn.vue'
import CartogramChart from './CartogramChart.vue'
import CartogramEdit from './CartogramEdit.vue'
import ProgressBar from './ProgressBar.vue'
import type { Mappack } from '../lib/interface'
import { Region } from '../lib/region'
import shareState from '../lib/state'
import tracker from '../lib/tracker'
import config from '../lib/config'

const CONFIG = { version: 'devel' }
var detectTasks = [
  'test4',
  'test6',
  'test58',
  'test34',
  'test117',
  'test130',
  'test138',
  'test18',
  'test21',
  'test105',
  'test64'
]

const props = defineProps<{
  defaultHandler: string
  cartogram_handlers: Array<{ id: string; display_name: string }> | null
  cartogram_data: any
  cartogramui_data: any
  mode: string | null
}>()

const state = reactive({
  currentComponent: 'map',
  isLoading: true,
  isLoaded: false,
  isPlaying: false,
  error: '',
  extendError: '',
  versions: {} as { [key: string]: any }
})

// Form values
var selectedHandler = props.defaultHandler
// Elements
const progressBarEl = ref()
const cartogramUIEl = ref()
const cartogramChartEl = ref()
// Vars
var cartogramResponse: any = null
var cartogram_data: any = null
var cartogramui_data: any = null
var mappack: Mappack | null = null
var regions: { [key: string]: Region } | null = null
let urlParams: URLSearchParams

onMounted(async () => {
  urlParams = new URLSearchParams(window.location.search)
  tracker.start()
  tracker.setUserID(urlParams.get('pid'))

  cartogram_data = props.cartogram_data
  cartogramui_data = props.cartogramui_data
  await getMapPack()
  state.isLoaded = true // to prevent rendering map without mappack
  await nextTick()
  regions = cartogramUIEl.value.getRegions()
  state.versions = cartogramUIEl.value.getVersions()

  if (urlParams.get('zoom') === '0') shareState.options.zoomable = false
  else shareState.options.zoomable = true
  if (urlParams.get('rotate') === '0') shareState.options.rotatable = false
  else shareState.options.rotatable = true
  if (urlParams.get('stretch') === '0') shareState.options.stretchable = false
  else shareState.options.stretchable = true
  tracker.setMeta(
    'features_set',
    shareState.options.zoomable +
      ':' +
      shareState.options.rotatable +
      ':' +
      shareState.options.stretchable
  )
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
async function getMapPack() {
  mappack = (await HTTP.get(
    '/static/cartdata/' + selectedHandler + '/mappack.json?v=' + CONFIG.version,
    null,
    function (e: any) {
      progressBarEl.value.setValue(Math.floor((e.loaded / e.total) * 100))
    }
  )) as Mappack

  tracker.setMap(selectedHandler)
  if (urlParams.get('pid')) {
    ;[shareState.options.zoomable, shareState.options.rotatable, shareState.options.stretchable] =
      config(urlParams.get('pid')!, selectedHandler)
  }
}

async function switchMap() {
  await getMapPack()
  cartogramUIEl.value.switchMap(mappack)
  regions = cartogramUIEl.value.getRegions()
  state.versions = cartogramUIEl.value.getVersions()
}

function playVersions() {
  state.isPlaying = true
  let keys = Object.keys(state.versions)
  let i = 0
  cartogramUIEl.value.switchVersion(keys[i++])
  let interval = setInterval(function () {
    cartogramUIEl.value.switchVersion(keys[i++])
    if (i >= keys.length) {
      clearInterval(interval)
      state.isPlaying = false
    }
  }, 1000)
}

function confirmData(cartogramui_promise: Promise<any>) {
  cartogramui_promise
    .then(async function (response: any) {
      cartogramResponse = response
      if (response.error == 'none') {
        state.currentComponent = 'chart'
        await nextTick()
        cartogramChartEl.value.drawPieChartFromTooltip(
          regions,
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

  var sysname = selectedHandler
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
                progressBarEl.value.setValue(8)
                return
              }

              let percentage = Math.floor(progress.progress * 100)
              progressBarEl.value.setValue(percentage)
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
        progressBarEl.value.setValue(100)
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

  state.currentComponent = 'map'
  shareState.current_sysname = '99-cartogram'
  await nextTick()
  cartogramResponse = null
  state.versions = cartogramUIEl.value.getVersions()
}

function clearEditing() {
  state.currentComponent = 'map'
  cartogramResponse = null
}
</script>

<template>
  <nav class="navbar bg-light p-0">
    <div class="w-100 mw-100 d-flex align-items-start">
      <div class="p-2" v-if="mode === 'embed'">
        <img src="/static/img/gocart_final.svg" width="100" alt="go-cart.io logo" />
      </div>

      <div v-if="mode !== 'embed'" class="p-2" style="max-width: 30%">
        <!--label for="handler">Map:</label-->
        <div class="d-flex">
          <select
            class="form-select"
            id="handler"
            v-model="selectedHandler"
            v-on:change="switchMap"
          >
            <option v-for="handler in props.cartogram_handlers" v-bind:value="handler.id">
              {{ handler.display_name }}
            </option>
          </select>
          <a
            class="btn btn-primary ms-2"
            title="Download template"
            v-bind:href="'/static/cartdata/' + selectedHandler + '/template.csv'"
          >
            <i class="fas fa-file-download"></i>
          </a>
        </div>
      </div>

      <div
        v-if="cartogramUIEl"
        class="btn-group d-flex flex-shrink-1 p-2"
        style="min-width: 40px"
        role="group"
        aria-label="Data"
      >
        <!--button
          class="btn btn-primary"
          v-on:click="playVersions()"
          v-bind:disabled="state.isPlaying"
        >
          <i class="fas fa-play"></i>
        </button-->
        <button
          v-for="(version, index) in state.versions"
          type="button"
          class="btn btn-outline-primary version"
          v-bind:class="{ active: shareState.current_sysname === index.toString() }"
          v-bind:disabled="detectTasks.indexOf(selectedHandler) < 0 && version.name === '2016'"
          v-on:click="cartogramUIEl.switchVersion(index.toString())"
        >
          {{ version.name }}
          <i
            class="fas fa-check"
            v-if="
              Object.keys(state.versions).length === 2 &&
              shareState.current_sysname === index.toString()
            "
          ></i>
        </button>
      </div>

      <!-- Menu -->
      <div class="py-2 d-flex flex-nowrap">
        <span v-if="cartogramUIEl && mappack && mode !== 'embed'" class="text-nowrap">
          <CartogramUploadBtn :sysname="selectedHandler" v-on:change="confirmData" />
          <CartogramEdit
            :grid_document="mappack.griddocument"
            :sysname="selectedHandler"
            v-on:change="confirmData"
          />
        </span>
        <span v-else-if="mode !== 'embed'" class="text-nowrap">
          <button type="button" class="btn btn-primary disabled me-2" title="Upload data">
            <i class="fas fa-file-upload"></i>
          </button>
          <button type="button" class="btn btn-primary disabled me-2" title="Edit data">
            <i class="far fa-edit"></i>
          </button>
        </span>

        <!-- <div class="dropdown me-2">
          <button
            class="btn btn-primary dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown"
            aria-expanded="false"
            title="Customization"
          >
            <i class="fas fa-cog"></i>
          </button>
          <div class="dropdown-menu dropdown-menu-end p-2 container" style="width: 220px">
            <div class="row">
              <div class="col-auto">
                <label class="form-check-label" for="gridline-toggle-cartogram"
                  >Show grid lines</label
                >
              </div>
              <div class="col text-end">
                <input
                  type="checkbox"
                  class="form-check-input"
                  v-model="shareState.options.showGrid"
                />
              </div>
            </div>

            <div class="row">
              <div class="col-auto">
                <label class="form-check-label" for="gridline-toggle-cartogram"
                  >Show base map</label
                >
              </div>
              <div class="col text-end">
                <input
                  type="checkbox"
                  class="form-check-input"
                  v-model="shareState.options.showBase"
                />
              </div>
            </div>

            <div class="row">
              <div class="col-auto">
                <label class="form-check-label" for="gridline-toggle-cartogram">Zoomable</label>
              </div>
              <div class="col text-end">
                <input
                  type="checkbox"
                  class="form-check-input"
                  v-model="shareState.options.zoomable"
                />
              </div>
            </div>

            <div class="row">
              <div class="col-auto">
                <label class="form-check-label" for="gridline-toggle-cartogram">Rotatable</label>
              </div>
              <div class="col text-end">
                <input
                  type="checkbox"
                  class="form-check-input"
                  v-model="shareState.options.rotatable"
                />
              </div>
            </div>

            <div class="row">
              <div class="col-auto">
                <label class="form-check-label" for="gridline-toggle-cartogram">Stretchable</label>
              </div>
              <div class="col text-end">
                <input
                  type="checkbox"
                  class="form-check-input"
                  v-model="shareState.options.stretchable"
                />
              </div>
            </div>
          </div>
        </div> -->

        You can pan {{ shareState.options.zoomable ? ', zoom' : '' }}
        {{ shareState.options.rotatable ? ', rotate' : '' }}
        {{ shareState.options.stretchable ? ', stretch' : '' }}
      </div>
    </div>
  </nav>
  <ProgressBar
    ref="progressBarEl"
    v-on:change="(isLoading: boolean) => (state.isLoading = isLoading)"
  />
  <div v-if="!state.isLoading && state.isLoaded" class="d-flex flex-fill p-2">
    <CartogramChart
      v-if="state.currentComponent === 'chart'"
      ref="cartogramChartEl"
      v-on:confirm="getGeneratedCartogram"
      v-on:cancel="clearEditing"
    />

    <CartogramUI
      v-else
      ref="cartogramUIEl"
      v-bind:handler="selectedHandler"
      v-bind:mappack="mappack"
      v-bind:cartogram_data="cartogram_data"
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

<style>
button.version {
  min-width: 0;
  padding: 0.4rem 1px;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
