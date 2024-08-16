<script setup lang="ts">
import { ref } from 'vue'
import * as d3 from 'd3'
import * as XLSX from 'xlsx'

import type { DataTable } from '../lib/interface'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const emit = defineEmits<{
  (e: 'change', data: DataTable): void
}>()

const csvInput = ref<HTMLInputElement>()

async function processFile() {
  if (!csvInput.value || !csvInput.value.files) return

  let data = {
    fields: [],
    items: {}
  } as DataTable

  var dataFile: any = csvInput.value.files[0]
  var dataJson: any = {}
  if (!dataFile) return

  // if input file is xls/xlsx file
  await readFile(dataFile).then((json) => {
    dataJson = json
  })

  if (!dataJson || dataJson.length < 1) return

  const colName = 0
  const colColor = 2
  const colValue = 3
  let dataKeys = Object.keys(dataJson[0])

  // Header
  data.fields = [
    { key: '0', label: 'Region', editable: false },
    { key: '1', label: 'Abbreviation', editable: true, type: 'text' },
    { key: '2', label: 'Color', editable: true, type: 'color' }
  ]
  for (let col = colValue; col < dataKeys.length; col++) {
    data.fields.push({
      key: col.toString(),
      label: dataKeys[col],
      editable: true,
      type: 'number',
      headerEditable: true
    })
  }

  // Content
  for (let row = 0; row < dataJson.length; row++) {
    let dataItem: any = [
      dataJson[row][dataKeys[0]],
      dataJson[row][dataKeys[1]],
      dataJson[row][dataKeys[2]]
    ]
    for (let col = colValue; col < dataKeys.length; col++) {
      let value = dataJson[row][dataKeys[col]]
      if (typeof value === 'string') value = parseFloat(value)
      dataItem.push(value)
    }
    data.items[row] = dataItem
  }

  emit('change', data)
}

function readFile(file: File): Promise<any> {
  return new Promise((resolve, reject) => {
    let reader = new FileReader()
    let type = file.name.split('.').pop()?.slice(0, 3)
    try {
      reader.onloadend = function (e) {
        var data = e.target?.result
        var dataJson = {}

        if (type === 'xls') {
          var wb = XLSX.read(data, { type: 'binary' })
          var ws = wb.Sheets[wb.SheetNames[0]]
          dataJson = XLSX.utils.sheet_to_json(ws)
        } else {
          dataJson = d3.csvParse(data as string)
        }

        resolve(dataJson)
      }
    } catch (e) {
      console.log(e)
      reject(Error('Given file is corrupted or incorrect format.'))
    }
    reader.readAsBinaryString(file)
  })
}
</script>

<template>
  <button
    class="btn btn-primary me-2"
    v-bind:class="{ disabled: store.isLoading }"
    v-on:click="csvInput?.click()"
    id="upload-button"
    title="Upload data"
  >
    <i class="fas fa-file-upload"></i>
  </button>

  <input
    ref="csvInput"
    type="file"
    id="csv"
    accept="text/csv,.csv,.xlsx,.xls"
    style="display: none"
    v-on:change="processFile()"
  />
</template>
