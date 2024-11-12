<script setup lang="ts">
import type { FeatureCollection, Feature } from 'geojson'
import { ref, reactive } from 'vue'

import HTTP from '../../common/lib/http'
import type { MapHandlers } from '../../common/lib/interface'

const props = defineProps<{
  maps: MapHandlers
}>()

const emit = defineEmits(['changed'])
const fileEl = ref()
var geojsonData = {} as FeatureCollection

const state = reactive({
  isLoading: false,
  error: '',
  handler: '',
  geojsonUniqueProperties: [] as Array<string>,
  geojsonRegionCol: ''
})

async function loadGeoJson(event: Event) {
  fileEl.value.value = null
  geojsonData = {} as FeatureCollection
  state.geojsonUniqueProperties = []
  if (!state.handler) return

  HTTP.get('/static/cartdata/' + state.handler + '/Original.json').then(function (response: any) {
    state.geojsonRegionCol = 'name'
    emit('changed', state.handler, response, state.geojsonRegionCol)
  })
}

async function uploadGeoJson(event: Event) {
  geojsonData = {} as FeatureCollection
  state.geojsonUniqueProperties = []
  const files = (event.target as HTMLInputElement).files
  if (!files || files.length == 0) return

  state.isLoading = true
  const formData = new FormData()
  formData.append('file', files[0])

  var response = await new Promise<any>(function (resolve, reject) {
    HTTP.post('/api/v1/cartogram/preprocess', formData).then(
      function (response: any) {
        resolve(response)
      },
      function (error: any) {
        reject(error)
      }
    )
  }).catch(function (error: any) {
    console.log(error)
    state.error = 'Unable to processs your geospatial file(s)'
    state.isLoading = false
    return
  })

  if (!response || !response.geojson) return
  var geojson = JSON.parse(response.geojson)
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

  emit('changed', state.handler, {}, '')
}

function updateRegionCol() {}
</script>

<template>
  <div class="p-2 text-bg-light">
    <div class="badge text-bg-secondary">2. Select map</div>
    <div class="p-2">
      Select an appropriate map for your data.

      <select class="form-select" v-model="state.handler" v-on:change="loadGeoJson">
        <option></option>
        <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey">
          {{ mapItem.name }}
        </option>
      </select>
    </div>
    <div class="p-2">
      OR upload your GeoJSONs or Shapefiles (.shp, .shx, and .dbf in zip).
      <input
        ref="fileEl"
        class="form-control"
        v-bind:class="{ 'is-invalid': state.error }"
        type="file"
        accept=".geojson,.json,.zip"
        v-on:change="uploadGeoJson"
      />
      <div class="invalid-feedback">{{ state.error }}</div>
    </div>
    <div class="d-flex justify-content-center" v-if="state.isLoading">
      <div class="p-2 spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div class="p-2" v-if="state.geojsonUniqueProperties.length > 0">
      Which column contain region names (e.g., country names)?
      <!-- TODO Only show column name with unique value -->
      <select
        class="form-select"
        v-model="state.geojsonRegionCol"
        v-on:change="emit('changed', state.handler, geojsonData, state.geojsonRegionCol)"
      >
        <option v-for="(item, index) in state.geojsonUniqueProperties">
          {{ item }}
        </option>
      </select>
    </div>
  </div>
</template>
