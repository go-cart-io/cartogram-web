<script setup lang="ts">
import type { View } from 'vega'
import * as visualization from '../visualization'

let colorLegendView: View

const props = defineProps<{
  colorFields: Array<string>
  currentColorCol: string
}>()

const emit = defineEmits(['change'])

async function initLegendWithURL(...args: Parameters<typeof visualization.initLegendWithURL>) {
  colorLegendView = await visualization.initLegendWithURL(...args)
}

async function initLegendWithValues(...args: Parameters<typeof visualization.initLegendWithURL>) {
  colorLegendView = await visualization.initLegendWithValues(...args)
}

async function resize() {
  if (!colorLegendView || !colorLegendView.container()) return
  await colorLegendView.resize()
  await colorLegendView.width(colorLegendView.container()!.offsetWidth).runAsync()
}

defineExpose({
  initLegendWithURL,
  initLegendWithValues,
  resize
})
</script>

<template>
  <div class="d-flex w-100 h-100">
    <!-- Legend -->
    <div id="legend" class="flex-grow-1 overflow-hidden" style="min-width: 0"></div>

    <!-- Color column selector -->
    <div class="dropdown">
      <button
        class="btn btn-primary dropdown-toggle"
        type="button"
        data-bs-toggle="dropdown"
        title="Select map/cartogram color strategy"
      >
        <span class="d-none d-lg-inline me-2">Color</span>
        <i class="fas fa-palette"></i>
      </button>
      <ul class="dropdown-menu dropdown-menu-end">
        <li>
          <button
            class="dropdown-item"
            v-bind:class="{ active: props.currentColorCol === 'Region' }"
            v-on:click="emit('change', 'Region')"
          >
            Region
          </button>
        </li>
        <li><button class="dropdown-item disabled">Data:</button></li>
        <li v-if="!props.colorFields.length">
          <button class="dropdown-item disabled">&nbsp;&nbsp;No color column</button>
        </li>
        <li
          v-for="(versionItem, versionKey) in props.colorFields"
          v-bind:value="versionItem"
          v-bind:key="versionKey"
        >
          <button
            class="dropdown-item"
            v-bind:class="{ active: props.currentColorCol === versionItem }"
            v-on:click="emit('change', versionItem)"
          >
            &nbsp;&nbsp;{{ versionItem }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
#legend :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>
