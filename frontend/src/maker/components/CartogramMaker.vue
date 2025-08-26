<script setup lang="ts">
import type { FeatureCollection } from 'geojson'
import { Toast, Modal } from 'bootstrap'
import { reactive, ref, onMounted } from 'vue'

import * as config from '../../common/config'
import * as datatable from '../lib/datatable'
import * as util from '../lib/util'
import HTTP from '../lib/http'
import type { MapHandlers } from '../../common/interface'
import { disableLeaveConfirmOnce, useLeaveConfirm } from '../composables/useLeaveConfirm'

import CFormGeojson from './CFormGeojson.vue'
import CFormCsv from './CFormCsv.vue'
import CFormSettings from './CFormSettings.vue'
import CFormCartogram from './CFormCartogram.vue'
import CFormChoropleth from './CFormChoropleth.vue'
import CVisualization from './CVisualization.vue'
import CDataTable from './CDataTable.vue'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

const mapDBKey = util.generateShareKey(32)
const csvFormEl = ref()
const visEl = ref()

const props = defineProps<{
  maps: MapHandlers
  mapName?: string
  mapTitle?: string
  geoUrl?: string
  csvUrl?: string
  mapTypes?: { [key: string]: Array<string> }
  cartoColorScheme?: string
  choroSettings?: any
}>()

const state = reactive({
  isProcessing: false,
  progressName: '',
  progressPercentage: 0,
  error: '',
  handler: props.mapName ? props.mapName : '',
  geojsonRegionCol: '',
  isInitialized: false
})

useLeaveConfirm()

onMounted(() => {
  if (!props.mapName || !props.geoUrl || !props.csvUrl) return

  store.title = props.mapTitle ? props.mapTitle : ''
  store.visTypes = props.mapTypes ? props.mapTypes : { cartogram: [], choropleth: [] }
  store.cartoColorScheme = props.cartoColorScheme ? props.cartoColorScheme : 'pastel1'
  if (props.choroSettings) store.choroSettings = props.choroSettings

  const projectedUrl = props.geoUrl.replace('/Input.json', '/Geographic Area.json')
  HTTP.get(projectedUrl).then(async function (response: any) {
    await datatable.initDataTableWGeojson(response, 'Region', props.csvUrl)
    onGeoJsonChanged(props.mapName!, response, 'Region', true)
  })
})

async function onGeoJsonChanged(
  handler: string,
  geojsonData: FeatureCollection,
  regionCol: string,
  isInitialized: boolean = true
) {
  state.handler = handler
  state.geojsonRegionCol = regionCol
  state.isInitialized = isInitialized
  await visEl.value.init(geojsonData, regionCol)

  if (isInitialized) collapseStep('1')
}

function collapseStep(step: string) {
  document.getElementById('step' + step + '-btn')?.click()
}

function isAllValid(): boolean {
  let isAllValid = true
  const elementsToValidate = document.querySelectorAll<
    HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
  >('.need-validation')

  elementsToValidate.forEach((element) => {
    // Check the element's validity based on its HTML attributes (e.g., required, minlength, type="email")
    if (!element.checkValidity()) {
      element.classList.add('is-invalid')
      element.reportValidity()
      isAllValid = false
    } else {
      element.classList.remove('is-invalid')
    }
  })

  return isAllValid
}

async function getGeneratedCartogram() {
  if (!isAllValid()) return

  if (store.regionWarnings.size > 0)
    if (
      !window.confirm(
        "Some region data don't align with the map. Click OK to continue or Cancel to review your data."
      )
    )
      return

  state.isProcessing = true
  const progressModal = new Modal('#progressBackdrop', {
    backdrop: 'static',
    keyboard: false
  })
  progressModal.show()

  // Force include control fields when generate cartogram
  store.dataTable.fields[config.COL_REGIONMAP].show = true
  store.dataTable.fields[config.COL_AREA].show = true
  const csvData = await util.getGeneratedCSV(store.dataTable)
  store.dataTable.fields[config.COL_REGIONMAP].show = false
  store.dataTable.fields[config.COL_AREA].show = false

  store.updateChoroSpec()

  await new Promise<any>(function (resolve, reject) {
    const req_body = JSON.stringify({
      title: store.title,
      scheme: store.cartoColorScheme,
      handler: state.handler,
      csv: csvData,
      geojsonRegionCol: state.geojsonRegionCol,
      visTypes: JSON.stringify(store.visTypes),
      spec: store.choroSettings.spec,
      mapDBKey: mapDBKey,
      persist: true,
      editedFrom: props.geoUrl
    })

    const progressUpdater = window.setInterval(
      (function (key) {
        return function () {
          HTTP.get(
            '/api/v1/getprogress?key=' + encodeURIComponent(key) + '&time=' + Date.now()
          ).then(function (progress: any) {
            if (progress.progress === null) {
              state.progressName = ''
              state.progressPercentage = 8
              return
            }

            state.progressName = progress.name
            state.progressPercentage = Math.floor(progress.progress * 100)
            // state.error += progress.stderr
            console.log(progress.stderr)
          })
        }
      })(mapDBKey),
      500
    )

    HTTP.post('/api/v1/cartogram', req_body, {
      'Content-type': 'application/json'
    }).then(
      function (response: any) {
        state.progressPercentage = 100
        window.clearInterval(progressUpdater)
        resolve(response)
        disableLeaveConfirmOnce()
        window.location.href = '/cartogram/key/' + response.mapDBKey + '/preview'
      },
      function (error: any) {
        state.progressPercentage = 100
        window.clearInterval(progressUpdater)
        reject(error)
      }
    )
  }).catch(function (error: any) {
    state.error = error
    progressModal.hide()
    state.isProcessing = false
    Toast.getOrCreateInstance(document.getElementById('errorToast')!).show()
    return
  })
}
</script>

<template>
  <div class="row">
    <div id="stepAccordion" class="accordion col-12 col-sm-4 col-md-3 p-0 bg-light">
      <button
        id="step1-btn"
        class="accordion-button p-2 bg-light border"
        data-bs-toggle="collapse"
        data-bs-target="#step1"
        aria-expanded="true"
        aria-controls="step1"
      >
        1. Define a map
      </button>
      <div id="step1" class="accordion-collapse collapse show p-2">
        <c-form-geojson
          v-bind:mapDBKey="mapDBKey"
          v-bind:maps="props.maps"
          v-bind:geoUrl="props.geoUrl"
          v-on:changed="onGeoJsonChanged"
          v-on:reset="
            () => {
              state.isInitialized = false
              datatable.reset()
              csvFormEl.reset()
              visEl.reset()
            }
          "
        />
      </div>

      <button
        id="step2-btn"
        class="accordion-button p-2 bg-light border"
        data-bs-toggle="collapse"
        data-bs-target="#step2"
        aria-expanded="true"
        aria-controls="step2"
      >
        2. Input your data
      </button>
      <div id="step2" class="accordion-collapse collapse show p-2">
        <c-form-csv
          ref="csvFormEl"
          v-bind:disabled="!state.isInitialized"
          v-on:changed="
            () => {
              visEl.updateData()
              if (store.regionWarnings.size <= 0) collapseStep('2')
            }
          "
          v-on:regionResolve="
            () => {
              visEl.resolveRegionIssues()
              if (store.regionWarnings.size <= 0) collapseStep('2')
            }
          "
        />
      </div>

      <button
        id="step3-btn"
        class="accordion-button p-2 bg-light border"
        data-bs-toggle="collapse"
        data-bs-target="#step3"
        aria-expanded="true"
        aria-controls="step3"
      >
        3. Specify visualization
      </button>
      <div id="step3" class="accordion-collapse collapse show p-2">
        <c-form-settings v-bind:disabled="!state.isInitialized"></c-form-settings>
      </div>

      <button
        id="step3.1-btn"
        class="accordion-button p-2 bg-light border"
        data-bs-toggle="collapse"
        data-bs-target="#step3-1"
        aria-expanded="true"
        aria-controls="step3-1"
      >
        3.1 Map/Cartogram
      </button>
      <div id="step3-1" class="accordion-collapse collapse show p-2">
        <c-form-cartogram v-bind:disabled="!state.isInitialized" />
      </div>

      <button
        id="step3.2-btn"
        class="accordion-button p-2 bg-light border"
        data-bs-toggle="collapse"
        data-bs-target="#step3-2"
        aria-expanded="true"
        aria-controls="step3-2"
      >
        3.2 Choropleth
      </button>
      <div id="step3-2" class="accordion-collapse collapse show p-2">
        <c-form-choropleth
          v-bind:disabled="!state.isInitialized"
          v-on:specChanged="visEl.refresh()"
        />
      </div>

      <button
        id="step4-btn"
        class="accordion-button p-2 bg-light border"
        data-bs-toggle="collapse"
        data-bs-target="#step4"
        aria-expanded="true"
        aria-controls="step4"
      >
        4. Generate visualization
      </button>
      <div id="step4" class="accordion-collapse collapse show p-2">
        <div class="p-2">
          <p class="bg-warning-subtle p-1 rounded">
            <span class="badge text-bg-warning">Important</span> Your data will be deleted from our
            server within 2 days unless you share and access a non-preview link. Please back up your
            original data.
          </p>
          <button
            id="generateBtn"
            class="btn btn-primary"
            v-bind:disabled="state.isProcessing || !state.isInitialized"
            v-on:click="getGeneratedCartogram"
          >
            Generate
          </button>
        </div>
      </div>
    </div>

    <div class="col-12 col-sm-8 col-md-9">
      <div class="p-2">
        <span class="badge text-bg-secondary">Input Overview</span>
      </div>
      <div class="p-2" v-if="store.dataTable.items.length < 1">
        <p>
          Please follow the steps
          <span class="d-none d-sm-inline">on the left panel</span>
          <span class="d-inline d-sm-none">above</span>. Once a step is completed, you can collapse
          the step panel for more space or re-expand it if you need to revisit it.
        </p>
        <p>
          Don't know where to start? You may try editing one of our
          <a href="/cartogram">examples</a>. If you have any questions or issues about cartogram
          generation, refer to the <a href="//guides.go-cart.io/quick-start">guides</a> or
          <a href="/contact">contact us</a>.
        </p>
      </div>

      <c-visualization ref="visEl" />

      <c-data-table
        v-if="state.isInitialized && store.dataTable.items.length > 0"
        v-on:labelChanged="visEl.updateData()"
        v-on:valueChanged="(row, col, value) => visEl.setDataItem(row, col, value)"
      />
    </div>
  </div>

  <div
    id="errorToast"
    class="toast toast position-fixed end-0 bottom-0 m-3 text-bg-danger"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    data-bs-autohide="false"
  >
    <div class="d-flex">
      <div class="toast-body">{{ state.error }}</div>
      <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  </div>

  <div class="modal" id="progressBackdrop" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-body">
          <div>Processing {{ state.progressName }}</div>
          <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100">
            <div
              class="progress-bar bg-primary"
              v-bind:style="{ width: state.progressPercentage + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
