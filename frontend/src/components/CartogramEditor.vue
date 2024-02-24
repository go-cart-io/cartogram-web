<script setup lang="ts">
import { reactive, onBeforeMount } from 'vue'
import { Toast } from 'bootstrap'

import CBtnUploadCsv from './editor/CBtnUploadCsv.vue'

import * as util from '../lib/util'
import HTTP from '../lib/http'
import type { DataTable, MapHandlers, Mappack } from '../lib/interface'

var data: any = {}
var tempCSVData: any = null

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  maps: MapHandlers
}>()

const state = reactive({
  error: '',
  mapName: '',
  geojsonFileName: '',
  fieldKeys: [] as string[],
  mapFieldKeys: [] as string[],
  dataTable: {} as DataTable,
  selectedFieldKeys: [] as string[],
  mapRegionKey: ''
})

onBeforeMount(() => {
  reset()
})

function reset() {
  state.mapName = 'custom'
  state.fieldKeys = []
  state.mapFieldKeys = []

  state.dataTable.fields = [
    { key: 'region', label: 'Region', editable: true, type: 'text' },
    { key: 'abbr', label: 'Abbrivation', editable: true, type: 'text' },
    { key: 'color', label: 'Colour', editable: true, type: 'color' },
    {
      key: '0',
      label: 'Area',
      unit: 'sq.m.',
      editable: true,
      type: 'number',
      headerEditable: true
    },
    {
      key: 'value',
      label: 'Value',
      unit: 'unit',
      editable: true,
      type: 'number',
      headerEditable: true
    }
  ]
  state.dataTable.items = {}
  state.selectedFieldKeys = Array(state.dataTable.fields.length).fill('')
}

function initDataTableRows(length: number) {
  for (var id = 0; id < length; id++) {
    state.dataTable.items[id] = ['', '', '#eeeeee', 0, 0]
  }
}

function uploadData(data: any) {
  tempCSVData = data
  var mapFieldKeys = Object.keys(data[0]).map((item) => 'file:' + item)
  state.mapFieldKeys.push(...mapFieldKeys)

  console.log(data)
}

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

  if (!data['mapData'].features) return // TODO: error warning

  state.geojsonFileName = files[0].name
  var mapFieldKeys = Object.keys(data['mapData'].features[0].properties)

  for (var id = 0; id < data['mapData'].features.length; id++) {
    console.log(data['mapData'].features[id].properties)
    state.dataTable.items[id] = [
      data['mapData'].features[id].properties[mapFieldKeys[0]],
      data['mapData'].features[id].properties[mapFieldKeys[0]],
      '#eeeeee',
      0,
      0
    ]
  }

  state.mapFieldKeys = mapFieldKeys.map((item) => 'map:' + item)
  state.fieldKeys.push(...state.mapFieldKeys)
  state.selectedFieldKeys[0] = state.mapFieldKeys[0]
  state.selectedFieldKeys[1] = state.mapFieldKeys[0]
}

function generateDataTable() {
  // tempCSVData data['mapData']
}

function updateDataTable(index: number) {
  var keyInfo = state.selectedFieldKeys[index].split(':')
  for (var id = 0; id < data['mapData'].features.length; id++) {
    state.dataTable.items[id][index] =
      keyInfo[0] === 'map' ? data['mapData'].features[id].properties[keyInfo[1]] : ''
  }
}

async function getGeneratedCartogram() {
  var stringKey = util.generateShareKey(32)
  var newmappack = await new Promise<Mappack>(function (resolve, reject) {
    data['handler'] = state.mapName
    data['values'] = tempCSVData
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
    tempCSVData = null
    Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
    return
  })

  tempCSVData = null
  console.log(newmappack)
}
</script>

<template>
  <div class="d-flex flex-fill card-group p-2">
    <div class="card w-100">
      <div class="p-2">
        <div class="badge text-bg-secondary">1. Import your data</div>

        <div class="row p-2">
          Import data from csv or Excel file. You may skip this step if your data is only in GeoJson
          file or you want to input data manually.
        </div>

        <div class="row p-2">
          <div class="col p-2"><c-btn-upload-csv v-on:change="uploadData" /></div>
          <div class="col-auto p-2">OR</div>
          <div class="col-auto p-2"><button class="btn btn-outline-secondary">Skip</button></div>
        </div>
      </div>
      <div class="p-2 text-bg-light">
        <div class="badge text-bg-secondary">2. Select map</div>

        <div class="row p-2">
          We found a potential map suitable for your data. Alternatively, you may upload your
          GeoJson file.
        </div>

        <div class="row p-2">
          We could not find a potential map suitable for your data. Please select the appropriate
          map or upload your map in GeoJson format.
        </div>

        <div class="row">
          <div class="col p-2">
            <select class="form-select" v-model="state.mapName">
              <option></option>
              <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey">
                {{ mapItem.name }}
              </option>
            </select>
          </div>
          <div class="col-auto p-2">OR</div>
          <div class="col p-2">
            <input
              class="form-control"
              type="file"
              accept="application/json,.json,.geojson"
              v-on:change="uploadGeoJson"
            />
          </div>
        </div>
      </div>
      <div class="p-2">
        <div class="badge text-bg-secondary">3. Review data</div>

        <div class="row p-2">
          Please review your data. You can configure properties/columns to be imported and edit data
          value as you want.
        </div>

        <div class="row p-2 table-responsive">
          <table class="table table-bordered">
            <thead>
              <tr class="table-light">
                <th v-for="(field, index) in state.dataTable.fields">
                  <select
                    class="form-select"
                    v-model="state.selectedFieldKeys[index]"
                    v-on:change="updateDataTable(index)"
                  >
                    <option></option>
                    <option v-for="fieldKey in state.mapFieldKeys">{{ fieldKey }}</option>
                  </select>
                </th>
              </tr>
              <tr class="table-light">
                <th v-for="(field, index) in state.dataTable.fields">
                  <span v-if="!field.headerEditable">{{ field.label }}</span>
                  <input
                    v-else
                    type="text"
                    v-bind:id="'input-h-' + field.key"
                    v-model="field.label"
                  />
                </th>
              </tr>
              <tr class="table-light">
                <th v-for="(field, index) in state.dataTable.fields">
                  <input
                    v-if="field.unit"
                    type="text"
                    v-bind:id="'input-hu-' + field.key"
                    v-model="field.unit"
                  />
                </th>
              </tr>
            </thead>
            <tr v-for="(row, rIndex) in state.dataTable.items">
              <td v-for="(cell, cIndex) in row">
                <span v-if="!state.dataTable.fields[cIndex].editable">{{ cell }}</span>
                <input
                  v-else
                  v-bind:id="'input-' + rIndex + '-' + cIndex"
                  v-model="state.dataTable.items[rIndex][cIndex]"
                  v-bind:type="state.dataTable.fields[cIndex].type"
                />
              </td>
            </tr>
          </table>
        </div>
      </div>
      <div class="p-2">
        <div class="badge text-bg-secondary">4. Generate cartogram</div>

        <div class="row p-2">
          <div class="col-auto p-2">
            <button class="btn btn-primary" v-on:click="getGeneratedCartogram">Generate</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card w-100 p-2">
      <div><span class="badge text-bg-secondary">Preview</span></div>
    </div>
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
      <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  </div>
</template>

<style scoped>
table input {
  border: 0;
  box-sizing: border-box;
  display: block;
}

table input[type='text'] {
  width: 100%;
}

table input[type='color'] {
  padding: 0;
}
</style>
