<script setup lang="ts">
import type { FeatureCollection } from 'geojson'
import { ref, reactive } from 'vue'

import HTTP from '../lib/http'
import type { MapHandlers } from '../../common/interface'

const props = defineProps<{
  mapDBKey: string
  maps: MapHandlers
  geoUrl?: string
}>()

const emit = defineEmits(['changed'])
const fileEl = ref()
let geojsonData = {} as FeatureCollection

const state = reactive({
  isLoading: false,
  error: '',
  warnings: [] as Array<string>,
  handler: '',
  selectedFileName: '',
  geojsonUniqueProperties: [] as Array<string>,
  geojsonRegionCol: ''
})

async function loadGeoJson() {
  fileEl.value.value = null
  geojsonData = {} as FeatureCollection
  state.geojsonUniqueProperties = []
  if (!state.handler) return

  const basedUrl = '/static/cartdata/' + state.handler
  HTTP.get(basedUrl + '/Geographic Area.json').then(function (response: any) {
    state.geojsonRegionCol = 'Region'
    emit('changed', state.handler, response, state.geojsonRegionCol, basedUrl + '/data.csv')
  })
}

async function uploadGeoJson(event: Event) {
  geojsonData = {} as FeatureCollection
  state.geojsonUniqueProperties = []

  const input = event.target as HTMLInputElement
  const files = input.files
  state.error = ''
  if (!files || files.length == 0) return

  state.isLoading = true
  const formData = new FormData()
  formData.append('file', files[0])

  // Store the file name before clearing so that selecting the same file again triggers a change event.
  const file = files[0]
  state.selectedFileName = file.name
  input.value = ''

  const response = await new Promise<any>(function (resolve, reject) {
    HTTP.post('/api/v1/cartogram/preprocess/' + props.mapDBKey, formData).then(
      function (response: any) {
        resolve(response)
      },
      function (error: any) {
        reject(error)
      }
    )
  }).catch(function (error: any) {
    console.log(error)
    state.error = 'Unable to process your geospatial file(s): ' + error
    state.isLoading = false
    return
  })

  if (!response || !response.geojson) return
  const geojson = response.geojson
  // Check whether the GeoJSON contains any polygons or multipolygons and remove all other objects.
  if (!geojson || !geojson.features) {
    state.error = 'Invalid geospatial file'
    state.isLoading = false
    return
  }

  state.error = ''
  geojsonData = geojson
  state.geojsonUniqueProperties = response.unique
  state.geojsonRegionCol = ''
  state.handler = 'custom'
  state.isLoading = false
  state.warnings = response.warnings
  const firstUniqueProprety = state.geojsonUniqueProperties[0]
  emit('changed', state.handler, geojsonData, firstUniqueProprety, '', false)
}
</script>

<template>
  <div v-if="props.geoUrl" class="p-2">
    <input type="text" class="form-control" v-bind:value="props.geoUrl" disabled />
  </div>
  <div v-else>
    <div class="p-2">
      Select an appropriate map for your data.

      <select class="form-select" v-model="state.handler" v-on:change="loadGeoJson">
        <option></option>
        <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey" v-bind:key="mapKey">
          {{ mapItem.name }}
        </option>
      </select>
    </div>
    <div class="p-2">
      OR upload your GeoJSONs or Shapefiles (.shp, .shx, and .dbf in zip).
      <div>
        <label for="fileInput" class="btn btn-outline-secondary">
          Choose file <i class="fa-solid fa-upload"></i>
        </label>
        <input
          id="fileInput"
          ref="fileEl"
          type="file"
          accept=".geojson,.json,.zip"
          class="d-none"
          v-on:change="uploadGeoJson"
        />
        <div class="text-truncate">
          {{ state.selectedFileName || 'No file chosen' }}
        </div>
        <div class="d-block invalid-feedback">{{ state.error }}</div>
      </div>
    </div>
    <div class="d-flex justify-content-center" v-if="state.isLoading">
      <div class="p-2 spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div
      v-else
      v-for="(warning, index) in state.warnings"
      class="p-2 bg-warning-subtle"
      v-bind:key="index"
    >
      <i class="fa-solid fa-triangle-exclamation text-warning"></i> {{ warning }}
    </div>

    <div class="p-2" v-if="state.geojsonUniqueProperties.length > 0">
      Which property contain unique region names (e.g., country names)?
      <select
        class="form-select"
        v-model="state.geojsonRegionCol"
        v-on:change="emit('changed', state.handler, geojsonData, state.geojsonRegionCol)"
      >
        <option v-for="(item, index) in state.geojsonUniqueProperties" v-bind:key="index">
          {{ item }}
        </option>
      </select>
    </div>
  </div>
</template>
