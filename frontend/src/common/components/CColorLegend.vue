<script setup lang="ts">
import type { View } from 'vega'
import * as visualization from '../lib/visualization'

let colorLegendView = null as View | null

// Props: colorFields (available color columns), currentColorCol (selected column)
const props = defineProps<{
  colorFields: Array<string>
  currentColorCol: string
}>()

// Emits: 'change' event when color column changes
const emit = defineEmits(['change'])

// Expose methods for parent components
defineExpose({
  reset,
  initColorLegendWithURL,
  initColorLegendWithValues,
  resize
})

function reset(): void {
  visualization.reset('color-legend')
}

/**
 * Initialize legend using a URL (delegates to visualization helper)
 */
async function initColorLegendWithURL(
  ...args: Parameters<typeof visualization.initColorLegendWithURL>
) {
  colorLegendView = await visualization.initColorLegendWithURL(...args)
}

/**
 * Initialize legend using explicit values (delegates to visualization helper)
 */
async function initColorLegendWithValues(
  ...args: Parameters<typeof visualization.initColorLegendWithValues>
) {
  colorLegendView = await visualization.initColorLegendWithValues(...args)
}

/**
 * Resize the legend to fit its container
 */
async function resize() {
  if (!colorLegendView || !colorLegendView.container()) return
  await colorLegendView.resize()
  await colorLegendView.width(colorLegendView.container()!.offsetWidth).runAsync()
}
</script>

<template>
  <div class="d-flex w-100 h-100">
    <!-- Legend SVG will be rendered here by Vega -->
    <div id="color-legend" class="flex-grow-1 overflow-hidden vis-container"></div>

    <!-- Color column selector dropdown -->
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
        <!-- Region option -->
        <li>
          <button
            class="dropdown-item"
            v-bind:class="{ active: props.currentColorCol === 'Region' }"
            v-on:click="emit('change', 'Region')"
          >
            Region
          </button>
        </li>
        <!-- Data label -->
        <li><button class="dropdown-item disabled">Data:</button></li>
        <!-- No color column available -->
        <li v-if="!props.colorFields.length">
          <button class="dropdown-item disabled">&nbsp;&nbsp;No color column</button>
        </li>
        <!-- List color fields -->
        <li v-for="(colorField, idx) in props.colorFields" :value="colorField" :key="colorField">
          <button
            class="dropdown-item"
            v-bind:class="{ active: props.currentColorCol === colorField }"
            v-on:click="emit('change', colorField)"
          >
            &nbsp;&nbsp;{{ colorField }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
/* Ensure legend SVG fits container */
.vis-container :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>
