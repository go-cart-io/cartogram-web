<script setup lang="ts">
import { reactive, onMounted } from 'vue'

import type { Mappack } from '../lib/interface'
import HTTP from '../lib/http'
import CMenuBtnUpload from './CMenuBtnUpload.vue'
import CMenuBtnEdit from './CMenuBtnEdit.vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = withDefaults(
  defineProps<{
    isEmbed: boolean
    mapName: string
    maps: Array<{ id: string; display_name: string }> | null
    grid_document: any
  }>(),
  {
    isEmbed: false
  }
)

const state = reactive({
  isPlaying: false
})

const emit = defineEmits(['map_changed', 'version_changed', 'loading_progress', 'confirm_data'])

onMounted(() => {
  store.currentMapName = props.mapName
  switchMap()
})

async function switchMap() {
  var mappack = (await HTTP.get(
    '/static/cartdata/' + store.currentMapName + '/mappack.json?v=devel',
    null,
    function (e: any) {
      store.loadingProgress = Math.floor((e.loaded / e.total) * 100)
    }
  )) as Mappack

  emit('map_changed', mappack)
}

function playVersions() {
  state.isPlaying = true
  let keys = Object.keys(store.versions)
  let i = 0
  emit('version_changed', keys[i++])
  let interval = setInterval(function () {
    emit('version_changed', keys[i++])
    if (i >= keys.length) {
      clearInterval(interval)
      state.isPlaying = false
    }
  }, 1000)
}

function confirmData(cartogramui_promise: Promise<any>) {
  emit('confirm_data', cartogramui_promise)
}
</script>

<template>
  <nav class="navbar bg-light p-0">
    <div class="w-100 mw-100 d-flex align-items-start">
      <div class="p-2" v-if="props.isEmbed">
        <img src="/static/img/gocart_final.svg" width="80" alt="go-cart.io logo" />
      </div>

      <div v-if="!props.isEmbed" class="p-2" style="max-width: 30%">
        <div class="d-flex">
          <select class="form-select" v-model="store.currentMapName" v-on:change="switchMap">
            <option v-for="map in props.maps" v-bind:value="map.id">
              {{ map.display_name }}
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
      </div>

      <div
        class="btn-group d-flex flex-shrink-1 p-2"
        style="min-width: 40px"
        role="group"
        aria-label="Data"
      >
        <button
          class="btn btn-primary"
          v-on:click="playVersions()"
          v-bind:disabled="state.isPlaying"
        >
          <i class="fas fa-play"></i>
        </button>
        <button
          v-for="(version, index) in store.versions"
          type="button"
          class="btn btn-outline-primary version"
          v-bind:class="{ active: store.currentVersionName === index.toString() }"
          v-on:click="
            () => {
              emit('version_changed', index.toString())
            }
          "
        >
          {{ version.name }}
          <i
            class="fas fa-check"
            v-if="
              store.versions.length === 2 &&
              store.currentVersionName === index.toString()
            "
          ></i>
        </button>
      </div>

      <!-- Menu -->
      <div class="py-2 d-flex flex-nowrap">
        <span v-if="!props.isEmbed" class="text-nowrap">
          <c-menu-btn-upload :mapname="store.currentMapName" v-on:change="confirmData" />
          <c-menu-btn-edit
            v-bind:grid_document="props.grid_document"
            v-bind:mapname="store.currentMapName"
            v-on:change="confirmData"
          />
        </span>

        <div class="dropdown me-2">
          <button
            class="btn btn-primary dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown"
            aria-expanded="false"
            title="Customization"
          >
            <i class="fas fa-cog"></i>
          </button>
          <div class="dropdown-menu dropdown-menu-end p-2 container" style="width: 220px">
            <div class="row">
              <div class="col-auto">
                <label class="form-check-label" for="gridline-toggle-cartogram"
                  >Show grid lines</label
                >
              </div>
              <div class="col text-end">
                <input
                  type="checkbox"
                  class="form-check-input"
                  v-model="store.options.showGrid"
                />
              </div>
            </div>

            <div class="row">
              <div class="col-auto">
                <label class="form-check-label" for="gridline-toggle-cartogram"
                  >Show base map</label
                >
              </div>
              <div class="col text-end">
                <input
                  type="checkbox"
                  class="form-check-input"
                  v-model="store.options.showBase"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
button.version {
  min-width: 0;
  padding: 0.4rem 1px;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>