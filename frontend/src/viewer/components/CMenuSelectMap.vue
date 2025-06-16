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
  mapDBKey?: string
}>()

const emit = defineEmits(['map_changed'])

let mapDataURL: string | null

onMounted(async () => {
  // const urlParams = new URLSearchParams(window.location.search)
  mapDataURL = null //urlParams.get('url') //TODO: enable only when there is schema verification
  switchMap()
})

async function switchMap() {
  const url = mapDataURL
    ? mapDataURL
    : props.mapDBKey
      ? '/static/userdata/' + props.mapDBKey + '/data.csv'
      : '/static/cartdata/' + store.currentMapName + '/data.csv'

  const csvdata = await d3.csv(url)
  store.versions = {}
  for (let i = 0; i < csvdata.columns.length; i++) {
    if (RESERVE_FIELDS.includes(csvdata.columns[i])) continue

    const unitMatch = csvdata.columns[i].match(/\(([^)]+)\)$/)
    const unit = unitMatch ? unitMatch[1].trim() : ''
    const name = csvdata.columns[i].replace('(' + unit + ')', '').trim()
    store.versions[i.toString()] = {
      key: i.toString(),
      header: csvdata.columns[i],
      name: name,
      unit: unit
    }
  }

  emit('map_changed')
}
</script>

<template>
  <div v-if="!props.isEmbed" class="d-flex p-2">
    <select
      v-if="!props.mapDBKey"
      id="mapSelect"
      class="form-select"
      v-model="store.currentMapName"
      v-on:change="switchMap"
      title="Select map"
    >
      <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey" v-bind:key="mapKey">
        {{ mapItem.name }}
      </option>
    </select>
    <span v-else>{{ props.mapTitle }}</span>
  </div>
</template>
