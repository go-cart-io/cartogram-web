<script setup lang="ts">
import { reactive, ref } from 'vue'

const state = reactive({
  isShow: false,
  top: 0,
  left: 0,
  content: ''
})

const tooltipEl = ref()

function drawWithEntries(
  event: MouseEvent,
  name: string,
  abbreviation: string,
  entries: Array<{
    name: string
    value: number
    unit: string
  }>
): void {
  let content = '<b>' + name + ' (' + abbreviation + ')</b>'

  entries.forEach((entry) => {
    content += '<br/><i>' + entry.name + ':</i> ' + entry.value.toLocaleString() + ' ' + entry.unit
  })

  state.content = content
  state.left = event.pageX - 50
  state.top = event.pageY + 15
  state.isShow = true
}

function hide(): void {
  state.isShow = false
}

defineExpose({
  drawWithEntries,
  hide
})
</script>

<template>
  <div
    ref="tooltipEl"
    class="tooltip"
    :style="{ top: state.top + 'px', left: state.left + 'px' }"
    v-html="state.content"
  ></div>
</template>

<style scoped>
.tooltip {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid black;
  width: auto;
  height: auto;
  min-height: 75px;
  padding: 5px;
  position: absolute;
  font-size: small;
  top: 0;
  left: 0;
  z-index: 1000;
}
</style>
