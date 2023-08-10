<script setup lang="ts">
import * as d3 from 'd3'
import { ref, reactive, onMounted, nextTick } from 'vue'

import { MapVersionData, MapDataFormat, MapVersion } from '@/lib/mapVersion'
import type { Region } from '@/lib/region'
import CartMap from '@/lib/cartMap'
import CartogramLegend from './CartogramLegend.vue'
import CartogramDownload from './CartogramDownload.vue'
import CartogramShare from './CartogramShare.vue'
import type { Mappack } from '../lib/interface'
import * as util from '../lib/util'
import shareState from '../lib/state'

var map: CartMap
var pointerangle: number | boolean, // (A)
  pointerposition: number[] | null, // (B)
  pointerdistance: number | boolean // (C)
var supportsTouch = 'ontouchstart' in window || navigator.maxTouchPoints

const mapLegendEl = ref()
const cartogramLegendEl = ref()
const cartogramDownloadEl = ref()

const props = withDefaults(
  defineProps<{
    handler?: string
    cartogram_data?: any
    cartogramui_data?: any
    mappack: Mappack | null
    mode?: string | null
  }>(),
  {
    handler: 'usa',
    mode: 'full'
  }
)

const state = reactive({
  isLoading: true,
  cursor: 'grab',
  isLockRatio: true,
  affineMatrix: util.getOriginalMatrix(),
  affineScale: [1, 1] // Keep track of scale for scaling grind easily
})

onMounted(() => {
  if (!props.mappack) return

  if (!props.cartogram_data) {
    switchMap(props.mappack)
  } else {
    props.cartogram_data.tooltip = props.cartogramui_data.tooltip
    var mapVersionData = MapVersionData.mapVersionDataFromMappack(null, props.cartogram_data)
    switchMap(props.mappack, mapVersionData)
  }
})

async function switchMap(mappack: Mappack, mapVersionData: MapVersionData | null = null) {
  state.isLoading = true
  map = new CartMap(props.handler, mappack.config)
  let data_names = mappack.config.data_names || ['original', 'population']
  let current_sysname = '0-base'
  map.addVersion(
    '0-base',
    MapVersionData.mapVersionDataFromMappack(mappack, mappack[data_names[0]]),
    '0-base'
  )
  for (let i = 1; i < data_names.length; i++) {
    current_sysname = i.toString() + '-' + data_names[i]
    map.addVersion(
      current_sysname,
      MapVersionData.mapVersionDataFromMappack(null, mappack[data_names[i]]),
      '0-base'
    )
  }

  if (mapVersionData !== null) {
    map.addVersion('99-cartogram', mapVersionData, '0-base')
    current_sysname = '99-cartogram'
  }
  shareState.current_sysname = current_sysname

  /*
    The keys in the colors.json file are prefixed with id_. We iterate through the regions and extract the color
    information from colors.json to produce a color map where the IDs are plain region IDs, as required by
    CartMap.
    */
  var colors: { [key: string]: string } = {}
  Object.keys(map.regions).forEach(function (region_id) {
    colors[region_id] = mappack.colors['id_' + region_id]
  })
  map.colors = colors
  state.isLoading = false

  await nextTick()
  map.drawVersion('0-base', 'map-area', ['map-area', 'cartogram-area'])
  map.drawVersion(shareState.current_sysname, 'cartogram-area', ['map-area', 'cartogram-area'])
}

function switchVersion(version: string) {
  if (!version) return
  map?.switchVersion(shareState.current_sysname, version, 'cartogram-area')
  shareState.current_sysname = version
}

function getRegions(): { [key: string]: Region } {
  return map?.regions || {}
}

function getVersions(): { [key: string]: MapVersion } {
  return map?.versions || {}
}

// https://observablehq.com/@d3/multitouch
function onTouchstart(event: any, id: string) {
  const t = d3.pointers(event, d3.select(id))
  pointerangle = t.length > 1 && Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (A)
  pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0] // (B)
  pointerdistance = t.length > 1 && Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (C)
  state.cursor = 'grabbing' // (F)
  if (event.cancelable) event.preventDefault()
}

function onTouchend(event: any) {
  pointerposition = null // signals mouse up for (D) and (E)
  state.cursor = 'grab'
  if (event.cancelable) event.preventDefault()
}

function onTouchmove(event: any, id: string) {
  if (!pointerposition) return // mousemove with the mouse up

  //const t = [event.clientX, event.clientY]
  const t = d3.pointers(event, d3.select(id))
  var matrix = util.getOriginalMatrix()
  var angle = 0
  var position = [0, 0]
  var scale = [1, 1]

  // Order should be rotate, scale, translate
  // https://gamedev.stackexchange.com/questions/16719/what-is-the-correct-order-to-multiply-scale-rotation-and-translation-matrices-f
  if (t.length > 1) {
    if (state.isLockRatio) {
      // (B) rotate
      if (pointerangle && typeof pointerangle === 'number') {
        var pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
        angle = pointerangle2 - pointerangle
        pointerangle = pointerangle2
        matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(angle))
      }
      // (C) scale
      if (pointerdistance && typeof pointerdistance === 'number') {
        var pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
        scale[0] = pointerdistance2 / pointerdistance
        scale[1] = pointerdistance2 / pointerdistance
        state.affineScale[0] *= scale[0]
        state.affineScale[1] *= scale[1]
        pointerdistance = pointerdistance2

        if (scale[0] !== 0 && scale[1] !== 0)
          matrix = util.multiplyMatrix(matrix, util.getScaleMatrix(scale[0], scale[1]))
      }
    } else if (pointerangle && typeof pointerangle === 'number') {
      // (B) rotate
      var pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
      angle = pointerangle2 - pointerangle
      pointerangle = pointerangle2
      matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(angle))

      // (C) scale
      if (pointerdistance && typeof pointerdistance === 'number') {
        var pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
        scale[0] = pointerdistance2 / pointerdistance
        state.affineScale[0] *= scale[0]
        pointerdistance = pointerdistance2

        if (scale[0] !== 0) {
          matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(pointerangle))
          matrix = util.multiplyMatrix(matrix, util.getScaleMatrix(scale[0], 1))
          matrix = util.multiplyMatrix(matrix, util.getRotateMatrix(-pointerangle))
        }
      }
    }
  }

  // (A) translate
  var pointerposition2 = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0]
  position[0] = pointerposition2[0] - pointerposition[0]
  position[1] = pointerposition2[1] - pointerposition[1]
  pointerposition = pointerposition2
  matrix = util.multiplyMatrix(matrix, util.getTranslateMatrix(position[0], position[1]))

  transformVersion(matrix, state.affineMatrix)
  if (event.cancelable) event.preventDefault()
}

function onWheel(event: any) {
  // (D) and (E), pointerposition also tracks mouse down/up
  var matrix: Array<Array<number>> = []
  if (pointerposition) {
    matrix = util.getRotateMatrix(event.wheelDelta / 1000)
  } else {
    var scale = 1 + event.wheelDelta / 1000
    var scales

    if (event.altKey) {
      scales = [scale, 1]
    } else if (event.shiftKey) {
      scales = [1, scale]
    } else {
      scales = [scale, scale]
    }

    state.affineScale[0] *= scales[0]
    state.affineScale[1] *= scales[1]
    matrix = util.getScaleMatrix(scales[0], scales[1])
  }
  transformVersion(matrix, state.affineMatrix)
  if (event.cancelable) event.preventDefault()
}

function transformVersion(matrix1: Array<Array<number>>, matrix2: Array<Array<number>>) {
  state.affineMatrix = util.multiplyMatrix(matrix1, matrix2)

  d3.selectAll('#cartogram-area-svg g').attr(
    'transform',
    'matrix(' +
      state.affineMatrix[0][0] +
      ' ' +
      state.affineMatrix[1][0] +
      ' ' +
      state.affineMatrix[0][1] +
      ' ' +
      state.affineMatrix[1][1] +
      ' ' +
      state.affineMatrix[0][2] +
      ' ' +
      state.affineMatrix[1][2] +
      ')'
  )
}

function transformReset() {
  state.affineMatrix = util.getOriginalMatrix()
  state.affineScale = [1, 1]
  transformVersion(state.affineMatrix, state.affineMatrix)
}

function snapToBetterNumber() {
  let value = cartogramLegendEl.value.getCurrentScale()
  let [scaleNiceNumber, scalePowerOf10] = util.findNearestNiceNumber(value)
  let targetValue = scaleNiceNumber * Math.pow(10, scalePowerOf10)
  let adjustedScale = Math.sqrt(value / targetValue)

  state.affineScale[0] *= adjustedScale
  state.affineScale[1] *= adjustedScale
  var matrix = util.getScaleMatrix(adjustedScale, adjustedScale)
  transformVersion(matrix, state.affineMatrix)
}

defineExpose({
  switchMap,
  switchVersion,
  getRegions,
  getVersions,
  mapLegendEl,
  cartogramLegendEl
})
</script>

<template>
  <div id="cartogram" class="d-flex flex-fill card-group">
    <div class="card d-none d-sm-flex w-100">
      <div class="d-flex flex-column card-body">
        <CartogramLegend
          v-if="!state.isLoading"
          ref="mapLegendEl"
          mapID="map-area"
          v-bind:map="map"
          sysname="0-base"
        >
          <svg id="map-area-svg"></svg>
        </CartogramLegend>
      </div>

      <div class="card-footer d-flex justify-content-between">
        <div class="text-nowrap overflow-hidden">Equal-Area Map</div>
        <div class="text-nowrap">
          <button
            v-if="mode !== 'embed'"
            class="btn btn-primary mx-1"
            id="map-download"
            v-on:click="
              cartogramDownloadEl.generateSVGDownloadLinks(
                'map-area',
                JSON.stringify(map?.getVersionGeoJSON('0-base'))
              )
            "
            data-bs-toggle="modal"
            data-bs-target="#downloadModal"
            title="Download map"
          >
            <i class="fas fa-download"></i>
          </button>
        </div>
      </div>
    </div>

    <div class="card w-100">
      <div class="d-flex flex-column card-body">
        <CartogramLegend
          v-if="!state.isLoading"
          ref="cartogramLegendEl"
          mapID="cartogram-area"
          v-bind:map="map"
          v-bind:sysname="shareState.current_sysname"
          v-bind:affineScale="state.affineScale"
        >
          <svg
            id="cartogram-area-svg"
            v-bind:style="{ cursor: state.cursor }"
            v-on:mousedown="onTouchstart($event, 'cartogram-area-svg')"
            v-on:touchstart="onTouchstart($event, 'cartogram-area-svg')"
            v-on:mousemove="onTouchmove($event, 'cartogram-area-svg')"
            v-on:touchmove="onTouchmove($event, 'cartogram-area-svg')"
            v-on:mouseup="onTouchend"
            v-on:touchend="onTouchend"
            v-on:wheel="onWheel"
          ></svg>
          <img class="position-absolute bottom-0 end-0 z-3" src="/static/img/by.svg" alt="cc-by" />
        </CartogramLegend>
      </div>

      <div class="card-footer d-flex justify-content-between">
        <div class="d-none d-sm-block text-nowrap overflow-hidden">Cartogram</div>
        <div class="text-nowrap">
          <button
            v-if="supportsTouch"
            class="btn btn-primary mx-1"
            v-on:click="state.isLockRatio = !state.isLockRatio"
            v-bind:title="state.isLockRatio ? 'Switch to free transform' : 'Switch to lock ratio'"
          >
            <i v-if="state.isLockRatio" class="fas fa-lock"></i>
            <i v-else class="fas fa-unlock"></i>
          </button>
          <button
            class="btn btn-primary mx-1"
            v-on:click="snapToBetterNumber()"
            title="Snap grid to nice number"
          >
            <i class="fas fa-expand"></i>
          </button>
          <button class="btn btn-primary mx-1" v-on:click="transformReset()" title="Reset">
            <i class="fas fa-undo"></i>
          </button>

          <span v-if="mode !== 'embed'">
            <div class="vr"></div>
            <button
              class="btn btn-primary mx-1"
              id="cartogram-download"
              v-on:click="
                cartogramDownloadEl.generateSVGDownloadLinks(
                  'cartogram-area',
                  JSON.stringify(map?.getVersionGeoJSON(shareState.current_sysname))
                )
              "
              data-bs-toggle="modal"
              data-bs-target="#downloadModal"
              title="Download cartogram"
            >
              <i class="fas fa-download"></i>
            </button>
            <CartogramShare
              v-bind:sysname="props.handler"
              v-bind:sharing_key="
                props.cartogramui_data ? props.cartogramui_data.unique_sharing_key : null
              "
            />
          </span>
        </div>
      </div>
    </div>

    <p id="tooltip" style="display: none">&nbsp;</p>
    <CartogramDownload ref="cartogramDownloadEl" />
  </div>
</template>

<style>
#map-area,
#cartogram-area {
  position: relative;
}

#map-area-svg,
#cartogram-area-svg {
  position: absolute;
  width: 100%;
  height: 100%;
  min-height: 100px;
  mix-blend-mode: multiply;
}

#map-area-svg g,
#cartogram-area-svg g {
  transform-box: fill-box;
  transform-origin: center;
}
</style>

<style scoped>
/* TODO: move to Tooltip component */
#tooltip {
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
