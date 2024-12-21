<script setup lang="ts">
import { reactive } from 'vue'
import * as vega from 'vega'

const schemeNames = [
  'accent',
  'category10',
  'category20',
  'category20b',
  'category20c',
  'dark2',
  'paired',
  'pastel1',
  'pastel2',
  'set1',
  'set2',
  'set3',
  'tableau10',
  'tableau20',
  'observable10'
]
const schemeObject = schemeNames.reduce((acc: any, name: string) => {
  acc[name] = vega.scheme(name)
  return acc
}, {})

const props = defineProps<{
  disabled: boolean
  scheme: string
}>()

const state = reactive({
  scheme: props.scheme
})

const emit = defineEmits(['changed'])

function changeScheme(scheme: string) {
  state.scheme = scheme
  emit('changed', state.scheme)
}
</script>

<template>
  Color
  <div class="dropdown">
    <button
      class="btn btn-outline-secondary dropdown-toggle w-100"
      type="button"
      data-bs-toggle="dropdown"
      aria-expanded="false"
      v-bind:disabled="props.disabled"
    >
      {{ state.scheme }}
    </button>
    <ul class="dropdown-menu">
      <li>
        <a
          class="dropdown-item"
          v-bind:class="{ 'bg-secondary text-white': 'custom' === state.scheme }"
          v-on:click="changeScheme('custom')"
          >Custom</a
        >
      </li>
      <li
        v-for="scheme in schemeNames"
        :key="scheme"
        v-bind:class="{ 'bg-secondary': scheme === state.scheme }"
      >
        <a class="dropdown-item" v-on:click="changeScheme(scheme)">
          <div class="d-inline swatch">
            <div
              v-for="color in schemeObject[scheme]"
              v-bind:title="color"
              v-bind:style="'background: ' + color"
            ></div>
          </div>
          <span class="ms-2" v-bind:class="{ 'text-white': scheme === state.scheme }">{{
            scheme
          }}</span>
        </a>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.swatch div {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 1px solid white;
}
</style>
