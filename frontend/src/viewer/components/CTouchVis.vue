<script setup lang="ts">
import { reactive, ref, onMounted, watch } from 'vue'
import TouchInfo from '../lib/touchInfo'

const svgEl = ref()
var posX = 0,
  posY = 0

const props = defineProps<{
  touchInfo: TouchInfo
  touchLenght: number
}>()

const state = reactive({
  points: [] as number[][],
  midPoint: [] as number[]
})

onMounted(() => {
  let pos = svgEl.value.getBoundingClientRect()
  posX = pos.left
  posY = pos.top
  updatePoints()
})

watch(
  () => props.touchLenght,
  (touchLenght, prevTouchLenght) => {
    updatePoints()
  }
)

function updatePoints() {
  state.points = []
  state.midPoint = []

  try {
    if (props.touchInfo.length > 1) {
      state.points = [props.touchInfo.getThumb(posX, posY)]
      for (const identifier in props.touchInfo.touches) {
        if (identifier === props.touchInfo.thumbIndex.toString()) continue
        state.points.push([
          props.touchInfo.touches[identifier].pageX - posX,
          props.touchInfo.touches[identifier].pageY - posY
        ])
      }
      state.midPoint = props.touchInfo.getOthers()
    }
  } catch (err) {
    console.log(err)
  }
}
</script>

<template>
  <svg ref="svgEl" class="w-100 h-100 position-absolute">
    <g v-for="(point, index) in state.points">
      <circle
        v-bind:cx="point[0]"
        v-bind:cy="point[1]"
        v-bind:fill="index === 0 ? 'red' : 'blue'"
        r="5"
      />
    </g>
    <g v-if="state.points.length > 2 && state.midPoint.length > 0">
      <line
        v-bind:x1="state.points[0][0]"
        v-bind:y1="state.points[0][1]"
        v-bind:x2="state.midPoint[0]"
        v-bind:y2="state.midPoint[1]"
        style="stroke: rgb(255, 0, 0); stroke-width: 2"
      />
    </g>
  </svg>
</template>
