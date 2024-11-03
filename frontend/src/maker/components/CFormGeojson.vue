<script setup lang="ts">
import type { FeatureCollection, Feature } from 'geojson'
import { reactive } from 'vue'

import HTTP from '../../common/lib/http'
import type { MapHandlers } from '../../common/lib/interface'
import * as util from '../lib/util'

const props = defineProps<{
  maps: MapHandlers
}>()

const emit = defineEmits(['changed'])

const state = reactive({
  error: '',
  handler: '',
  geojsonData: {} as FeatureCollection,
  geojsonRegionCol: ''
})

async function loadGeoJson(event: Event) {
  HTTP.get('/static/cartdata/' + state.handler + '/Original.json').then(function (response: any) {
    state.geojsonRegionCol = 'name'
    state.geojsonData = {} as FeatureCollection
    emit('changed', state.handler, response, state.geojsonRegionCol)
  })
}

async function uploadGeoJson(event: Event) {
  state.geojsonData = {} as FeatureCollection
  const files = (event.target as HTMLInputElement).files
  if (!files || files.length == 0) return

  try {
    var data = await util.readFile(files[0])
    var geojson = JSON.parse(data)
  } catch (err) {
    state.error = 'Invalid GeoJSON object'
    return
  }

  // Check whether the GeoJSON contains any polygons or multipolygons and remove all other objects.
  if (!geojson || !geojson.features) {
    state.error = 'Invalid GeoJSON object'
    return
  }

  const filteredFeatures = geojson.features.filter((feature: Feature) => {
    return (
      feature.geometry &&
      (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon')
    )
  })
  var filteredGeojson = { ...geojson, features: filteredFeatures }

  state.error = ''
  state.geojsonData = filteredGeojson
  state.geojsonRegionCol = ''
  state.handler = 'custom'

  emit('changed', state.handler, {}, '')
}

function updateRegionCol() {}
</script>

<template>
  <div class="p-2 text-bg-light">
    <div class="badge text-bg-secondary">1. Select map</div>
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
      OR upload your map in GeoJson format.
      <input
        class="form-control"
        v-bind:class="{ 'is-invalid': state.error }"
        type="file"
        accept="application/json,.json,.geojson"
        v-on:change="uploadGeoJson"
      />
      <div class="invalid-feedback">{{ state.error }}</div>
    </div>
    <div class="p-2" v-if="state.geojsonData.features && state.geojsonData.features[0]">
      Which column contain region names (e.g., country names)?
      <!-- TODO Only show column name with unique value -->
      <select
        class="form-select"
        v-model="state.geojsonRegionCol"
        v-on:change="emit('changed', state.handler, state.geojsonData, state.geojsonRegionCol)"
      >
        <option v-for="(index, item) in state.geojsonData.features[0].properties">
          {{ item }}
        </option>
      </select>
    </div>
  </div>
</template>
