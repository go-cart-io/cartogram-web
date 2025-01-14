<script setup lang="ts">
import * as d3 from 'd3'
import * as XLSX from 'xlsx'

import * as util from '../lib/util'

const props = withDefaults(
  defineProps<{
    disabled: boolean
  }>(),
  {
    disabled: false
  }
)

const emit = defineEmits(['changed'])

async function uploadCsvData(event: Event) {
  // TODO check region values as well as color and inset format
  const files = (event.target as HTMLInputElement).files
  if (!files || files.length == 0) return

  var data = await util.readFile(files[0])
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

  //   if (csvData.some((obj) => obj.hasOwnProperty('Region'))) {
  //     state.csvRegionCol = 'Region'
  //   }
  //   console.log(state.csvData)

  emit('changed', csvData)
}
</script>

<template>
  <div class="p-2 text-bg-light">
    <div class="badge text-bg-secondary">4. Input your data</div>
    <div class="p-2">Input your data to the table on the right panel.</div>
    <div class="p-2">
      Alternatively, upload your data in CSV or Excel format.
      <input
        type="file"
        class="form-control"
        accept="text/csv,.csv,.xlsx,.xls"
        v-bind:disabled="props.disabled"
        v-on:change="uploadCsvData"
      />
    </div>
  </div>
</template>
