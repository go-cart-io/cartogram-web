<script setup lang="ts">
import { onMounted } from 'vue'
import HTTP from '../lib/http'
import type { MapHandlers, Mappack } from '../lib/interface'
import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  isEmbed: boolean
  maps: MapHandlers | null
}>()

const emit = defineEmits(['map_changed'])

onMounted(async () => {
  switchMap()
})

async function switchMap() {
  var url = store.stringKey
    ? '/mappack/' + store.stringKey
    : '/static/cartdata/' + store.currentMapName + '/mappack.json'

  var mappack = (await HTTP.get(url, null, function (e: any) {
    store.loadingProgress = Math.floor((e.loaded / e.total) * 100)
  })) as Mappack

  emit('map_changed', mappack)
}
</script>

<template>
  <div v-if="!props.isEmbed" class="d-flex p-2" style="max-width: 30%">
    <select class="form-select" v-model="store.currentMapName" v-on:change="switchMap">
      <option v-for="(mapItem, mapKey) in props.maps" v-bind:value="mapKey">
        {{ mapItem.name }}
      </option>
    </select>
    <a
      class="btn btn-primary ms-2"
      title="Download template"
      v-bind:href="'/static/cartdata/' + store.currentMapName + '/template.csv'"
    >
      <i class="fas fa-file-download"></i>
    </a>
  </div>
</template>
