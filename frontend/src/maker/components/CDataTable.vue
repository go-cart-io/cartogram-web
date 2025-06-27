<script setup lang="ts">
import { toRaw } from 'vue'

import * as util from '../lib/util'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

const emit = defineEmits(['labelChanged', 'valueChanged'])

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
    vis: '',
    editable: true,
    editableHead: true,
    show: true
  })
  store.dataTable.items = util.addKeyInArray(toRaw(store.dataTable.items), label, 0)
}

function updateVisType(index: number, event: Event) {
  const selectElement = event.target as HTMLSelectElement
  const oldType = store.dataTable.fields[index].vis
  const newType = selectElement.value
  if (oldType === newType) return

  // Remove from existing list
  if (oldType)
    store.visTypes[oldType] = store.visTypes[oldType].filter(
      (item) => item !== store.dataTable.fields[index].label
    )

  store.visTypes[newType].push(store.dataTable.fields[index].label)
  store.visTypes[newType].sort()
  store.dataTable.fields[index].vis = newType
}

function updateLabel(index: number) {
  const oldLabel = store.dataTable.fields[index].label
  let newLabel = store.dataTable.fields[index].name
  if (store.dataTable.fields[index].unit)
    newLabel = newLabel + ' (' + store.dataTable.fields[index].unit + ')'

  // Update data table
  store.dataTable.fields[index].label = newLabel
  store.dataTable.items = util.renameKeyInArray(toRaw(store.dataTable.items), oldLabel, newLabel)

  // Update label in vis type
  const visTpe = store.dataTable.fields[index].vis
  if (visTpe)
    store.visTypes[visTpe] = store.visTypes[visTpe].map((item) => item.replace(oldLabel, newLabel))

  emit('labelChanged')
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
  emit('valueChanged', store.dataTable.items[rIndex].Region, label, target.value)
}
</script>

<template>
  <div class="d-table p-2">
    <button class="btn btn-outline-secondary mb-2 float-end" v-on:click="addColumn">
      <span class="d-inline d-sm-none d-md-inline">Add column </span>
      <i class="btn-icon fas fa-plus-circle"></i>
    </button>
    <table class="table table-bordered">
      <thead>
        <tr class="table-light">
          <th
            v-for="(field, index) in store.dataTable.fields"
            v-show="field.show"
            v-bind:key="index"
          >
            <select
              class="form-select"
              v-if="field.editableHead"
              required
              v-bind:id="'formFieldVis' + index"
              v-bind:value="store.dataTable.fields[index].vis"
              v-on:blur="validateInput"
              v-on:change="updateVisType(index, $event)"
            >
              <option value="" selected disabled>Select visualization</option>
              <option
                v-for="option in ['Cartogram', 'Choropleth']"
                v-bind:value="option.toLowerCase()"
                v-bind:key="option"
              >
                {{ option }}
              </option>
            </select>
          </th>
        </tr>
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
