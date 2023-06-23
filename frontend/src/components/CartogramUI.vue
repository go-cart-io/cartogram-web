<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import Cartogram from '../lib/cartogram'

import { MapVersionData, MapDataFormat, MapVersion } from '@/lib/mapVersion'
import type { Region } from '@/lib/region'
import type CartMap from '@/lib/cartMap'
import CartogramLegend from './CartogramLegend.vue'
import CartogramDownload from './CartogramDownload.vue'
import CartogramShare from './CartogramShare.vue'

const props = withDefaults(
  defineProps<{
    handler?: string
    cartogram_data?: any
    cartogramui_data?: any
    mappack: any
    mode?: string | null
    scale?: number | null
    isGridVisible?: boolean
    isLegendResizable?: boolean
  }>(),
  {
    handler: 'usa',
    mode: 'full',
    scale: 1.3
  }
)

const state = reactive({
  current_sysname: '2-population' as string
})

var cartogram = new Cartogram('/static/cartdata')

const mapLegendEl = ref()
const cartogramLegendEl = ref()
const cartogramDownloadEl = ref()

onMounted(() => {
  if (!props.cartogram_data) {
    switchMap(props.handler, '', props.mappack)
  } else {
    var extrema
    var format
    var world = false
    if (props.cartogram_data.hasOwnProperty('bbox')) {
      extrema = {
        min_x: props.cartogram_data.bbox[0],
        min_y: props.cartogram_data.bbox[1],
        max_x: props.cartogram_data.bbox[2],
        max_y: props.cartogram_data.bbox[3]
      }

      // We check if the generated cartogram is a world map by detecting the extent key
      if ('extent' in props.cartogram_data) {
        world = props.cartogram_data.extent === 'world'
      }
      format = MapDataFormat.GEOJSON
    } else {
      extrema = props.cartogram_data.extrema
      format = MapDataFormat.GOCARTJSON
    }

    var mapVersionData = new MapVersionData(
      props.cartogram_data.features,
      extrema,
      props.cartogramui_data.tooltip,
      null,
      null,
      format,
      world
    )
    switchMap(
      props.handler,
      '',
      props.mappack,
      mapVersionData,
      props.cartogramui_data.unique_sharing_key
    )
  }
})

function switchMap(
  sysname: string,
  hrname: string = '',
  mappack: any,
  mapVersionData: MapVersionData | null = null,
  sharing_key: string | null = null
) {
  cartogram.switchMap(sysname, hrname, mappack, mapVersionData, sharing_key)
  mapLegendEl.value.update(
    cartogram.model.map,
    '1-conventional',
    'map-area-legend',
    cartogram.model.map?.max_width,
    cartogram.model.map?.max_height
  )
  cartogramLegendEl.value.update(
    cartogram.model.map,
    cartogram.model.current_sysname,
    'cartogram-area-legend',
    cartogram.model.map?.max_width,
    cartogram.model.map?.max_height
  )
}

function switchVersion(version: string) {
  cartogram.model.map?.switchVersion(state.current_sysname, version, 'cartogram-area')
  state.current_sysname = version
}

function getRegions(): { [key: string]: Region } {
  return cartogram.model.map?.regions || {}
}

function getVersions(): { [key: string]: MapVersion } {
  return cartogram.model.map?.versions || {}
}

defineExpose({
  switchMap,
  switchVersion,
  getRegions,
  getVersions
})
</script>

<template>
  <div id="cartogram" class="d-flex flex-fill card-group">
    <div class="card d-none d-sm-flex">
      <div class="d-flex flex-column card-body">
        <svg id="map-area" class="flex-fill" data-grid-visibility="off">
          <defs>
            <pattern id="map-area-grid" patternUnits="userSpaceOnUse">
              <path fill="none" stroke="#5A5A5A" stroke-width="2" stroke-opacity="0.4"></path>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#map-area-grid)"></rect>
          <svg id="map-area-svg"></svg>
        </svg>
        <CartogramLegend
          ref="mapLegendEl"
          mapID="map-area"
          v-bind:isGridVisible="props.isGridVisible"
          v-bind:isLegendResizable="props.isLegendResizable"
        />
      </div>

      <div class="card-footer">
        Equal-Area Map
        <span class="float-end">
          <button
            v-if="mode !== 'embed'"
            class="btn btn-primary"
            id="map-download"
            v-on:click="
              cartogramDownloadEl.generateSVGDownloadLinks(
                'map-area',
                JSON.stringify(cartogram.model.map?.getVersionGeoJSON('1-conventional'))
              )
            "
            data-bs-toggle="modal"
            data-bs-target="#downloadModal"
          >
            <i class="fas fa-download"></i>
          </button>
        </span>
      </div>
    </div>

    <div class="card" id="cartogram-container">
      <div class="d-flex flex-column card-body">
        <div class="flex-fill">
          <div v-if="typeof cartogram.model.map !== 'undefined'" class="z-3 position-absolute">
            <button
              v-on:click="() => {cartogram.model.map!.stretch[0] += 0.1; cartogram.model.map!.transformVersion()}"
            >
              x+
            </button>
            <button
              v-on:click="() => {cartogram.model.map!.stretch[0] -= 0.1; cartogram.model.map!.transformVersion()}"
            >
              x-
            </button>
            <button
              v-on:click="() => {cartogram.model.map!.stretch[1] += 0.1; cartogram.model.map!.transformVersion()}"
            >
              y+
            </button>
            <button
              v-on:click="() => {cartogram.model.map!.stretch[1] -= 0.1; cartogram.model.map!.transformVersion()}"
            >
              y-
            </button>
            <button v-on:click="() => {cartogram.model.map!.transformReset()}">reset</button>
          </div>
          <svg id="cartogram-area" class="w-100 h-100" data-grid-visibility="off">
            <defs>
              <pattern id="cartogram-area-grid" patternUnits="userSpaceOnUse">
                <path fill="none" stroke="#5A5A5A" stroke-width="2" stroke-opacity="0.4"></path>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#cartogram-area-grid)"></rect>
            <svg id="cartogram-area-svg"></svg>
          </svg>
        </div>
        <CartogramLegend
          ref="cartogramLegendEl"
          mapID="cartogram-area"
          v-bind:isGridVisible="props.isGridVisible"
          v-bind:isLegendResizable="props.isLegendResizable"
        />
      </div>

      <div class="card-footer">
        Cartogram
        <span class="float-end">
          <button
            v-if="mode !== 'embed'"
            class="btn btn-primary me-2"
            id="cartogram-download"
            v-on:click="
              cartogramDownloadEl.generateSVGDownloadLinks(
                'cartogram-area',
                JSON.stringify(cartogram.model.map?.getVersionGeoJSON(state.current_sysname))
              )
            "
            data-bs-toggle="modal"
            data-bs-target="#downloadModal"
          >
            <i class="fas fa-download"></i>
          </button>
          <CartogramShare
            v-if="mode !== 'embed'"
            v-bind:sysname="props.handler"
            v-bind:key="props.cartogramui_data ? props.cartogramui_data.unique_sharing_key : null"
          />
        </span>
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
