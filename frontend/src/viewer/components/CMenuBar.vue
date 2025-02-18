<script setup lang="ts">
import type { MapHandlers } from '../../common/interface'
import CMenuSelectMap from './CMenuSelectMap.vue'
import CMenuBtnShare from './CMenuBtnShare.vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = withDefaults(
  defineProps<{
    isEmbed: boolean
    maps: MapHandlers
    mapTitle?: string
    mapDBKey?: string
  }>(),
  {
    isEmbed: false
  }
)

const emit = defineEmits(['map_changed'])

function onMapChanged(data: any) {
  emit('map_changed', data)
}
</script>

<template>
  <nav class="navbar bg-light p-0">
    <div class="w-100 mw-100 d-flex justify-content-between">
      <div class="p-2" v-if="props.isEmbed">
        <img src="/static/img/gocart_final.svg" width="80" alt="go-cart.io logo" />
      </div>

      <c-menu-select-map
        v-bind:maps="props.maps"
        v-bind:mapTitle="props.mapTitle"
        v-bind:mapDBKey="props.mapDBKey"
        v-bind:isEmbed="props.isEmbed"
        v-on:map_changed="onMapChanged"
      />

      <!-- Menu -->
      <div class="py-2 d-flex flex-nowrap">
        <a
          class="btn btn-primary me-2 d-flex align-items-center"
          title="Edit cartogram"
          v-bind:href="
            props.mapDBKey
              ? '/cartogram/edit/key/' + props.mapDBKey
              : '/cartogram/edit/map/' + store.currentMapName
          "
        >
          <span class="d-none d-md-block me-2">Edit</span>
          <i class="far fa-edit"></i>
        </a>

        <c-menu-btn-share v-bind:mapDBKey="props.mapDBKey" />

        <div class="dropdown me-2 d-flex">
          <button
            class="btn btn-primary dropdown-toggle d-flex align-items-center"
            type="button"
            data-bs-toggle="dropdown"
            aria-expanded="false"
            title="Customize cartogram viewer"
          >
            <span class="d-none d-md-block me-2">Customize</span>
            <i class="fas fa-cog"></i>
          </button>
          <div class="dropdown-menu dropdown-menu-end p-2 container" style="width: 250px">
            <div class="row">
              <div class="col-8">
                <label class="form-check-label" for="gridline-toggle-cartogram"
                  >Show grid lines</label
                >
              </div>
              <div class="col-4 text-end">
                <input type="checkbox" class="form-check-input" v-model="store.options.showGrid" />
              </div>
            </div>

            <div class="row">
              <div class="col-8">
                <label class="form-check-label" for="gridline-toggle-cartogram"
                  >Number of panels</label
                >
              </div>
              <div class="col-4 text-end">
                <select class="form-select" v-model="store.options.numberOfPanels">
                  <option v-for="number in [1, 2, 3, 4, 5]" v-bind:key="number" v-bind:value="number">
                    {{ number }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
