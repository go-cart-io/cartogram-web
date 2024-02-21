<script setup lang="ts">
import { reactive, ref } from 'vue'
import { Toast } from 'bootstrap'

import CMenuBtnUpload from './CMenuBtnUpload.vue'

import * as util from '../lib/util'
import HTTP from '../lib/http'
import type { DataTable, MapHandlers, Mappack } from '../lib/interface'

var data: any = {}
var tempDataTable: DataTable | null = null

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  maps: MapHandlers
}>()

const state = reactive({
  error: '',
  mapName: '',
  geojsonFileName: ''
})

store.loadingProgress = 100

async function uploadGeoJson(event: Event) {
  const files = (event.target as HTMLInputElement).files
  if (!files) return

  async function readFile(file: File) {
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsText(file)
      reader.onload = () => resolve(<string>reader.result)
      reader.onerror = (error) => reject(error)
    })
  }

  var mapData = await readFile(files[0])
  data['mapData'] = JSON.parse(mapData)
  state.geojsonFileName = files[0].name
  state.mapName = ''
}

function uploadData(data: DataTable) {
  tempDataTable = data
  getGeneratedCartogram()
}

async function getGeneratedCartogram() {
  var stringKey = util.generateShareKey(32)
  var newmappack = await new Promise<Mappack>(function (resolve, reject) {
    data['handler'] = state.mapName
    data['values'] = tempDataTable
    data['stringKey'] = stringKey

    var req_body = 'data=' + JSON.stringify(data)

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
    state.error = error
    tempDataTable = null
    Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
    return
  })

  tempDataTable = null
  console.log(newmappack)
}
</script>

<template>
  {{ store.loadingProgress }}
  <select class="form-select" v-model="state.mapName">
    <option></option>
    <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey">
      {{ mapItem.name }}
    </option>
  </select>

  <label for="geojson" class="btn btn-primary">
    {{ state.geojsonFileName ? state.geojsonFileName : 'Upload GeoJson file' }}
  </label>
  <input
    id="geojson"
    class="d-none"
    type="file"
    accept="application/json,.json,.geojson"
    v-on:change="uploadGeoJson"
  />

  <c-menu-btn-upload v-on:change="uploadData" />

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
