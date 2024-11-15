<script setup lang="ts">
import type { MapHandlers } from '../../common/interface'
import CMenuSelectMap from './CMenuSelectMap.vue'
import CMenuSelectVersion from './CMenuSelectVersion.vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = withDefaults(
  defineProps<{
    isEmbed: boolean
    maps: MapHandlers
    mapTitle?: string
  }>(),
  {
    isEmbed: false
  }
)

const emit = defineEmits(['map_changed', 'version_changed', 'loading_progress', 'confirm_data'])

function onMapChanged(data: any) {
  emit('map_changed', data)
}
</script>

<template>
  <nav class="navbar bg-light p-0">
    <div class="w-100 mw-100 d-flex align-items-start">
      <div class="p-2" v-if="props.isEmbed">
        <img src="/static/img/gocart_final.svg" width="80" alt="go-cart.io logo" />
      </div>

      <c-menu-select-map
        v-bind:maps="props.maps"
        v-bind:map-title="props.mapTitle"
        v-bind:isEmbed="props.isEmbed"
        v-on:map_changed="onMapChanged"
      />

      <c-menu-select-version
        v-bind:versions="store.versions"
        v-bind:currentVersionName="store.currentVersionName"
        v-on:version_changed="(version) => emit('version_changed', version)"
      />

      <!-- Menu -->
      <div class="py-2 d-flex flex-nowrap">
        <a
          class="btn btn-primary me-2"
          title="Edit"
          v-bind:href="
            store.stringKey
              ? '/cartogram/edit/key/' + store.stringKey
              : '/cartogram/edit/map/' + store.currentMapName
          "
        >
          <i class="far fa-edit"></i>
        </a>

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
                <input type="checkbox" class="form-check-input" v-model="store.options.showGrid" />
              </div>
            </div>

            <div class="row">
              <div class="col-auto">
                <label class="form-check-label" for="gridline-toggle-cartogram"
                  >Show base map</label
                >
              </div>
              <div class="col text-end">
                <input type="checkbox" class="form-check-input" v-model="store.options.showBase" />
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
