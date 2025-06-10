<script setup lang="ts">
import * as d3 from 'd3'
import * as XLSX from 'xlsx'
import { reactive } from 'vue'

import * as util from '../lib/util'

const props = withDefaults(
  defineProps<{
    disabled: boolean
  }>(),
  {
    disabled: false
  }
)

const emit = defineEmits(['changed', 'downloadCSV', 'downloadExcel'])

const state = reactive({
  selectedFileName: ''
})

async function uploadCsvData(event: Event) {
  // TODO check region values as well as color and inset format
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return

  // Store the file name before clearing so that selecting the same file again triggers a change event.
  const file = files[0]
  state.selectedFileName = file.name
  input.value = ''

  const data = await util.readFile(file)
  const type = file.name.split('.').pop()?.toLowerCase()
  let csvData = [{}]

  if (type === 'xls' || type === 'xlsx') {
    const wb = XLSX.read(data, { type: 'array' })
    const ws = wb.Sheets[wb.SheetNames[0]]
    csvData = XLSX.utils.sheet_to_json(ws, { defval: '' })
  } else {
    // Assume CSV: decode ArrayBuffer to a UTF‑8 string before parsing
    const text = new TextDecoder('utf-8').decode(data)
    csvData = d3.csvParse(text)
  }

  if (!csvData || csvData.length < 1) return

  // Rename the first column key to "Region" if "Region" key does not exist
  if (!('Region' in csvData[0])) {
    const firstKey = Object.keys(csvData[0])[0]

    // Copy current row then add new key "Region"
    csvData = csvData.map((row) => {
      const newRow: { [key: string]: any } = { ...row }
      newRow['Region'] = newRow[firstKey]
      delete newRow[firstKey]
      return newRow
    })
  }

  csvData.sort((a: { [key: string]: any }, b: { [key: string]: any }) => {
    const aRegion = (a['Region'] || '').toString()
    const bRegion = (b['Region'] || '').toString()
    return aRegion.localeCompare(bRegion)
  })

  emit('changed', csvData)
}
</script>

<template>
  <div class="p-2">
    Input your data to the table on the right panel. Alternatively, download data for editing on
    your device, then upload the edited file.
  </div>
  <div class="p-2">
    <div class="badge text-bg-secondary mb-2">Download</div>
    <div>
      <button
        class="btn btn-outline-secondary"
        v-on:click="emit('downloadCSV')"
        v-bind:class="{ disabled: props.disabled }"
      >
        CSV <i class="fa-solid fa-download"></i>
      </button>
      or
      <button
        class="btn btn-outline-secondary"
        v-on:click="emit('downloadExcel')"
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
      <div class="text-truncate">
        {{ state.selectedFileName || 'No file chosen' }}
      </div>
    </div>

    <div class="bg-info-subtle p-1 rounded">
      Please ensure the first column contains the same region names you chose in step 1.
    </div>
  </div>
</template>
