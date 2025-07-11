<script setup lang="ts">
import * as cvega from '../lib/vega'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

const props = defineProps<{
  disabled: boolean
}>()

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
  }
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
            }
          "
        />
      </div>
    </div>
    <div v-else class="mb-2">
      <label for="choroTextarea" class="form-label">
        Define scale for each choroplate data column
      </label>
      <textarea
        id="choroTextarea"
        class="form-control"
        rows="3"
        v-model="store.choroSettings.spec"
      ></textarea>
    </div>
  </div>
</template>
