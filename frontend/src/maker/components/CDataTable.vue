<script setup lang="ts">
import type { FeatureCollection } from 'geojson'

import { reactive, watch, toRaw } from 'vue'
import embed, { type VisualizationSpec } from 'vega-embed'

import type { KeyValueArray } from '../lib/interface'
import spec from '../../assets/template.vg.json' with { type: 'json' }
import * as config from '../../common/config'
import * as util from '../lib/util'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

const versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
let visView: any

const state = reactive({
  displayTable: false
})

defineExpose({
  reset,
  initDataTableWGeojson,
  updateDataTable,
  getCSV,
  getExcel,
  validateCSV
})

watch(
  () => store.colorRegion,
  (newValue, oldValue) => {
    changeColor(newValue, oldValue)
  }
)

watch(
  () => store.useInset,
  () => {
    store.dataTable.fields[config.COL_INSET].show = store.useInset
  }
)

function reset() {
  store.dataTable.items = []
  store.dataTable.fields = [
    {
      label: 'Region',
      name: 'Region',
      type: 'text',
      editable: false,
      show: true,
      headerError: false,
      errorMessage: ''
    },
    { label: 'RegionLabel', name: 'RegionLabel', type: 'text', editable: true, show: true },
    { label: 'Color', name: 'Color', type: 'color', editable: true, show: false },
    { label: 'ColorGroup', name: 'ColorGroup', type: 'number', editable: false, show: false },
    {
      label: 'Inset',
      name: 'Inset',
      type: 'select',
      options: config.OPTIONS_INSET,
      editable: true,
      show: false
    },
    {
      label: 'Geographic Area',
      name: 'Geographic Area',
      unit: 'sq. km',
      type: 'text',
      editable: true,
      editableHead: true,
      show: false
    }
  ]
  state.displayTable = false
  document.getElementById('map-vis')!.innerHTML = ''
}

function initDataTableWGeojson(
  geojsonData: FeatureCollection,
  geojsonRegionCol: string,
  displayTable: boolean = true
) {
  reset()

  store.dataTable.fields.splice(config.NUM_RESERVED_FILEDS)
  store.dataTable.items = []
  state.displayTable = displayTable

  // Transform geojson to data fields
  let geoProperties = util.propertiesToArray(geojsonData)
  if (geoProperties.length === 0) return

  geoProperties = util.deleteKeysInArray(geoProperties, 'cartogram_id')

  const areaKey = Object.keys(geoProperties[0]).find((key) => key.startsWith('Geographic Area'))
  if (areaKey) geoProperties = util.renameKeyInArray(geoProperties, areaKey, 'Geographic Area')
  geoProperties = util.renameKeyInArray(geoProperties, geojsonRegionCol, 'Region')
  geoProperties = util.arrangeKeysInArray(geoProperties, [...config.RESERVE_FIELDS])
  geoProperties = util.addKeyInArray(geoProperties, '', 0)
  geoProperties.sort((a, b) => a.Region.localeCompare(b.Region))

  versionSpec.data[1].values = geojsonData
  versionSpec.data[2].transform[2].fields = ['properties.' + geojsonRegionCol]

  initDataTableWArray(geoProperties)
}

async function initDataTableWArray(data: KeyValueArray, isReplace = true) {
  data = util.filterKeyValueInArray(data, config.RESERVE_FIELDS)
  if (isReplace) {
    store.dataTable.items = data
  } else {
    store.dataTable.items = util.mergeObjInArray(store.dataTable.items, data, 'Region')
  }

  const keys = Object.keys(store.dataTable.items[0])
  for (let i = 0; i < keys.length; i++) {
    if (!config.RESERVE_FIELDS.includes(keys[i])) {
      const [fieldname, unit] = util.getNameUnit(keys[i])
      store.dataTable.fields.push({
        label: keys[i],
        name: fieldname,
        unit: unit,
        type: 'number',
        editable: true,
        editableHead: true,
        show: true
      })
    }
  }

  versionSpec.data[0].values = store.dataTable.items
  versionSpec.data[0].format = 'json'

  const container = await embed('#map-vis', <VisualizationSpec>versionSpec, {
    renderer: 'svg',
    actions: false,
    tooltip: config.tooltipOptions
  })
  visView = container.view
  if (store.colorRegion !== 'custom') visView.signal('color_scheme', store.colorRegion).runAsync()
}

function addColumn() {
  const index = store.dataTable.fields.findIndex((item) => item.name === '')
  if (index > -1) {
    const nameInput = document.getElementById('formFieldName' + index) as HTMLInputElement
    if (nameInput) {
      nameInput.reportValidity()
    }
    return
  }

  const label = Date.now().toString()
  store.dataTable.fields.push({
    label: label,
    name: '',
    unit: '',
    type: 'number',
    editable: true,
    editableHead: true,
    show: true
  })
  store.dataTable.items = util.addKeyInArray(toRaw(store.dataTable.items), label, 0)
}

function validateCSV(csvData: KeyValueArray): boolean {
  if (csvData.length === 0) return false

  // 1. Check if the CSV header contains the "Region" column.
  if (!csvData[0].hasOwnProperty('Region')) {
    // Mark error on the header for the Region field.
    const regionField = store.dataTable.fields.find((field) => field.label === 'Region')
    if (regionField) {
      regionField.errorMessage = 'Region column not found in the uploaded CSV'
      regionField.headerError = true // Custom property for header errors.
    }
    return false
  } else {
    // Clear any header error if the Region column is present.
    const regionField = store.dataTable.fields.find((field) => field.label === 'Region')
    if (regionField) {
      regionField.errorMessage = ''
      regionField.headerError = false
    }
  }

  // 2. Compare Region values row by row.
  const csvRegions = csvData.map((row) => row['Region'])
  const mapRegions = store.dataTable.items.map((row) => row['Region'])

  let valid = true

  // Check row count mismatch and mark header error.
  if (csvRegions.length !== mapRegions.length) {
    const regionField = store.dataTable.fields.find((field) => field.label === 'Region')
    if (regionField) {
      regionField.errorMessage = `Row count mismatch: CSV has ${csvRegions.length} rows, but expected ${mapRegions.length}`
      regionField.headerError = true
    }
    valid = false
  }

  // Now, check each row's Region value.
  for (let i = 0; i < Math.min(csvRegions.length, mapRegions.length); i++) {
    if (csvRegions[i] !== mapRegions[i]) {
      // Mark error on the specific row's Region cell.
      store.dataTable.items[i].regionError =
        `Region mismatch at row ${i + 1}: CSV has "${csvRegions[i]}", expected "${mapRegions[i]}"`
      valid = false
    } else {
      // Clear any previous error if the values match.
      delete store.dataTable.items[i].regionError
    }
  }

  return valid
}

function updateDataTable(csvData: KeyValueArray) {
  if (csvData.length === 0) return

  const areaKey = Object.keys(csvData[0]).find((key) => key.startsWith('Geographic Area'))
  if (areaKey) {
    const [, unit] = util.getNameUnit(areaKey)
    store.dataTable.fields[config.COL_AREA].unit = unit
    csvData = util.renameKeyInArray(csvData, areaKey, 'Geographic Area')
  }

  store.dataTable.items = util.filterKeyValueInArray(
    store.dataTable.items,
    config.RESERVE_FIELDS,
    null
  )
  store.dataTable.fields.splice(config.NUM_RESERVED_FILEDS)
  store.dataTable.fields[config.COL_COLOR].show = csvData[0].hasOwnProperty('Color')
  store.dataTable.fields[config.COL_INSET].show = csvData[0].hasOwnProperty('Inset')
  initDataTableWArray(csvData, false)

  store.colorRegion = store.dataTable.fields[config.COL_COLOR].show ? 'custom' : store.colorRegion
  store.useInset = store.dataTable.fields[config.COL_INSET].show
}

function changeColor(scheme: string, oldScheme: string) {
  if (scheme === 'custom') {
    if (oldScheme !== 'custom') {
      // No color assigned - Copy all color from Vega to data table
      const colorScale = visView.scale('color_group')
      for (let i = 0; i < store.dataTable.items.length; i++) {
        store.dataTable.items[i]['Color'] = colorScale(store.dataTable.items[i]['ColorGroup'])
      }
    } else {
      // Assign white to empty color
      for (let i = 0; i < store.dataTable.items.length; i++) {
        store.dataTable.items[i]['Color'] = store.dataTable.items[i]['Color']
          ? store.dataTable.items[i]['Color']
          : '#ffffff'
      }
    }

    store.dataTable.fields[config.COL_COLOR].show = true
  } else {
    for (let i = 0; i < store.dataTable.items.length; i++) {
      delete store.dataTable.items[i]['Color']
    }

    store.dataTable.fields[config.COL_COLOR].show = false
    visView.signal('color_scheme', scheme).runAsync()
  }
}

async function getCSV(isGetFile = false) {
  if (!isGetFile) store.dataTable.fields[config.COL_AREA].show = true // Force include Geographic Area when generate cartogram
  const csv = await util.getGeneratedCSV(store.dataTable, isGetFile)
  store.dataTable.fields[config.COL_AREA].show = false
  return csv
}

async function getExcel() {
  return await util.getGeneratedExcel(store.dataTable)
}

function updateLabel(index: number) {
  const oldLabel = store.dataTable.fields[index].label
  let newLabel = store.dataTable.fields[index].name
  if (store.dataTable.fields[index].unit)
    newLabel = newLabel + ' (' + store.dataTable.fields[index].unit + ')'

  store.dataTable.fields[index].label = newLabel
  store.dataTable.items = util.renameKeyInArray(toRaw(store.dataTable.items), oldLabel, newLabel)
  visView.data('source_csv', store.dataTable.items).runAsync()
}

function validateInput(event: Event) {
  const inputElement = event.target as HTMLInputElement
  if (!inputElement.checkValidity()) {
    inputElement.reportValidity()
  }
}

function onValueChange(rIndex: number, label: string, event: Event) {
  const target = <HTMLInputElement>event.target
  store.dataTable.items[rIndex][label] = target.value
  const changeset = visView
    .changeset()
    .modify(
      (item: any) => item.Region === store.dataTable.items[rIndex].Region,
      label,
      target.value
    )
  visView.change('source_csv', changeset).run()
}
</script>
<template>
  <!-- Overview Message -->
  <div class="p-2">
    <span class="badge text-bg-secondary">Input Overview</span>
  </div>
  <div class="p-2" v-if="store.dataTable.items.length < 1">
    <p>
      Please follow the steps
      <span class="d-none d-sm-inline">on the left panel</span>
      <span class="d-inline d-sm-none">above</span>.
    </p>
    <p>
      Don't know where to start? You may try editing one of our
      <a href="/cartogram">examples</a>. If you have any questions or issues about cartogram
      generation, refer to the <a href="//guides.go-cart.io/quick-start">guides</a> or
      <a href="/contact">contact us</a>.
    </p>
  </div>

  <!-- Map Container -->
  <div id="map-vis" class="vis-area p-2"></div>

  <!-- Data Table -->
  <div class="d-table p-2" v-if="state.displayTable && store.dataTable.items.length > 0">
    <button class="btn btn-outline-secondary mb-2 float-end" v-on:click="addColumn">
      Add column <i class="btn-icon fas fa-plus-circle"></i>
    </button>
    <table class="table table-bordered">
      <thead>
        <tr class="table-light">
          <th
            v-for="(field, index) in store.dataTable.fields"
            v-show="field.show"
            v-bind:key="index"
          >
            <!-- Wrap header content in a container for tooltip -->
            <div
              class="header-cell"
              v-bind:class="{ 'header-error': field.label === 'Region' && field.headerError }"
            >
              <span v-if="!field.editableHead">{{ field.label }}</span>
              <div v-else>
                <i
                  v-if="store.dataTable.fields[index].name !== 'Geographic Area'"
                  class="position-absolute top-0 end-0 btn-icon text-secondary fas fa-minus-circle"
                  v-on:click="store.dataTable.fields[index].show = false"
                  v-bind:title="'Remove ' + store.dataTable.fields[index].name + ' column'"
                ></i>
                <!-- TODO ask for the confirmation and completely remove it so it'll beremove from the popup. -->
                <input
                  class="form-control"
                  v-model="store.dataTable.fields[index].name"
                  placeholder="Data name"
                  required
                  v-bind:id="'formFieldName' + index"
                  v-on:blur="validateInput"
                  v-on:change="updateLabel(index)"
                />
                <input
                  class="form-control"
                  v-model="store.dataTable.fields[index].unit"
                  placeholder="Unit"
                  v-bind:id="'formFieldUnit' + index"
                  v-on:change="updateLabel(index)"
                />
              </div>
              <!-- Tooltip for header error -->
              <div v-if="field.label === 'Region' && field.headerError" class="tooltip">
                {{ field.errorMessage }}
              </div>
            </div>
          </th>
        </tr>
      </thead>
      <tr v-for="(row, rIndex) in store.dataTable.items" v-bind:key="rIndex">
        <td v-for="(field, index) in store.dataTable.fields" v-show="field.show" v-bind:key="index">
          <div
            class="cell-content"
            v-bind:class="{ 'error-cell': field.label === 'Region' && row.regionError }"
          >
            <span v-if="!field.editable">{{ row[field.label] }}</span>
            <select
              v-else-if="field.type === 'select'"
              class="form-select"
              v-model="store.dataTable.items[rIndex][field.label]"
            >
              <option
                v-for="option in field.options"
                v-bind:value="option.value"
                v-bind:key="option.value"
              >
                {{ option.text }}
              </option>
            </select>
            <input
              v-else-if="field.show"
              class="form-control"
              v-bind:type="field.type"
              v-bind:value="store.dataTable.items[rIndex][field.label]"
              v-on:change="($event: any) => onValueChange(rIndex, field.label, $event)"
            />
            <!-- Tooltip for cell error -->
            <div v-if="field.label === 'Region' && row.regionError" class="tooltip">
              {{ row.regionError }}
            </div>
          </div>
        </td>
      </tr>
    </table>
  </div>
</template>

<style scoped>
.vis-area {
  width: 100%;
  height: 300px;
}

/* Table input/select styling */
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

/* Header error highlighting */
.header-error {
  background-color: #f8d7da;
  /* Light red background */
}

/* Cell error highlighting */
.error-cell {
  background-color: #f8d7da;
}

/* Tooltip container styles */
.header-cell,
.cell-content {
  position: relative;
  display: inline-block;
}

/* Show tooltip immediately on hover */
.header-cell:hover .tooltip,
.cell-content:hover .tooltip {
  visibility: visible;
  opacity: 1;
  transition: opacity 0s;
}
</style>
