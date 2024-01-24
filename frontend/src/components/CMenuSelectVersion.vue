<script setup lang="ts">
import { reactive } from 'vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const emit = defineEmits(['version_changed'])

const state = reactive({
  isPlaying: false
})

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
</script>

<template>
  <div
    class="btn-group d-flex flex-shrink-1 p-2"
    style="min-width: 40px"
    role="group"
    aria-label="Data"
  >
    <button
      v-if="Object.keys(store.versions).length > 2"
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
        v-if="store.versions.length === 2 && store.currentVersionName === index.toString()"
      ></i>
    </button>
  </div>
</template>
