<script setup lang="ts">
import { reactive, ref, onMounted, watch } from 'vue'
import TouchInfo from '../lib/touchInfo'

const svgEl = ref()
let posX = 0,
  posY = 0

const props = defineProps<{
  touchInfo: TouchInfo
  touchLenght: number
}>()

const state = reactive({
  points: [] as number[][],
  line: [] as number[][]
})

onMounted(() => {
  const pos = svgEl.value.getBoundingClientRect()
  posX = pos.left
  posY = pos.top
  updatePoints()
})

watch(
  () => props.touchLenght,
  () => {
    updatePoints()
  }
)

function updatePoints() {
  state.points = []
  state.line = []

  try {
    // Uncomment this code to visualize each pointer
    // state.points = props.touchInfo.getAllPoints(posX, posY)
    if (props.touchInfo.length() > 2) {
      state.line = props.touchInfo.getMergedPoints(posX, posY)
    }
  } catch (err) {
    console.log(err)
  }
}
</script>

<template>
  <svg ref="svgEl" class="w-100 h-100 position-absolute z-3" style="pointer-events: none">
    <g v-for="(point, index) in state.points" v-bind:key="index">
      <circle v-bind:cx="point[0]" v-bind:cy="point[1]" fill="blue" r="5" />
    </g>
    <g v-if="state.line.length > 0">
      <line
        v-bind:x1="state.line[0][0]"
        v-bind:y1="state.line[0][1]"
        v-bind:x2="state.line[1][0]"
        v-bind:y2="state.line[1][1]"
        style="stroke: rgb(255, 0, 0); stroke-width: 2"
      />
    </g>
  </svg>
</template>
