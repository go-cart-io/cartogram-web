<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import shareState from '../lib/state'
import TouchInfo from '../lib/touchInfo'

const props = defineProps<{
  handler: string
  touchInfo: TouchInfo
  touchLenght: number
}>()

const state = reactive({
  points: [] as number[][],
  midPoint: [] as number[]
})

onMounted(() => {
  try {
    if (props.touchInfo.length > 1) {
      state.points = [props.touchInfo.getThumb()]
      for (const identifier in props.touchInfo.touches) {
        if (identifier === props.touchInfo.thumbIndex.toString()) continue
        state.points.push([
          props.touchInfo.touches[identifier].pageX,
          props.touchInfo.touches[identifier].pageY
        ])
      }
      state.midPoint = props.touchInfo.getOthers()
    }
  } catch (err) {
    console.log(err)
  }
})
</script>

<template>
  <svg class="w-100 h-100" v-if="props.touchLenght > 0 && state.points.length > 0">
    <g v-for="(point, index) in state.points">
      <circle
        v-bind:cx="point[0]"
        v-bind:cy="point[1]"
        v-bind:fill="index === 0 ? 'red' : 'blue'"
        r="5"
      />
    </g>
    <g v-if="props.touchLenght > 2 && shareState.options.stretchable">
      <text
        font-weight="bold"
        v-bind:x="state.points[0][0] - 50"
        v-bind:y="state.points[0][1] + 50"
        style="fill: white; stroke: red; stroke-width: 2"
      >
        Thumb
      </text>
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
