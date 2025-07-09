<script setup lang="ts">
import * as vega from 'vega'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

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
}>()
</script>

<template>
  Region Colors
  <div class="dropdown">
    <button
      id="colorDropdownBtn"
      class="btn btn-outline-secondary dropdown-toggle w-100"
      type="button"
      data-bs-toggle="dropdown"
      aria-expanded="false"
      v-bind:disabled="props.disabled"
    >
      {{ store.cartoColorScheme }}
    </button>
    <ul id="colorDropdownList" class="dropdown-menu">
      <li>
        <a
          class="dropdown-item"
          v-bind:class="{ 'bg-secondary text-white': store.cartoColorScheme === 'custom' }"
          v-on:click="store.cartoColorScheme = 'custom'"
        >
          Custom
        </a>
      </li>
      <li
        v-for="scheme in schemeNames"
        v-bind:key="scheme"
        v-bind:class="{ 'bg-secondary': store.cartoColorScheme === scheme }"
      >
        <a class="dropdown-item" v-on:click="store.cartoColorScheme = scheme">
          <div class="d-inline swatch">
            <div
              v-for="color in schemeObject[scheme]"
              v-bind:title="color"
              v-bind:style="'background: ' + color"
              v-bind:key="color"
            ></div>
          </div>
          <span class="ms-2" v-bind:class="{ 'text-white': store.cartoColorScheme === scheme }">{{
            scheme
          }}</span>
        </a>
      </li>
    </ul>
    <small v-if="store.cartoColorScheme === 'custom'" class="text-muted">
      Go back to step 2 if needed.
    </small>
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
