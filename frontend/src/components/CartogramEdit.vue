<script setup lang="ts">
import HTTP from '@/lib/http'
import { reactive, ref, onMounted, nextTick } from 'vue'

const props = defineProps<{
  grid_document: any
  sysname: string
}>()

const state = reactive({
  fields: [],
  items: []
})

const emit = defineEmits<{
  (e: 'change', cartogramui_promise: Promise<any>): void
}>()

onMounted(() => {
  let row, col: number

  state.fields = []
  // Header
  for (col = 0; col < props.grid_document.width; col++) {
    state.fields.push({ key: col.toString(), label: props.grid_document.contents[col] })
  }

  // Content
  state.items = []
  for (row = 1; row < props.grid_document.height; row++) {
    var data: any = {}
    for (col = 0; col < props.grid_document.width; col++) {
      data[col.toString()] = props.grid_document.contents[props.grid_document.width * row + col]
    }
    state.items.push(data)
  }

  for (let i = 0; i < props.grid_document.edit_mask.length; i++) {
    // set editable property of col
    if (props.grid_document.edit_mask[i].row === null) {
      if (typeof props.grid_document.edit_mask[i].type === 'string') {
        state.fields[props.grid_document.edit_mask[i].col].editable = true
        state.fields[props.grid_document.edit_mask[i].col].type =
          props.grid_document.edit_mask[i].type
      } else {
        state.fields[props.grid_document.edit_mask[i].col].editable =
          props.grid_document.edit_mask[i].editable
      }
    } else if (props.grid_document.edit_mask[i].row === 0 && props.grid_document.edit_mask[i].col) {
      // set editable property of header
      if (typeof props.grid_document.edit_mask[i].type === 'string') {
        state.fields[props.grid_document.edit_mask[i].col].headerEditable = true
      } else {
        state.fields[props.grid_document.edit_mask[i].col].headerEditable =
          props.grid_document.edit_mask[i].editable
      }
    }
  }
})

function updateCartogram() {
  var mime_boundary = HTTP.generateMIMEBoundary()
  var csv = ''
  for (let key in state.fields) {
    csv += '"' + state.fields[key].label.replace(/"/gm, '""') + '",'
  }
  csv = csv.substring(0, csv.length - 1) + '\n'
  for (let row in state.items) {
    for (let key in state.items[row]) {
      csv += '"' + state.items[row][key].replace(/"/gm, '""') + '",'
    }
    csv = csv.substring(0, csv.length - 1) + '\n'
  }

  // The MIME boundary can't be contained in the request body text
  while (true) {
    var search_string = csv + 'csv' + 'handler' // + handler
    if (search_string.search(mime_boundary) === -1) break

    mime_boundary = HTTP.generateMIMEBoundary()
  }

  var req_body = ''

  req_body += '--' + mime_boundary + '\n'
  req_body += 'Content-Disposition: form-data; name="handler"\n\n'
  req_body += props.sysname + '\n'

  req_body += '--' + mime_boundary + '\n'
  req_body += 'Content-Disposition: form-data; name="csv"; filename="data.csv"\n'
  req_body += 'Content-Type: text/csv\n\n'
  req_body += csv + '\n'
  req_body += '--' + mime_boundary + '--'

  var cartogramui_promise = HTTP.post('/cartogramui', req_body, {
    'Content-Type': 'multipart/form-data; boundary=' + mime_boundary
  })

  emit('change', cartogramui_promise)
}
</script>

<template>
  <div>
    <div>
      <button class="float-right" v-on:click="updateCartogram">Update Cartogram</button>
      <h2>{{ grid_document.name }}</h2>
    </div>
    <b-table :items="state.items" :fields="state.fields">
      <template v-for="(field, index) in state.fields" v-slot:[`head(${field.key})`]="data">
        <span v-if="!field.headerEditable">{{ data.label }}</span>
        <b-form-input v-else type="text" v-model="field.label"></b-form-input>
      </template>

      <template v-for="(field, index) in state.fields" v-slot:[`cell(${field.key})`]="data">
        <span v-if="!field.editable">{{ data.value }}</span>
        <b-form-input
          v-else
          v-model="state.items[data.index][field.key]"
          :type="field.type"
        ></b-form-input>
      </template>
    </b-table>
    <pre>
      {{ state.fields }}
    </pre>
    <pre>
      {{ state.items }}
    </pre>
  </div>
</template>

<style>
thead,
tbody,
tfoot,
tr,
td,
th {
  text-align: left;
  width: 100px;
  vertical-align: middle;
}
</style>
