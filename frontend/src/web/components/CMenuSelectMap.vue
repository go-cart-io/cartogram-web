<script setup lang="ts">
import * as d3 from 'd3'
import { onMounted } from 'vue'

import { RESERVE_FIELDS } from '../../common/lib/config'
import type { MapHandlers } from '../../common/lib/interface'
import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  isEmbed: boolean
  maps: MapHandlers | null
}>()

const emit = defineEmits(['map_changed'])

let mapDataURL: string | null

onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search)
  mapDataURL = null //urlParams.get('url') //TODO: enable only when there is schema verification
  switchMap()
})

async function switchMap() {
  var url = mapDataURL
    ? mapDataURL
    : store.stringKey
    ? '/static/userdata/' + store.stringKey + '/data.csv'
    : '/static/cartdata/' + store.currentMapName + '/data.csv'

  let csvdata = await d3.csv(url)
  store.versions = {}
  for (let i = 0; i < csvdata.columns.length; i++) {
    if (RESERVE_FIELDS.includes(csvdata.columns[i])) continue

    let unitMatch = csvdata.columns[i].match(/\(([^)]+)\)$/)
    let unit = unitMatch ? unitMatch[1].trim() : ''
    let name = csvdata.columns[i].replace('(' + unit + ')', '').trim()
    store.versions[i.toString()] = {
      key: i.toString(),
      header: csvdata.columns[i],
      name: name,
      unit: unit
    }
    store.currentVersionName = i.toString()
  }
  store.loadingProgress = 100

  emit('map_changed', csvdata)
}
</script>

<template>
  <div v-if="!props.isEmbed" class="d-flex p-2" style="max-width: 30%">
    <select
      class="form-select"
      v-model="store.currentMapName"
      v-on:change="switchMap"
      v-bind:disabled="store.stringKey.length > 0"
    >
      <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey">
        {{ mapItem.name }}
      </option>
    </select>
    <a
      class="btn btn-primary ms-2"
      title="Download template"
      v-bind:href="'/static/cartdata/' + store.currentMapName + '/data.csv'"
    >
      <i class="fas fa-file-download"></i>
    </a>
  </div>
</template>
