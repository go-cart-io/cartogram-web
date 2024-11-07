<script setup lang="ts">
import * as d3 from 'd3'
import type { FeatureCollection, Feature } from 'geojson'
import { Toast, Modal } from 'bootstrap'
import { reactive, onBeforeMount } from 'vue'
import embed, { type VisualizationSpec } from 'vega-embed'

import spec from '../../assets/template.vg.json' with { type: "json" }
import * as util from '../lib/util'
import HTTP from '../../common/lib/http'
import { RESERVE_FIELDS, RESERVE_FIELDS_CSV } from '../../common/lib/config'
import type { KeyValueArray, DataTable } from '../lib/interface'
import type { MapHandlers } from '../../common/lib/interface'

import CFormGeojson from './CFormGeojson.vue'
import CFormCsv from './CFormCsv.vue'

var versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template

const props = defineProps<{
  maps: MapHandlers
}>()

const state = reactive({
  loadingProgress: 0,
  error: '',
  handler: '',
  title: '',
  geojsonData: {} as FeatureCollection,
  geojsonRegionCol: '',
  dataTable: { fields: [], items: [] } as DataTable
})

onBeforeMount(() => {
  reset()
})

function reset() {
  state.loadingProgress = 0
  state.error = ''
  state.handler = ''
  state.title = ''
  state.geojsonData = {} as FeatureCollection
  state.geojsonRegionCol = ''
  state.dataTable = { fields: [], items: [] } as DataTable
}

function initDataTableWGeojson(handler: string, geojsonData: FeatureCollection, regionCol: string) {
  // TODO Ask for confirmation before clearing data or closing page
  state.dataTable = { fields: [], items: [] } as DataTable

  state.handler = handler
  state.geojsonRegionCol = regionCol
  state.geojsonData = geojsonData

  // Transform geojson to data fields
  var geoProperties = util.propertiesToArray(geojsonData)
  if (geoProperties.length === 0) return
  geoProperties = util.renameKeyInArray(geoProperties, state.geojsonRegionCol, 'Region')

  initDataTableWArray(geoProperties)
}

async function initDataTableWArray(data: KeyValueArray) {
  data = util.filterNumberInArray(data, RESERVE_FIELDS_CSV)
  data = util.arrangeKeysInArray(data, RESERVE_FIELDS_CSV)
  state.dataTable.items = data
  state.dataTable.items.sort((a, b) => a.Region.localeCompare(b.Region))

  state.dataTable.fields = [
    { label: 'Region', type: 'text', editable: false, show: true, required: true },
    { label: 'Abbreviation', type: 'text', editable: true, show: true, required: true },
    { label: 'Color', type: 'text', editable: true, show: false }
  ]
  var headers = [] as Array<string>
  var keys = Object.keys(state.dataTable.items[0])
  for (var i = 0; i < keys.length; i++) {
    if (!RESERVE_FIELDS.includes(keys[i]))
      state.dataTable.fields.push({ label: keys[i], type: 'number', editable: true, show: true })
      headers.push(keys[i])
  }

  versionSpec.data[0].values = state.dataTable.items
  versionSpec.data[0].format = 'json'
  versionSpec.data[1].values = state.geojsonData
  // versionSpec.data[2].transform[1].values.push(...headers)
  let container = await embed('#map-vis', <VisualizationSpec> versionSpec, { renderer: 'svg', "actions": false })
}

function updateDataTable(csvData: KeyValueArray, isReplace: boolean) {
  if (csvData.length === 0) return

  // TODO Check if the csv data match with map data
  if (isReplace) {
    initDataTableWArray(csvData)
  } else {
    // Merge csv data to exiting table
    var keys = Object.keys(csvData[0])
    var existingKeys = Object.keys(state.dataTable.items[0])
    for (var i = 0; i < keys.length; i++) {
      if (!RESERVE_FIELDS.includes(keys[i]) && !existingKeys.includes(keys[i])) {
        state.dataTable.fields.push({ label: keys[i], type: 'number', editable: true, show: true })
      }
    }

    state.dataTable.items = state.dataTable.items.map((item) => {
      const csvItems = csvData.find((c) => c.Region === item.Region)
      return { ...item, ...csvItems }
    })
  }
}

async function getGeneratedCSV() {
  var data = util.tableToArray(state.dataTable)
  var csv = d3.csvFormat(data)
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'data.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

async function getGeneratedCartogram() {
  const progressModal = new Modal('#progressBackdrop', {
    backdrop: 'static',
    keyboard: false
  })
  progressModal.show()

  // TODO Rename property of geojson
  var data = util.tableToArray(state.dataTable)
  var csvData = d3.csvFormat(data)
  var stringKey = util.generateShareKey(32)
  await new Promise<any>(function (resolve, reject) {
    var req_body =
      'data=' +
      JSON.stringify({
        handler: state.handler,
        csv: csvData,
        geojson: state.handler === 'custom' ? state.geojsonData : undefined,
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
    Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
    return
  })
}
</script>

<template>
  <div class="d-flex flex-fill">
    <div class="card w-25 m-2">
      <c-form-geojson v-bind:maps="props.maps" v-on:changed="initDataTableWGeojson" />

      <div class="p-2">
        <div class="badge text-bg-secondary">2. Download data (optional)</div>
        <div class="p-2">
          <button class="btn btn-outline-secondary" v-on:click="getGeneratedCSV">
            Download data
          </button>
          for editing on your device.
        </div>
      </div>

      <c-form-csv v-on:changed="updateDataTable" />

      <div class="p-2">
        <div class="badge text-bg-secondary">4. Specify visualization</div>

        <div class="p-2">
          Title
          <input class="form-control" type="text" v-model="state.title" maxlength="100" />
        </div>

        <div class="p-2">
          <span v-if="state.dataTable.fields.length > 0">Select data</span>
          <div class="form-check" v-for="(item, index) in state.dataTable.fields">
            <input
              class="form-check-input"
              type="checkbox"
              v-model="state.dataTable.fields[index].show"
              v-bind:id="index.toString()"
              v-bind:disabled="state.dataTable.fields[index].required"
            />
            <label class="form-check-label" v-bind:for="index.toString()">
              {{ item.label }}
            </label>
          </div>
        </div>
      </div>
      <div class="p-2">
        <div class="badge text-bg-secondary">4. Generate cartogram</div>

        <div class="row p-2">
          <div class="col-auto p-2">
            <p class="bg-warning-subtle p-1 rounded">
              <!-- TODO: Auto extend the link validity when hit share button -->
              <span class="badge text-bg-warning">Important</span> The data will be pruned from our
              server within 1-2 days, unless you share and access a non-preview link. We strongly
              advise you to back up your original data in a safe place so you can regenerate the
              cartogram if needed.
            </p>
            <button class="btn btn-primary" v-on:click="getGeneratedCartogram">Generate</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card w-75 m-2 border-0">
      <div class="p-2"><span class="badge text-bg-secondary">Input Overview</span></div>
      <div class="p-2" v-if="state.dataTable.fields.length < 1">
        Please follow steps on the left panel.
      </div>
      <div id="map-vis" class="vis-area p-2"></div>
      <div class="d-table p-2">
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
    class="toast toast position-fixed end-0 bottom-0 m-3 text-bg-danger"
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
.vis-area {
  width: 100%;
  height: 300px;
}

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
