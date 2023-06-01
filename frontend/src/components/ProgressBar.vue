<script setup lang="ts">
import { reactive, onMounted } from 'vue'

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

const state = reactive({
  loadingProgress: 0
})

const emit = defineEmits<{
  (e: 'change', isLoading: boolean): void
}>()

onMounted(() => {
  state.loadingProgress = props.max
})

function setValue(value: number): void {
  if (value < props.max) value = Math.max(props.min, value)
  else value = Math.min(props.max, value)
  state.loadingProgress = value
  emit('change', value < props.max)
}

defineExpose({
  setValue
})
</script>

<template>
  <div class="text-center" v-if="state.loadingProgress < props.max">
    <h4>Loading...</h4>

    <div
      class="progress"
      role="progressbar"
      aria-label="Basic example"
      aria-valuenow="0"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div class="progress-bar bg-primary" :style="{ width: state.loadingProgress + '%' }"></div>
    </div>
  </div>
</template>

<style scoped>
.progress-bar {
  -webkit-transition: width 0.5s ease;
  transition: width 0.5s ease;
}
</style>
