<script setup lang="ts">
import { Tooltip } from 'bootstrap'
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps<{
  title: string
}>()

const tooltipButton = ref(null)
let tooltip = null as any

onMounted(() => {
  // Initialize Bootstrap tooltip
  if (tooltipButton.value) {
    tooltip = new Tooltip(tooltipButton.value)
  }
})

onBeforeUnmount(() => {
  // Clean up tooltip instance to prevent memory leaks
  if (tooltip) {
    tooltip.dispose()
  }
})
</script>

<template>
  <button
    ref="tooltipButton"
    class="badge rounded-pill text-bg-dark mx-1"
    data-bs-toggle="tooltip"
    data-bs-placement="bottom"
    v-bind:title="props.title"
  >
    ?
  </button>
</template>
