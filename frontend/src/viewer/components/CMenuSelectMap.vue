<script setup lang="ts">
import * as d3 from 'd3'
import { onMounted } from 'vue'

import { RESERVE_FIELDS } from '../../common/config'
import type { MapHandlers } from '../../common/interface'
import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  isEmbed: boolean
  maps: MapHandlers | null
  mapTitle?: string
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
  }

  emit('map_changed', csvdata)
}
</script>

<template>
  <div v-if="!props.isEmbed" class="d-flex p-2" style="max-width: 30%">
    <select
      v-if="!store.stringKey"
      class="form-select"
      v-model="store.currentMapName"
      v-on:change="switchMap"
    >
      <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey">
        {{ mapItem.name }}
      </option>
    </select>
    <span v-else>{{ props.mapTitle }}</span>
  </div>
</template>
