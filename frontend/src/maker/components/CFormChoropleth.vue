<script setup lang="ts">
import Ajv from 'ajv'
import addFormats from 'ajv-formats'
import vegaSchema from 'vega/build/vega-schema.json'

import * as cvega from '../lib/vega'

import { useProjectStore } from '../stores/project'
import { reactive } from 'vue'
const store = useProjectStore()

const props = defineProps<{
  spec: string
  disabled: boolean
}>()

const state = reactive({
  spec: props.spec,
  error: ''
})

const emit = defineEmits(['specChanged'])

const ajv = new Ajv({
  allErrors: true,
  verbose: true
})
addFormats(ajv)
const vegaValidator = ajv.compile(vegaSchema)

function switchMode() {
  if (store.choroSettings.isAdvanceMode) {
    // Switch from advance to simple
    if (
      window.confirm(
        'Advance configuration will be lost. Are you sure you want to quit advance mode?'
      )
    ) {
      store.choroSettings.isAdvanceMode = false
    } else {
      // Do nothing
    }
  } else {
    // Switch from simple to advance
    store.updateChoroSpec()
    store.choroSettings.isAdvanceMode = true
    state.spec = store.choroSettings.spec
  }
}

function applySpec() {
  state.error = ''
  try {
    const specJson = JSON.parse(state.spec) as any
    if (typeof specJson !== 'object' || specJson === null) {
      state.error = 'Error: JSON root node must be an object.'
      return false
    }

    // Validate vega specification
    const valid = vegaValidator(specJson)
    if (!valid) {
      for (const error of vegaValidator.errors ?? []) {
        state.error += `Error: ${error.instancePath ?? '/'} ${error.message}. `
      }
      return false
    }

    if (!validScales(specJson)) return false
  } catch (e) {
    state.error = 'Error: Specification must be valid json'
    return false
  }

  store.choroSettings.spec = state.spec
  emit('specChanged')
}

function validScales(specJson: any) {
  if (!specJson['scales']) {
    state.error = `Error: The scales must be defined.`
    return false
  }

  const scalesArray = (specJson as { scales: unknown }).scales as Array<any>
  const foundScaleNames = new Set<string>()
  const choroplethNamesSet = new Set(store.visTypes['choropleth'])

  // Iterate through each item in the 'scales' array and validate its structure
  for (let i = 0; i < scalesArray.length; i++) {
    const item = scalesArray[i]

    // Validate name and domain.field match
    if (
      item.hasOwnProperty('name') &&
      item.hasOwnProperty('domain') &&
      item.domain.hasOwnProperty('field') &&
      item.name !== item.domain.field
    ) {
      state.error = `Error: Item at scales[${i}]: 'name' ('${item.name}') must exactly match 'domain.field' ('${item.domain.field}').`
      return false
    }

    // Validate domain.data is "source_csv"
    if (
      item.hasOwnProperty('domain') &&
      item.domain.hasOwnProperty('data') &&
      item.domain.data !== 'source_csv'
    ) {
      state.error = `Error: Item at scales[${i}]: 'domain.data' must be "source_csv", but found '${item.domain.data}'.`
      return false
    }

    // Check if the 'name' is one of the valid names
    if (!choroplethNamesSet.has(item.name)) {
      state.error = `Error: Item at scales[${i}]: 'name' ('${item.name}') is not in the data columns.`
      return false
    }

    // Check for duplicate 'name' entries within the 'scales' array
    if (foundScaleNames.has(item.name)) {
      state.error = `Error: Duplicate 'name' found in 'scales' array: '${item.name}'.`
      return false
    }

    // Add the name to our set of found names
    foundScaleNames.add(item.name)
  }

  // Ensure the set of found names exactly matches the set of choropleth columns (ignoring order).
  // This means checking both size and if all expected names are present in the found names.
  if (foundScaleNames.size !== choroplethNamesSet.size) {
    state.error = `Error: Mismatch in the number of unique 'scales' names. Expected ${choroplethNamesSet.size}, but found ${foundScaleNames.size}.`
    return false
  }

  // Check if every expected name is present in the found names
  for (const expectedName of choroplethNamesSet) {
    if (!foundScaleNames.has(expectedName)) {
      state.error = `Error: Expected scale name '${expectedName}' is missing from the 'scales' array.`
      return false
    }
  }

  return true
}
</script>

<template>
  <div
    v-if="!store.visTypes['choropleth'] || store.visTypes['choropleth'].length <= 0"
    class="mb-2"
  >
    To enable visualization options, select visualization as "Choropleth" for at least one data
    column.
  </div>
  <div v-else>
    <div class="mb-2 form-check form-switch">
      <input
        id="modeSwitch"
        class="form-check-input"
        type="checkbox"
        role="switch"
        v-bind:checked="store.choroSettings.isAdvanceMode"
        v-on:change="switchMode"
      />
      <label class="form-check-label" for="modeSwitch">Advance mode</label>
    </div>
    <div v-if="!store.choroSettings.isAdvanceMode">
      <div class="mb-2">
        <label for="choroColorSelect">
          Scale Colors
          <small>
            (<a href="//vega.github.io/vega/docs/schemes/" target="_blank">examples</a>)
          </small>
        </label>
        <select
          id="choroColorSelect"
          class="form-select"
          v-model="store.choroSettings.scheme"
          v-bind:disabled="props.disabled"
          v-on:change="emit('specChanged')"
        >
          <option disabled>Sequential Single-Hue</option>
          <option v-for="scheme in cvega.sequentialSingleHueSchemes" v-bind:value="scheme">
            {{ scheme }}
          </option>
          <option disabled>----------------</option>
          <option disabled>Sequential Multi-Hue</option>
          <option v-for="scheme in cvega.sequentialMultiHueSchemes" v-bind:value="scheme">
            {{ scheme }}
          </option>
          <option disabled>----------------</option>
          <option disabled>Diverging</option>
          <option v-for="scheme in cvega.divergingSchemes" v-bind:value="scheme">
            {{ scheme }}
          </option>
        </select>
      </div>
      <div class="mb-2">
        <label for="choroTypeSelect">Scale Type</label>
        <select
          id="choroTypeSelect"
          class="form-select"
          v-model="store.choroSettings.type"
          v-bind:disabled="props.disabled"
          v-on:change="emit('specChanged')"
        >
          <option v-for="type in cvega.scaleTypeDiscretizing" v-bind:value="type">
            {{ type }}
          </option>
        </select>
      </div>
      <div class="mb-2" v-if="cvega.scaleTypeDiscretizing.includes(store.choroSettings.type)">
        <label for="choroStepInput">Steps</label>
        <input
          id="choroStepInput"
          class="form-control"
          type="number"
          min="1"
          step="1"
          v-model="store.choroSettings.step"
          v-bind:disabled="props.disabled"
          v-on:change="
            () => {
              store.choroSettings.step = Math.abs(Math.round(store.choroSettings.step))
              emit('specChanged')
            }
          "
        />
      </div>
    </div>
    <div v-else class="mb-2">
      <label for="choroTextarea" class="form-label">
        Define scale for each choropleth data column using
        <a href="https://vega.github.io/vega/docs/scales/" target="_blank">vega specification</a>.
        Futhermore, you may modify the legend title of each data column.
      </label>
      <textarea
        id="choroTextarea"
        class="form-control"
        rows="3"
        v-model="state.spec"
        v-bind:class="{ 'is-invalid': state.error }"
        v-on:change="applySpec()"
      ></textarea>
      <div class="d-block invalid-feedback">{{ state.error }}</div>
    </div>
  </div>
</template>
