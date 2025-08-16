<script setup lang="ts">
import { onMounted, reactive } from 'vue'

import CMenuColor from './CMenuColor.vue'
import CMenuBtnShare from './CMenuBtnShare.vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

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
    <div class="d-flex flex-wrap flex-sm-nowrap w-100 p-2 gap-2">
      <!-- Title or Map selector -->
      <div
        v-if="!CARTOGRAM_CONFIG.mapDBKey || CARTOGRAM_CONFIG.mapTitle"
        class="order-1 d-flex align-items-center"
        style="min-width: 100px; max-width: 50%"
      >
        <select
          v-if="!CARTOGRAM_CONFIG.mapDBKey"
          id="mapSelect"
          class="form-select"
          v-model="store.currentMapName"
          v-on:change="switchMap"
          title="Select map"
        >
          <option
            v-for="(mapItem, mapKey) in CARTOGRAM_CONFIG.maps"
            v-bind:value="mapKey"
            v-bind:key="mapKey"
          >
            {{ mapItem.name }}
          </option>
        </select>
        <strong v-else class="text-truncate">{{ CARTOGRAM_CONFIG.mapTitle }}</strong>
      </div>
      <div v-else class="order-1 flex-grow-1"></div>

      <!-- Color selector -->
      <c-menu-color v-bind:key="state.mapkey" />

      <!-- Menu -->
      <div class="order-3 d-flex flex-nowrap gap-2">
        <div class="dropdown d-flex">
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
          <div class="dropdown-menu dropdown-menu-end p-2 container">
            <div class="row mb-2">
              <label class="form-check-label" for="optionsGridline">Grid lines opacity</label>
              <div>
                <input
                  id="optionsGridline"
                  type="range"
                  class="form-range"
                  min="0"
                  max="0.5"
                  step="0.1"
                  v-model="store.options.gridOpacity"
                />
              </div>
            </div>

            <div class="row mb-2">
              <label class="form-label" for="optionsPanels">Number of panels</label>
              <div>
                <select
                  id="optionsPanels"
                  class="form-select"
                  v-model="store.options.numberOfPanels"
                  title="Select number of panels"
                >
                  <option
                    v-for="number in [1, 2, 3, 4, 5]"
                    v-bind:key="number"
                    v-bind:value="number"
                  >
                    {{ number }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div class="vr"></div>

        <a
          class="btn btn-primary d-flex align-items-center"
          title="Edit cartogram"
          v-bind:href="
            CARTOGRAM_CONFIG.mapDBKey
              ? '/cartogram/edit/key/' + CARTOGRAM_CONFIG.mapDBKey
              : '/cartogram/edit/map/' + store.currentMapName
          "
        >
          <span class="d-none d-lg-block me-2">Edit</span>
          <i class="far fa-edit"></i>
        </a>

        <c-menu-btn-share />
      </div>
    </div>
  </nav>
</template>
