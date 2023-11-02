<script setup lang="ts">
import { ref } from 'vue'
import * as util from '../lib/util'
import HTTP from '@/lib/http'

const props = defineProps<{
  sysname: string
}>()

const csvInput = ref<HTMLInputElement>()

const emit = defineEmits<{
  (e: 'change', cartogramui_promise: Promise<any>): void
}>()

var form_data: FormData

async function processFile() {
  form_data = new FormData()
  form_data.append('handler', props.sysname)
  if (!csvInput.value || !csvInput.value.files) return

  var input_data_file: any = csvInput.value.files[0]
  if (!input_data_file) return

  // if input file is xls/xlsx file
  if (input_data_file.name.split('.').pop().slice(0, 3) === 'xls') {
    await util.convertExcelToCSV(input_data_file).then((csv_file) => {
      input_data_file = csv_file
    })
  }

  form_data.append('csv', input_data_file)
  var cartogramui_promise = HTTP.post('/cartogramui', form_data)
  emit('change', cartogramui_promise)
}
</script>

<template>
  <button disabled
    class="btn btn-primary me-2"
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
