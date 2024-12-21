<script setup lang="ts">
import * as d3 from 'd3'
import type { FeatureCollection } from 'geojson'
import { Toast, Modal } from 'bootstrap'
import { reactive, onBeforeMount, onMounted } from 'vue'
import embed, { type VisualizationSpec } from 'vega-embed'

import spec from '../../assets/template.vg.json' with { type: "json" }
import * as util from '../lib/util'
import HTTP from '../lib/http'
import * as config from '../../common/config'
import type { KeyValueArray, DataTable } from '../lib/interface'
import type { MapHandlers } from '../../common/interface'

import CFormGeojson from './CFormGeojson.vue'
import CFormCsv from './CFormCsv.vue'
import CSelectColor from './CSelectColor.vue'

var versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
var mapDBKey = util.generateShareKey(32)
var visView: any

const props = defineProps<{
  maps: MapHandlers
  mapName?: string
  mapTitle?: string
  mapColorScheme?: string
  geoUrl?: string
  csvUrl?: string
}>()

const state = reactive({
  loadingProgress: 0,
  error: '',
  handler: '',
  title: '',
  colorScheme: 'pastel1',
  geojsonData: {} as FeatureCollection,
  geojsonRegionCol: '',
  dataTable: { fields: [], items: [] } as DataTable
})

onBeforeMount(() => {
  reset()
})

onMounted(() => {
  if (!props.mapName || !props.geoUrl || !props.csvUrl) return

  HTTP.get(props.geoUrl).then(function (response: any) {
    initDataTableWGeojson(props.mapName!, response, 'name', props.csvUrl)
  })
})

function reset() {
  state.loadingProgress = 0
  state.error = ''
  state.handler = ''
  state.title = props.mapTitle ? props.mapTitle : ''
  state.colorScheme = props.mapColorScheme ? props.mapColorScheme : 'pastel1'
  state.geojsonData = {} as FeatureCollection
  state.geojsonRegionCol = ''
  state.dataTable.items = []
  state.dataTable.fields = [
    { label: 'Region', name: 'Region', type: 'text', editable: false, show: true },
    { label: 'RegionLabel', name: 'RegionLabel', type: 'text', editable: true, show: true },
    { label: 'Color', name: 'Color', type: 'color', editable: true, show: false },
    { label: 'ColorGroup', name: 'ColorGroup', type: 'number', editable: false, show: false },
    { label: 'Inset', name: 'Inset', type: 'select', options: config.OPTIONS_INSET, editable: true, show: false },
    { label: 'Land Area', name: 'Land Area', unit: 'sq.km.', type: 'text', editable: true, editableHead: true, show: true }
  ]
}

function initDataTableWGeojson(handler: string, geojsonData: FeatureCollection, regionCol: string, csvFile = '') {
  // TODO Ask for confirmation before clearing data or closing page
  document.getElementById("map-vis")!.innerHTML = ""
  state.dataTable.fields.splice(config.NUM_RESERVED_FILEDS)
  state.dataTable.items = []

  state.handler = handler
  state.geojsonRegionCol = regionCol
  state.geojsonData = geojsonData

  // Transform geojson to data fields
  var geoProperties = util.propertiesToArray(geojsonData)
  if (geoProperties.length === 0) return

  if (!Object.keys(geoProperties[0]).some(key => key.startsWith('Population')))
    geoProperties = util.addKeyInArray(geoProperties, 'Population (people)', 0)

  const areaKey = Object.keys(geoProperties[0]).find(key => key.startsWith('Land Area'))
  if (areaKey) geoProperties = util.renameKeyInArray(geoProperties, areaKey, 'Land Area')
  geoProperties = util.renameKeyInArray(geoProperties, state.geojsonRegionCol, 'Region')
  geoProperties = util.arrangeKeysInArray(geoProperties, [...config.RESERVE_FIELDS, 'Population (people)'])
  geoProperties.sort((a, b) => a.Region.localeCompare(b.Region))

  initDataTableWArray(geoProperties)

  // Immediately populate data if a CSV file is supplied
  if (csvFile) {
    d3.csv(csvFile)
    .then((csvData) => {
      if (!csvData || !Array.isArray(csvData)) {
        console.error('Invalid CSV data')
        return
      }
      updateDataTable(csvData)
    })
    .catch((error) => {
      console.error('Error loading CSV:', error)
    })
  }
}

async function initDataTableWArray(data: KeyValueArray, isReplace = true) {
  data = util.filterKeyValueInArray(data, config.RESERVE_FIELDS)
  if (isReplace) {
    state.dataTable.items = data
  } else {
    state.dataTable.items = util.mergeObjInArray(state.dataTable.items, data, 'Region')
  }

  var keys = Object.keys(state.dataTable.items[0])
  for (var i = 0; i < keys.length; i++) {
    if (!config.RESERVE_FIELDS.includes(keys[i])) {
      var [fieldname, unit] = util.getNameUnit(keys[i])
      state.dataTable.fields.push({ label: keys[i], name: fieldname, unit: unit, type: 'number', editable: true, editableHead: true, show: true })
    }
  }

  versionSpec.data[0].values = state.dataTable.items
  versionSpec.data[0].format = 'json'
  versionSpec.data[1].values = state.geojsonData
  versionSpec.data[2].transform[0].fields = [ "properties." + state.geojsonRegionCol ]

  let container = await embed('#map-vis', <VisualizationSpec> versionSpec, { renderer: 'svg', "actions": false })
  visView = container.view
  visView.signal('colorScheme', state.colorScheme).runAsync()
}

function updateDataTable(csvData: KeyValueArray) {
  if (csvData.length === 0) return

  const areaKey = Object.keys(csvData[0]).find(key => key.startsWith('Land Area'))
  if (areaKey) {
    var [fieldname, unit] = util.getNameUnit(areaKey)
    state.dataTable.fields[config.COL_AREA].unit = unit
    csvData = util.renameKeyInArray(csvData, areaKey, 'Land Area')
  }

  state.dataTable.items = util.filterKeyValueInArray(state.dataTable.items, config.RESERVE_FIELDS, null)
  state.dataTable.fields.splice(config.NUM_RESERVED_FILEDS)
  state.dataTable.fields[config.COL_AREA].show = csvData[0].hasOwnProperty("Land Area")
  state.dataTable.fields[config.COL_COLOR].show = csvData[0].hasOwnProperty("Color")
  state.dataTable.fields[config.COL_INSET].show = csvData[0].hasOwnProperty("Inset")
  initDataTableWArray(csvData, false)
}

async function getGeneratedCartogram() {
  const progressModal = new Modal('#progressBackdrop', {
    backdrop: 'static',
    keyboard: false
  })
  progressModal.show()

  var geojsonData = state.handler === 'custom' ?
    util.filterGeoJSONProperties(state.geojsonData, ['cartogram_id', state.geojsonRegionCol, 'label'],  ['cartogram_id', 'name', 'label']) :
    undefined
  var data = util.tableToArray(state.dataTable)
  var csvData = d3.csvFormat(data)

  await new Promise<any>(function (resolve, reject) {
    var req_body =
      'data=' +
      JSON.stringify({
        title: state.title,
        scheme: state.colorScheme,
        handler: state.handler,
        csv: csvData,
        geojson: geojsonData,
        mapDBKey: mapDBKey,
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
      })(mapDBKey),
      500
    )

    HTTP.post('/api/v1/cartogram', req_body, {
      'Content-type': 'application/x-www-form-urlencoded'
    }).then(
      function (response: any) {
        state.loadingProgress = 100
        window.clearInterval(progressUpdater)
        resolve(response)
        window.location.href = '/cartogram/key/' + response.mapDBKey + '/preview'
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

function onColorChanged(scheme: string) {
  state.colorScheme = scheme
  if (scheme === 'custom') {
    state.dataTable.fields[config.COL_COLOR].show = true
  } else {
    state.dataTable.fields[config.COL_COLOR].show = false
    visView.signal('colorScheme', scheme).runAsync()
  }
}
</script>

<template>
  <div class="d-flex flex-fill">
    <div class="card w-25 m-2">
      <c-form-geojson
        v-bind:mapDBKey="mapDBKey"
        v-bind:maps="props.maps"
        v-bind:geoUrl="props.geoUrl"
        v-on:changed="initDataTableWGeojson"
      />

      <div class="p-2">
        <div class="badge text-bg-secondary">2. Specify visualization</div>

        <div class="p-2">
          Title
          <input class="form-control" type="text" v-model="state.title" maxlength="100" />
        </div>

        <div class="p-2">
          <c-select-color
            v-bind:disabled="!('features' in state.geojsonData)"
            v-bind:scheme="state.colorScheme"
            v-on:changed="onColorChanged"
          />
        </div>

        <div class="p-2">
          <div class="form-check">
            <input
              class="form-check-input"
              type="checkbox"
              v-model="state.dataTable.fields[config.COL_AREA].show"
              id="chk-area"
            />
            <label class="form-check-label" for="chk-area">
              Include equal-area map (recommended)
            </label>
          </div>
          <div class="form-check">
            <input
              class="form-check-input"
              type="checkbox"
              v-model="state.dataTable.fields[config.COL_INSET].show"
              id="chk-inset"
            />
            <label class="form-check-label" for="chk-inset"> Define inset </label>
          </div>
        </div>
      </div>

      <div class="p-2">
        <div class="badge text-bg-secondary">3. Download data (optional)</div>
        <div class="p-2">
          <button
            class="btn btn-outline-secondary"
            v-bind:disabled="!('features' in state.geojsonData)"
            v-on:click="util.getGeneratedCSV(state.dataTable)"
          >
            Download data
          </button>
          for editing on your device.
        </div>
      </div>

      <c-form-csv
        v-bind:disabled="!('features' in state.geojsonData)"
        v-on:changed="updateDataTable"
      />

      <div class="p-2">
        <div class="badge text-bg-secondary">5. Generate cartogram</div>

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
      <div class="p-2" v-if="state.dataTable.items.length < 1">
        Please follow steps on the left panel.
      </div>
      <div id="map-vis" class="vis-area p-2"></div>
      <div class="d-table p-2" v-if="state.dataTable.items.length > 0">
        <table class="table table-bordered">
          <thead>
            <tr class="table-light">
              <th v-for="(field, index) in state.dataTable.fields" v-show="field.show">
                <span v-if="!field.editableHead">{{ field.label }}</span>
                <div class="position-relative" v-else>
                  <i
                    class="position-absolute top-0 end-0 btn-icon text-secondary fas fa-minus-circle"
                    v-on:click="state.dataTable.fields[index].show = false"
                    v-bind:title="'Remove ' + state.dataTable.fields[index].name + ' column'"
                  ></i>
                  <input
                    class="form-control"
                    v-model="state.dataTable.fields[index]['name']"
                    v-bind:type="field.name"
                    placeholder="Data name"
                  />
                  <input
                    class="form-control"
                    v-model="state.dataTable.fields[index]['unit']"
                    v-bind:type="field.unit"
                    placeholder="Unit"
                  />
                </div>
              </th>
            </tr>
          </thead>
          <tr v-for="(row, rIndex) in state.dataTable.items">
            <td v-for="(field, index) in state.dataTable.fields" v-show="field.show">
              <span v-if="!field.editable">{{ row[field.label] }}</span>
              <select
                class="form-control"
                v-model="state.dataTable.items[rIndex][field.label]"
                v-else-if="field.type === 'select'"
              >
                <option v-for="option in field.options" v-bind:value="option.value">
                  {{ option.text }}
                </option>
              </select>
              <input
                v-else
                class="form-control"
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

table input,
table select {
  width: 100%;
  min-width: 100px;
}

table input[type='color'] {
  padding: 0;
  min-width: 60px;
}

.btn-icon {
  cursor: pointer;
}
</style>
