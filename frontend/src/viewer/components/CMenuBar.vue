<script setup lang="ts">
import { onMounted, reactive } from 'vue'

import type { MapHandlers } from '../../common/interface'
import CMenuColor from './CMenuColor.vue'
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

const state = reactive({
  mapkey: -1
})

const emit = defineEmits(['map_changed'])

onMounted(async () => {
  switchMap()
})

function switchMap() {
  state.mapkey = Date.now()
  emit('map_changed')
}
</script>

<template>
  <nav class="navbar bg-light p-0">
    <div class="w-100 mw-100 d-flex justify-content-between">
      <div class="p-2" v-if="props.isEmbed">
        <img src="/static/img/gocart_final.svg" width="80" alt="go-cart.io logo" />
      </div>

      <div v-if="!props.isEmbed" class="d-flex p-2" style="max-width: 20%">
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

      <c-menu-color v-bind:mapDBKey="props.mapDBKey" v-bind:key="state.mapkey" />

      <div class="dropdown d-flex py-2 me-2">
        <button
          class="btn btn-primary dropdown-toggle d-flex align-items-center"
          type="button"
          data-bs-toggle="dropdown"
          aria-expanded="false"
          title="Customize cartogram viewer"
        >
          <span class="d-none d-lg-block me-2">Customize</span>
          <i class="fas fa-cog"></i>
        </button>
        <div class="dropdown-menu dropdown-menu-end p-2 container" style="width: 250px">
          <div class="row">
            <div class="col-8">
              <label class="form-check-label" for="optionsGridline">Show grid lines</label>
            </div>
            <div class="col-4 text-end">
              <input
                id="optionsGridline"
                type="checkbox"
                class="form-check-input"
                v-model="store.options.showGrid"
                title="Toggle grid lines"
              />
            </div>
          </div>

          <div class="row">
            <div class="col-8">
              <label class="form-label" for="optionsPanels">Number of panels</label>
            </div>
            <div class="col-4 text-end">
              <select
                id="optionsPanels"
                class="form-select"
                v-model="store.options.numberOfPanels"
                title="Select number of panels"
              >
                <option v-for="number in [1, 2, 3, 4, 5]" v-bind:key="number" v-bind:value="number">
                  {{ number }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="vr my-2 me-2"></div>

      <!-- Menu -->
      <div class="d-flex flex-nowrap py-2">
        <a
          class="btn btn-primary me-2 d-flex align-items-center"
          title="Edit cartogram"
          v-bind:href="
            props.mapDBKey
              ? '/cartogram/edit/key/' + props.mapDBKey
              : '/cartogram/edit/map/' + store.currentMapName
          "
        >
          <span class="d-none d-lg-block me-2">Edit</span>
          <i class="far fa-edit"></i>
        </a>

        <c-menu-btn-share v-bind:mapDBKey="props.mapDBKey" />
      </div>
    </div>
  </nav>
</template>
