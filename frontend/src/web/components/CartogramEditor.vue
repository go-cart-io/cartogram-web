<script setup lang="ts">
import * as d3 from 'd3'
import * as XLSX from 'xlsx'
import { Toast, Modal } from 'bootstrap'
import { ref, reactive, onBeforeMount } from 'vue'

import HTTP from '../lib/http'
import type { MapHandlers } from '../../common/lib/interface'

const geojsonInput = ref<HTMLInputElement>()

const props = defineProps<{
  maps: MapHandlers
}>()

const state = reactive({
  loadingProgress: 0,
  error: '',
  handler: '',
  title: '',
  csvData: null as any,
  csvRegionCol: 'Region',
  geojsonData: null as any,
  geojsonRegionCol: 'name',
  dataTable: { fields: [], items: [] } as {
    fields: Array<{
      label: string
      type: string
      show: boolean
      editable: boolean
    }>
    items: Array<{ [key: string]: any }>
  }
})

onBeforeMount(() => {
  reset()
})

function reset() {
  state.loadingProgress = 0
  state.handler = 'custom'
  state.title = ''
  state.csvData = null
  state.csvRegionCol = 'Region'
  state.geojsonData = null
  state.geojsonRegionCol = 'name'
  state.dataTable.fields = []
  state.dataTable.items = []
}

async function readFile(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsBinaryString(file)
    reader.onload = () => resolve(<string>reader.result)
    reader.onerror = (error) => reject(error)
  })
}

async function uploadData(event: Event) {
  const files = (event.target as HTMLInputElement).files
  if (!files) return

  var data = await readFile(files[0])
  var type = files[0].name.split('.').pop()?.slice(0, 3)
  var csvData = [{}]
  if (type === 'xls' || type === 'xlsx') {
    var wb = XLSX.read(data, { type: 'binary' })
    var ws = wb.Sheets[wb.SheetNames[0]]
    csvData = XLSX.utils.sheet_to_json(ws)
  } else {
    csvData = d3.csvParse(data as string)
  }

  if (!csvData || csvData.length < 1) return

  state.csvData = csvData
  state.csvRegionCol = Object.keys(csvData[0])[0]
  console.log(state.csvData)
}

async function uploadGeoJson(event: Event) {
  const files = (event.target as HTMLInputElement).files
  if (!files) return

  var data = await readFile(files[0])
  state.geojsonData = JSON.parse(data)
  state.handler = 'custom'
  console.log(state.geojsonData)

  initDataTable()
}

function initDataTable() {
  // TODO Check if the csv data match with map data
  state.dataTable.fields = []
  var keys = Object.keys(state.csvData[0])
  for (var i = 0; i < keys.length; i++) {
    if (keys[i] === 'Region')
      state.dataTable.fields.push({ label: keys[i], type: 'text', editable: false, show: true })
    else if (keys[i] === 'Abbreviation' || keys[i] === 'Color')
      state.dataTable.fields.push({ label: keys[i], type: 'text', editable: true, show: true })
    else state.dataTable.fields.push({ label: keys[i], type: 'number', editable: true, show: true })
  }

  state.dataTable.items = JSON.parse(JSON.stringify(state.csvData))
}

async function getGeneratedCartogram() {
  const progressModal = new Modal('#progressBackdrop', {
    backdrop: 'static',
    keyboard: false
  })
  progressModal.show()

  // Remove hidden columns
  var data = [] as any
  for (var i = 0; i < state.dataTable.items.length; i++) {
    data[i] = {}
    for (var j = 0; j < state.dataTable.fields.length; j++) {
      if (state.dataTable.fields[j].show) {
        data[i][state.dataTable.fields[j].label] =
          state.dataTable.items[i][state.dataTable.fields[j].label]
      }
    }
  }

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

  var csvData = d3.csvFormat(data)
  var stringKey = generateShareKey(32)
  await new Promise<any>(function (resolve, reject) {
    var req_body =
      'data=' +
      JSON.stringify({
        handler: state.handler,
        csv: csvData,
        geojson: state.geojsonData,
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
              state.loadingProgress = 8
              return
            }

            state.loadingProgress = Math.floor(progress.progress * 100)
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
        state.loadingProgress = 100
        window.clearInterval(progressUpdater)
        resolve(response)
        window.location.href = '/cartogram/key/' + response.stringKey + '/preview'
      },
      function (error: any) {
        state.loadingProgress = 100
        window.clearInterval(progressUpdater)
        reject(error)
      }
    )
  }).catch(function (error: any) {
    state.error = error
    progressModal.hide()
    console.log('22222222222222')
    Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
    return
  })
}
</script>

<template>
  <div class="d-flex flex-fill">
    <div class="card w-25 m-2">
      <div class="p-2">
        <div class="badge text-bg-secondary">1. Import your data</div>

        <div class="p-2">
          Upload CSV or Excel file
          <input
            ref="csvInput"
            type="file"
            class="form-control"
            accept="text/csv,.csv,.xlsx,.xls"
            v-on:change="uploadData"
          />
        </div>

        <!-- TODO: Allow custom field name
        <div class="p-2" v-if="state.csvData && state.csvData[0]">
          Which column contain region names (e.g., country names)?
          <select class="form-select" v-model="state.csvRegionCol">
            <option v-for="(index, item) in state.csvData[0]">
              {{ item }}
            </option>
          </select>
        </div> -->
      </div>
      <div class="p-2 text-bg-light">
        <div class="badge text-bg-secondary">2. Select map</div>
        <div class="p-2">
          Select an appropriate map for your data.

          <select
            class="form-select"
            v-model="state.handler"
            v-on:change="
              () => {
                geojsonInput!.value = ''
                initDataTable()
              }
            "
          >
            <option></option>
            <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey">
              {{ mapItem.name }}
            </option>
          </select>
        </div>
        <div class="p-2">
          OR upload your map in GeoJson format.
          <input
            ref="geojsonInput"
            class="form-control"
            type="file"
            accept="application/json,.json,.geojson"
            v-on:change="uploadGeoJson"
          />
        </div>
        <!-- TODO: Allow custom property name
          <div class="p-2" v-if="state.geojsonData && state.geojsonData[0]">
          Which column contain region names (e.g., country names)?
          <select class="form-select" v-model="state.geojsonRegionCol">
            <option v-for="(index, item) in state.geojsonData[0].properties">
              {{ item }}
            </option>
          </select>
        </div> -->
      </div>
      <div class="p-2">
        <div class="badge text-bg-secondary">3. Specify visualization</div>

        <div class="p-2">
          Title
          <input class="form-control" type="text" v-model="state.title" />
        </div>

        <div class="p-2">
          Select data
          <div class="form-check" v-for="(item, index) in state.dataTable.fields">
            <input
              class="form-check-input"
              type="checkbox"
              v-model="state.dataTable.fields[index].show"
              v-bind:id="index.toString()"
            />
            <label class="form-check-label" v-bind:for="index.toString()">
              {{ item.label }}
            </label>
          </div>
          <!-- TODO: Also allow filed selection from geojson data -->
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

    <div class="card w-75 m-2">
      <div class="p-2"><span class="badge text-bg-secondary">Preview</span></div>
      <div class="p-2 table-responsive">
        <table class="table table-bordered">
          <thead>
            <tr class="table-light">
              <th v-for="(field, index) in state.dataTable.fields" v-show="field.show">
                {{ field.label }}
              </th>
            </tr>
          </thead>
          <tr v-for="(row, rIndex) in state.dataTable.items">
            <td v-for="(field, index) in state.dataTable.fields" v-show="field.show">
              <span v-if="!field.editable">{{ row[field.label] }}</span>
              <input
                v-else
                v-model="state.dataTable.items[rIndex][field.label]"
                v-bind:type="field.type"
              />
            </td>
          </tr>
        </table>
      </div>
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

  <div class="modal" id="progressBackdrop" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-body">
          <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100">
            <div
              class="progress-bar bg-primary"
              :style="{ width: state.loadingProgress + '%' }"
            ></div>
          </div>
        </div>
      </div>
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
