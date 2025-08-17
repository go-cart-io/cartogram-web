<script setup lang="ts">
import * as d3 from 'd3'
import * as XLSX from 'xlsx'
import { nextTick, reactive, ref } from 'vue'

import * as datatable from '../lib/datatable'
import * as util from '../lib/util'

import { useProjectStore } from '../stores/project'
import type { KeyValueArray } from 'maker/lib/interface'
const store = useProjectStore()

const props = withDefaults(
  defineProps<{
    disabled: boolean
  }>(),
  {
    disabled: false
  }
)

const emit = defineEmits(['changed', 'regionResolve'])

const csvRegionColSelect = ref<HTMLSelectElement | null>(null)
let csvData = [] as KeyValueArray

const state = reactive({
  selectedFileName: '',
  csvCols: [] as Array<string>,
  csvRegionCol: ''
})

defineExpose({
  reset
})

function reset() {
  csvData = []
  state.selectedFileName = ''
  state.csvCols = []
  state.csvRegionCol = ''
}

async function uploadCsvData(event: Event) {
  // TODO check region values as well as color and inset format
  const input = event.target as HTMLInputElement
  const files = input.files
  reset()
  if (!files || files.length === 0) return

  const file = files[0]
  state.selectedFileName = 'Uploading...'

  const data = await util.readFile(file)
  const type = file.name.split('.').pop()?.toLowerCase()

  if (type === 'xls' || type === 'xlsx') {
    const wb = XLSX.read(data, { type: 'array' })
    const ws = wb.Sheets[wb.SheetNames[0]]
    csvData = XLSX.utils.sheet_to_json(ws, { defval: '' })
  } else {
    // Assume CSV: decode ArrayBuffer to a UTF‑8 string before parsing
    const text = new TextDecoder('utf-8').decode(data)
    csvData = d3.csvParse(text)
  }

  // Store the file name before clearing so that selecting the same file again triggers a change event.
  state.selectedFileName = file.name
  input.value = ''

  standardizeInset()

  if ('Region' in csvData[0]) {
    state.csvRegionCol = 'Region'
    state.csvCols = []
    onRegionColChanged()
  } else {
    state.csvRegionCol = ''
    state.csvCols = Object.keys(csvData[0])

    await nextTick()
    if (csvRegionColSelect.value) {
      csvRegionColSelect.value.reportValidity()
    }
  }
}

async function onRegionColChanged() {
  if (!csvData || csvData.length < 1) return

  // Rename the column key to "Region" if "Region" key does not exist
  let newCsvData
  if (state.csvRegionCol !== 'Region')
    newCsvData = util.renameKeyInArray(csvData, state.csvRegionCol, 'Region')
  else newCsvData = csvData

  newCsvData.sort((a: { [key: string]: any }, b: { [key: string]: any }) => {
    const aRegion = (a['Region'] || '').toString()
    const bRegion = (b['Region'] || '').toString()
    return aRegion.localeCompare(bRegion)
  })

  datatable.updateDataTable(newCsvData)
  emit('changed')
}

function standardizeInset() {
  if (!('Inset' in csvData[0])) return
  for (let i = 0; i < csvData.length; i++) {
    let inset = csvData[i]['Inset'].toLowerCase().replace(/\s/g, '') // Remove space
    switch (inset) {
      case 'l':
      case 'left':
      case '(l)left':
        csvData[i]['Inset'] = 'L'
        break
      case 'r':
      case 'right':
      case '(r)right':
        csvData[i]['Inset'] = 'R'
        break
      case 't':
      case 'top':
      case '(t)top':
        csvData[i]['Inset'] = 'T'
        break
      case 'b':
      case 'bottom':
      case '(b)bottom':
        csvData[i]['Inset'] = 'B'
        break
      default:
        csvData[i]['Inset'] = ''
    }
  }
}
</script>

<template>
  <div class="p-2">
    Input your data to the table in the input overview panel<span class="d-inline d-sm-none">
      below</span
    >.
  </div>
  <div class="p-2">
    Alternatively, download data for editing on your device, then upload the edited file.
  </div>
  <div class="p-2">
    <div class="badge text-bg-secondary mb-2">Download</div>
    <div>
      <button
        class="btn btn-outline-secondary"
        v-on:click="util.getGeneratedCSV(store.dataTable, true)"
        v-bind:class="{ disabled: props.disabled }"
      >
        CSV <i class="fa-solid fa-download"></i>
      </button>
      or
      <button
        class="btn btn-outline-secondary"
        v-on:click="util.getGeneratedExcel(store.dataTable)"
        v-bind:class="{ disabled: props.disabled }"
      >
        Excel <i class="fa-solid fa-download"></i>
      </button>
    </div>
  </div>

  <div class="p-2">
    <div class="badge text-bg-secondary mb-2">Upload</div>
    <div class="mb-2">
      <label
        for="csvInput"
        class="btn btn-outline-secondary"
        v-bind:class="{ disabled: props.disabled }"
      >
        Choose file <i class="fa-solid fa-upload"></i>
      </label>
      <input
        id="csvInput"
        type="file"
        accept="text/csv,.csv,.xlsx,.xls"
        class="d-none"
        v-on:change="uploadCsvData"
      />
      <div id="csvFileName" class="small text-truncate text-muted">
        {{ state.selectedFileName || 'No file chosen' }}
      </div>
    </div>
  </div>

  <div v-if="state.csvCols.length > 0" class="p-2">
    Which column contains the region names that match your map?
    <select
      id="csvRegionColSelect"
      ref="csvRegionColSelect"
      class="form-select"
      required
      v-model="state.csvRegionCol"
      v-on:change="onRegionColChanged"
    >
      <option v-for="item in state.csvCols" v-bind:key="item">
        {{ item }}
      </option>
    </select>
  </div>

  <div v-if="store.regionWarnings.size > 0" class="p-2 bg-warning-subtle">
    <i class="fa-solid fa-triangle-exclamation text-warning"></i>
    Data regions don't match the map. Review and resolve mismatches in the "Region" column in the
    "Input Overview" panel, then apply the changes before proceeding.<br />

    <button
      class="btn btn-secondary mt-2"
      v-on:click="emit('regionResolve')"
      v-bind:class="{ disabled: props.disabled }"
    >
      Apply Changes
    </button>
  </div>
</template>
