<script setup lang="ts">
import { nextTick, reactive } from 'vue'

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

const props = defineProps<{
  panelID: string
  currentVersionName: string
}>()

const emit = defineEmits(['version_changed'])

const state = reactive({
  isPlaying: false
})

function playVersions() {
  state.isPlaying = true
  const keys = Object.keys(CARTOGRAM_CONFIG.cartoVersions)
  let i = 0
  emit('version_changed', keys[i++])
  nextTick()
  const interval = setInterval(function () {
    emit('version_changed', keys[i++])
    nextTick()
    if (i >= keys.length) {
      clearInterval(interval)
      state.isPlaying = false
    }
  }, 2000)
}
</script>

<template>
  <div
    class="btn-group d-flex flex-shrink-1"
    style="min-width: 40px"
    role="group"
    aria-label="Data"
  >
    <button
      v-if="Object.keys(CARTOGRAM_CONFIG.cartoVersions).length > 2"
      class="btn btn-primary"
      v-bind:disabled="state.isPlaying"
      v-on:click="playVersions()"
    >
      <i class="fas fa-play"></i>
    </button>
    <button
      v-for="(version, index) in CARTOGRAM_CONFIG.cartoVersions"
      type="button"
      class="btn btn-outline-primary version"
      v-bind:id="props.panelID + 'toV' + index + 'Btn'"
      v-bind:class="{ active: props.currentVersionName === index.toString() }"
      v-bind:title="'Switch to ' + version.name"
      v-bind:key="index"
      v-on:click="emit('version_changed', index.toString())"
    >
      {{ version.name }}
      <i
        class="fas fa-check"
        v-if="
          CARTOGRAM_CONFIG.cartoVersions.length === 2 &&
          props.currentVersionName === index.toString()
        "
      ></i>
    </button>
  </div>
</template>

<style scoped>
button.version {
  min-width: 0;
  padding: 0.4rem 0.2rem;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
