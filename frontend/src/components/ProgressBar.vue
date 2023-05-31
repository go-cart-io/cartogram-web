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
  <div v-if="state.loadingProgress < props.max">
    <p style="font-weight: bold">Loading...</p>

    <div class="row" id="loading-progress-container">
      <div class="col-sm-12 col-md-6">
        <div class="progress">
          <div class="progress-bar" :style="{ width: state.loadingProgress + '%' }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.progress-bar {
  -webkit-transition: width 0.5s ease;
  transition: width 0.5s ease;
}
</style>
