<script setup lang="ts">
import type { FeatureCollection } from 'geojson'

import * as d3 from 'd3'
import { reactive, watch } from 'vue'
import embed, { type VisualizationSpec } from 'vega-embed'

import type { KeyValueArray, DataTable } from '../lib/interface'
import spec from '../../assets/template.vg.json' with { type: "json" }
import * as config from '../../common/config'
import * as util from '../lib/util'

var versionSpec = JSON.parse(JSON.stringify(spec)) // copy the template
var visView: any

const props = defineProps<{
  mapColorScheme: string,
  useEqualArea: boolean,
  useInset: boolean
}>()

const state = reactive({
  dataTable: { fields: [], items: [] } as DataTable
})

defineExpose({
  initDataTableWGeojson, updateDataTable, getCSV
})

watch(
  () => props.mapColorScheme,
  (newValue, oldValue) => {
    changeColor(props.mapColorScheme)
  }
)

watch(
  () => props.useEqualArea,
  (newValue, oldValue) => {
    state.dataTable.fields[config.COL_AREA].show = props.useEqualArea
  }
)

watch(
  () => props.useInset,
  (newValue, oldValue) => {
    state.dataTable.fields[config.COL_INSET].show = props.useInset
  }
)

function reset() {
  state.dataTable.items = []
  state.dataTable.fields = [
    { label: 'Region', name: 'Region', type: 'text', editable: false, show: true },
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
      label: 'Land Area',
      name: 'Land Area',
      unit: 'sq.km.',
      type: 'text',
      editable: true,
      editableHead: true,
      show: true
    }
  ]
}

function initDataTableWGeojson(geojsonData: FeatureCollection, geojsonRegionCol: string, csvFile = '') {
  reset()

  document.getElementById('map-vis')!.innerHTML = ''
  state.dataTable.fields.splice(config.NUM_RESERVED_FILEDS)
  state.dataTable.items = []

  // Transform geojson to data fields
  var geoProperties = util.propertiesToArray(geojsonData)
  if (geoProperties.length === 0) return

  if (!Object.keys(geoProperties[0]).some((key) => key.startsWith('Population')))
    geoProperties = util.addKeyInArray(geoProperties, 'Population (people)', 0)

  const areaKey = Object.keys(geoProperties[0]).find((key) => key.startsWith('Land Area'))
  if (areaKey) geoProperties = util.renameKeyInArray(geoProperties, areaKey, 'Land Area')
  geoProperties = util.renameKeyInArray(geoProperties, geojsonRegionCol, 'Region')
  geoProperties = util.arrangeKeysInArray(geoProperties, [...config.RESERVE_FIELDS, 'Population (people)'])
  geoProperties.sort((a, b) => a.Region.localeCompare(b.Region))

  versionSpec.data[1].values = geojsonData
  versionSpec.data[2].transform[0].fields = ['properties.' + geojsonRegionCol]

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

  let container = await embed('#map-vis', <VisualizationSpec>versionSpec, { renderer: 'svg', actions: false })
  visView = container.view
  if (props.mapColorScheme !== 'custom') visView.signal('colorScheme', props.mapColorScheme).runAsync()
}

function updateDataTable(csvData: KeyValueArray) {
  if (csvData.length === 0) return

  const areaKey = Object.keys(csvData[0]).find((key) => key.startsWith('Land Area'))
  if (areaKey) {
    var [fieldname, unit] = util.getNameUnit(areaKey)
    state.dataTable.fields[config.COL_AREA].unit = unit
    csvData = util.renameKeyInArray(csvData, areaKey, 'Land Area')
  }

  state.dataTable.items = util.filterKeyValueInArray(state.dataTable.items, config.RESERVE_FIELDS, null)
  state.dataTable.fields.splice(config.NUM_RESERVED_FILEDS)
  state.dataTable.fields[config.COL_COLOR].show = csvData[0].hasOwnProperty('Color')
  state.dataTable.fields[config.COL_AREA].show = csvData[0].hasOwnProperty('Land Area')
  state.dataTable.fields[config.COL_INSET].show = csvData[0].hasOwnProperty('Inset')
  initDataTableWArray(csvData, false)

  return {
    customColor: state.dataTable.fields[config.COL_COLOR].show,
    useEqualArea: state.dataTable.fields[config.COL_AREA].show,
    useInset: state.dataTable.fields[config.COL_INSET].show
  }
}

function changeColor(scheme: string) {
  if (scheme === 'custom') {
    if (state.dataTable.items.length && !state.dataTable.items[0].hasOwnProperty('Color')) {
      // No color assigned - Copy all color from Vega to data table
      let colorScale = visView.scale('color_group')
      for (let i = 0; i < state.dataTable.items.length; i++) {
        state.dataTable.items[i]['Color'] = colorScale(state.dataTable.items[i]['ColorGroup'])
      }
    } else {
      // Assign white to empty color
      for (let i = 0; i < state.dataTable.items.length; i++) {
        state.dataTable.items[i]['Color'] = state.dataTable.items[i]['Color']? state.dataTable.items[i]['Color'] : '#ffffff'
      }
    }

    state.dataTable.fields[config.COL_COLOR].show = true
  } else {
    for (let i = 0; i < state.dataTable.items.length; i++) {
      delete state.dataTable.items[i]['Color']
    }

    state.dataTable.fields[config.COL_COLOR].show = false
    visView.signal('colorScheme', scheme).runAsync()
  }
}

async function getCSV(isGetFile = false) {
  return await util.getGeneratedCSV(state.dataTable, isGetFile)
}

function onValueChange(rIndex: number, label: string, event: Event) {
  const target = <HTMLInputElement>event.target
  state.dataTable.items[rIndex][label] = target.value
  const changeset = visView.changeset().modify((item: any) => item.Region === state.dataTable.items[rIndex].Region, label, target.value)
  visView.change('source_csv', changeset).run()
}
</script>

<template>
  <div class="card w-75 m-2 border-0">
    <div class="p-2"><span class="badge text-bg-secondary">Input Overview</span></div>
    <div class="p-2" v-if="state.dataTable.items.length < 1">
      Please follow steps on the left panel. If you have any questions or issues about cartogram
      generation, refer to the <a href="/faq">Frequently Asked Questions</a> or
      <a href="/contact">Contact us</a>.
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
              v-else-if="field.type === 'select'"
              class="form-control"
              v-model="state.dataTable.items[rIndex][field.label]"
            >
              <option v-for="option in field.options" v-bind:value="option.value">
                {{ option.text }}
              </option>
            </select>
            <input
              v-else-if="field.show"
              class="form-control"
              v-bind:type="field.type"
              v-bind:value="state.dataTable.items[rIndex][field.label]"
              v-on:change="($event) => onValueChange(rIndex, field.label, $event)"
            />
          </td>
        </tr>
      </table>
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
