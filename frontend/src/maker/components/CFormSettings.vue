<script setup lang="ts">
import { reactive, ref, computed, nextTick } from 'vue'
import { Tooltip } from 'bootstrap'

import * as config from '@/common/lib/config'
import * as util from '../lib/util'
import HTTP from '../lib/http'

import CSenseCheck from './CSenseCheck.vue'
import { useProjectStore } from '../stores/project'
const store = useProjectStore()

const props = defineProps<{
  disabled: boolean
}>()

const state = reactive({
  isProcessing: false,
  isExist: false,
  error: ''
})

const senseCheckRef = ref<InstanceType<typeof CSenseCheck> | null>(null)

// Columns that have a recommendation of 'area' or 'color' (not 'none')
const senseCheckColumns = computed(() => {
  return store.dataTable.fields
    .map((field, index) => ({ index, label: field.label, recommendation: field.recommendation }))
    .filter(
      (col) =>
        col.recommendation && (col.recommendation.type === 'area' || col.recommendation.type === 'color')
    ) as Array<{ index: number; label: string; recommendation: { type: string; reason: string; confidence?: number | null } }>
})

async function getRecommendations() {
  let recommendations = {} as {
    [key: string]: { type: string; reason: string }
  }
  state.isProcessing = true

  // Force include control fields when sending information
  store.dataTable.fields[config.COL_AREA].show = true
  const csvData = await util.getGeneratedCSV(store.dataTable)
  store.dataTable.fields[config.COL_AREA].show = false

  await new Promise<any>(function (resolve, reject) {
    const req_body = JSON.stringify({
      csv: csvData
    })

    HTTP.post('/api/v1/cartogram/recommend', req_body, {
      'Content-type': 'application/json'
    }).then(
      function (response: any) {
        resolve(response)
        recommendations = response
        for (let col_index = 0; col_index < store.dataTable.fields.length; col_index++) {
          if (recommendations[store.dataTable.fields[col_index].label])
            store.dataTable.fields[col_index].recommendation =
              recommendations[store.dataTable.fields[col_index].label]
        }

        state.isExist = true
        state.isProcessing = false
      },
      function (error: any) {
        reject(error)
      }
    )
  }).catch(function (error: any) {
    state.error = error
    state.isProcessing = false
    return
  })

  nextTick()
  if (state.isExist) {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(
      (tooltipTriggerEl) => new Tooltip(tooltipTriggerEl)
    )

    // Open sense-check modal if there are columns to verify
    if (senseCheckColumns.value.length > 0) {
      nextTick(() => senseCheckRef.value?.open())
    }
  }
}
</script>

<template>
  <div class="p-2">
    Project Title
    <input type="text" class="form-control" v-model="store.title" maxlength="100" />
  </div>

  <div class="p-2">
    <div class="form-check">
      <input
        id="chk-inset"
        class="form-check-input"
        type="checkbox"
        v-model="store.useInset"
        v-bind:disabled="props.disabled"
        v-on:change="store.dataTable.fields[config.COL_INSET].show = store.useInset"
      />
      <label class="form-check-label" for="chk-inset"> Define inset of specific regions </label>
    </div>
  </div>

  <div class="p-2">
    Review data and select a visualization method for each column in the "Input Overview" panel.
  </div>

  <div class="p-2">
    <span v-if="state.isExist">Check the data table for the recommendations.</span>
    <span v-else>Do not know which visualization is the best for your data?</span>
    <button
      class="btn mt-2"
      v-bind:disabled="props.disabled || state.isProcessing"
      v-bind:class="{ 'btn-primary': !state.isExist, 'btn-outline-secondary': state.isExist }"
      v-on:click="getRecommendations()"
    >
      <span v-if="state.isExist">Update</span>
      <span v-else>Get</span>
      recommendations
    </button>
    <div class="d-block invalid-feedback">{{ state.error }}</div>
    <div class="d-flex justify-content-center" v-if="state.isProcessing">
      <div class="p-2 spinner-border" role="status">
        <span class="visually-hidden">Working...</span>
      </div>
    </div>
  </div>

  <CSenseCheck
    ref="senseCheckRef"
    :columns="senseCheckColumns"
    @done="() => {}"
  />
</template>
