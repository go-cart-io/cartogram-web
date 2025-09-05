<script setup lang="ts">
import { computed, toRaw } from 'vue'

import * as config from '../../common/config'
import * as util from '../lib/util'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

const emit = defineEmits(['labelChanged', 'valueChanged'])

// Sample from uploaded data that cannot be matched with the map
const sampleRegionDataKey = computed<string[]>(() => {
  const keys: string[] = []
  const regionData = store.regionData[0]

  for (const key in regionData) {
    if (
      Object.prototype.hasOwnProperty.call(regionData, key) &&
      !config.RESERVE_FIELDS.includes(key)
    ) {
      keys.push(key)
      if (keys.length === 2) break
    }
  }
  return keys
})

function addColumn() {
  const index = store.dataTable.fields.findIndex((item) => item.name === '')
  if (index > -1) {
    const nameInput = document.getElementById('dtable-name-' + index) as HTMLInputElement
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

function removeColumn(index: number) {
  if (
    !window.confirm(
      'Click "OK" to remove the column. The changes cannot be undone unless re-uploading the data.'
    )
  )
    return

  const visType = store.dataTable.fields[index].vis
  if (visType) {
    store.visTypes[visType] = store.visTypes[visType].filter(
      (item) => item !== store.dataTable.fields[index].label
    )
  }

  const key = store.dataTable.fields[index].label
  store.dataTable.fields.splice(index, 1)
  store.dataTable.items = util.deleteKeysInArray(store.dataTable.items, key)

  emit('labelChanged')
}

function updateVisType(index: number, event: Event) {
  const selectElement = event.target as HTMLSelectElement
  const oldType = store.dataTable.fields[index].vis
  const newType = selectElement.value
  if (oldType === newType) return

  if (!store.visTypes[newType]) store.visTypes[newType] = []

  // Check limitation
  if (
    newType === 'cartogram' &&
    CARTOGRAM_CONFIG.maxCartogram &&
    !isNaN(CARTOGRAM_CONFIG.maxCartogram) &&
    store.visTypes['cartogram'].length >= CARTOGRAM_CONFIG.maxCartogram
  ) {
    selectElement.value = ''
    store.dataTable.fields[index].vis = ''
    alert(
      'Limit of ' +
        CARTOGRAM_CONFIG.maxCartogram +
        ' cartograms per data set. For unlimited use, consider running Go-Cart locally with Docker (see https://guides.go-cart.io/#/tutorials/local).'
    )
    return
  }

  if (oldType)
    // Remove from existing list
    store.visTypes[oldType] = store.visTypes[oldType].filter(
      (item) => item !== store.dataTable.fields[index].label
    )

  // Update the list and data table
  store.visTypes[newType].push(store.dataTable.fields[index].label)
  store.visTypes[newType].sort()
  store.dataTable.fields[index].vis = newType
}

function updateLabel(index: number, event: Event) {
  if (!validateInput(event)) return

  const oldLabel = store.dataTable.fields[index].label
  store.dataTable.fields[index].name = store.dataTable.fields[index].name.trim()
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

  // Update color column
  if (store.currentColorCol === oldLabel) store.currentColorCol = newLabel

  emit('labelChanged')
}

function onValueChange(rIndex: number, label: string, event: Event) {
  const target = <HTMLInputElement>event.target
  store.dataTable.items[rIndex][label] = target.value
  emit('valueChanged', store.dataTable.items[rIndex].Region, label, target.value)
}

function validateInput(event: Event) {
  const inputElement = event.target as HTMLInputElement
  if (!inputElement.checkValidity()) {
    inputElement.reportValidity()
    return false
  }
  inputElement.classList.remove('is-invalid')
  return true
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
              class="form-select need-validation"
              v-if="field.editableHead && field.name !== 'Geographic Area'"
              required
              v-bind:id="'dtable-vis-' + index"
              v-bind:value="store.dataTable.fields[index].vis"
              v-bind:disabled="store.choroSettings.isAdvanceMode"
              v-on:blur="validateInput"
              v-on:change="updateVisType(index, $event)"
            >
              <option value="" selected disabled>Select visualization</option>
              <option
                v-for="(option, value) in { Area: 'Cartogram', Color: 'Choropleth' }"
                v-bind:value="option.toLowerCase()"
                v-bind:key="option"
              >
                {{ value }}: {{ option }}
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
            <span v-if="!field.editableHead">{{ field.label }}</span>
            <div class="position-relative" v-else>
              <i
                v-if="
                  store.dataTable.fields[index].name !== 'Geographic Area' &&
                  !store.choroSettings.isAdvanceMode
                "
                class="position-absolute top-0 end-0 btn-icon text-secondary fas fa-minus-circle"
                v-bind:title="'Remove ' + store.dataTable.fields[index].name + ' column'"
                v-on:click="removeColumn(index)"
              ></i>
              <input
                class="form-control need-validation"
                placeholder="Data name"
                title='Data Name. Cannot contain \ / : * ? &#39; " &lt; &gt; |'
                pattern='^[^\\\/:\*\?&#39;"&lt;&gt;\|]+$'
                required
                v-model="store.dataTable.fields[index].name"
                v-bind:id="'dtable-name-' + index"
                v-bind:disabled="store.choroSettings.isAdvanceMode"
                v-on:change="updateLabel(index, $event)"
              />
              <input
                class="form-control"
                placeholder="Unit"
                title='Data Unit. Cannot contain \ / : * ? &#39; " &lt; &gt; |'
                pattern='^[^\\\/:\*\?&#39;"&lt;&gt;\|]+$'
                v-model="store.dataTable.fields[index].unit"
                v-bind:id="'dtable-unit-' + index"
                v-bind:disabled="store.choroSettings.isAdvanceMode"
                v-on:change="updateLabel(index, $event)"
              />
            </div>
          </th>
        </tr>
      </thead>
      <tr v-for="(row, rIndex) in store.dataTable.items" v-show="row.Region" v-bind:key="rIndex">
        <td v-for="(field, index) in store.dataTable.fields" v-show="field.show" v-bind:key="index">
          <div>
            <!-- Select action if the map regions and the uploaded data's regions mismatched -->
            <select
              v-if="field.label === 'Region' && store.regionWarnings.has(rIndex)"
              class="form-select"
              v-bind:id="'dtable-region-' + rIndex"
            >
              <option disabled selected>Choose action</option>
              <option disabled>Keep original name and values:</option>
              <option v-bind:value="row[field.label]" v-bind:key="row[field.label]">
                = {{ row[field.label] }}
              </option>
              <option disabled>Drop the region from map and data:</option>
              <option value="dropRegion">x {{ row[field.label] }}</option>
              <option disabled>Rename region and use values from:</option>
              <option
                v-for="(data, index) in store.regionData"
                v-bind:value="index"
                v-bind:key="data.Region"
              >
                &gt; {{ data.Region }} ({{
                  sampleRegionDataKey.map((key) => key + ': ' + data[key]).join(', ')
                }}, ...)
              </option>
            </select>
            <!-- Other field types -->
            <span v-else-if="!field.editable">{{ row[field.label] }}</span>
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
              v-else
              class="form-control"
              v-bind:id="'dtable-cell-' + rIndex + '-' + index"
              v-bind:type="field.type"
              v-bind:value="store.dataTable.items[rIndex][field.label]"
              v-on:change="($event: any) => onValueChange(rIndex, field.label, $event)"
            />
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
</style>
