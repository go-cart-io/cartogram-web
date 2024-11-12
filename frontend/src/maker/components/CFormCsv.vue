<script setup lang="ts">
import * as d3 from 'd3'
import * as XLSX from 'xlsx'
import { reactive } from 'vue'

import * as util from '../lib/util'

const state = reactive({
  isReplace: true
})

const emit = defineEmits(['changed'])

async function uploadCsvData(event: Event) {
  // TODO check region values as well as color and inset format
  // TODO disable custom color and inset if the user has deleted the fields
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

  emit('changed', csvData, state.isReplace)
}
</script>

<template>
  <div class="p-2">
    <div class="badge text-bg-secondary">4. Input your data</div>
    <div class="p-2">Input your data to the table on the right panel.</div>
    <div class="p-2">
      Alternatively, upload your data in CSV or Excel format.
      <input
        ref="csvInput"
        type="file"
        class="form-control"
        accept="text/csv,.csv,.xlsx,.xls"
        v-on:change="uploadCsvData"
      />
      <!-- <div class="form-check">
        <input
          class="form-check-input"
          type="checkbox"
          id="check-replace"
          v-model="state.isReplace"
        />
        <label class="form-check-label" for="check-replace"> Replace exiting data table </label>
      </div> -->
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
</template>
