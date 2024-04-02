<script setup lang="ts">
import { computed } from 'vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = withDefaults(
  defineProps<{
    min?: number
    max?: number
  }>(),
  {
    min: 0,
    max: 100
  }
)

const emit = defineEmits<{
  (e: 'change', isLoading: boolean): void
}>()

const progress = computed(() => {
  let value = store.loadingProgress
  if (value < props.max) value = Math.max(props.min, value)
  else value = Math.min(props.max, value)
  store.loadingProgress = value  
  emit('change', value < props.max)
  return store.loadingProgress
})
</script>

<template>
  <div class="container-fluid p-3 text-center" v-if="progress < props.max">
    <h4>Loading...</h4>

    <div
      class="progress"
      role="progressbar"
      aria-label="Basic example"
      aria-valuenow="0"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div class="progress-bar bg-primary" :style="{ width: progress + '%' }"></div>
    </div>
  </div>
</template>

<style scoped>
.progress-bar {
  -webkit-transition: width 0.5s ease;
  transition: width 0.5s ease;
}
</style>
