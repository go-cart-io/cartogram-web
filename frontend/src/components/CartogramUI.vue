<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

import { MapVersionData, MapDataFormat, MapVersion } from '@/lib/mapVersion'
import type { Region } from '@/lib/region'
import CartMap from '@/lib/cartMap'
import CartogramLegend from './CartogramLegend.vue'
import CartogramDownload from './CartogramDownload.vue'
import CartogramShare from './CartogramShare.vue'
import type { Mappack } from '@/lib/interface'

var map: CartMap
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
    scale?: number
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
  current_sysname: '2-population' as string,
  isLoading: true
})

onMounted(() => {
  if (!props.mappack) return
  console.log(props.mappack)
  if (!props.cartogram_data) {
    switchMap(props.mappack)
  } else {
    props.cartogram_data.tooltip = props.cartogramui_data.tooltip
    var mapVersionData = MapVersionData.mapVersionDataFromMappack(
      props.mappack,
      props.cartogram_data
    )
    switchMap(props.mappack, mapVersionData)
  }
})

function switchMap(mappack: Mappack, mapVersionData: MapVersionData | null = null) {
  state.isLoading = true
  map = new CartMap(props.handler, mappack.config, props.scale)
  map.addVersion(
    '1-conventional',
    MapVersionData.mapVersionDataFromMappack(mappack, mappack.original),
    '1-conventional'
  )
  map.addVersion(
    '2-population',
    MapVersionData.mapVersionDataFromMappack(null, mappack.population),
    '1-conventional'
  )
  if (mapVersionData !== null) {
    map.addVersion('3-cartogram', mapVersionData, '1-conventional')
  }

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

  map.drawVersion('1-conventional', 'map-area', ['map-area', 'cartogram-area'])

  if (mapVersionData !== null) {
    map.drawVersion('3-cartogram', 'cartogram-area', ['map-area', 'cartogram-area'])
    state.current_sysname = '3-cartogram'
  } else {
    map.drawVersion('2-population', 'cartogram-area', ['map-area', 'cartogram-area'])
    state.current_sysname = '2-population'
  }
  state.isLoading = false
}

function switchVersion(version: string) {
  map?.switchVersion(state.current_sysname, version, 'cartogram-area')
  state.current_sysname = version
}

function getRegions(): { [key: string]: Region } {
  return map?.regions || {}
}

function getVersions(): { [key: string]: MapVersion } {
  return map?.versions || {}
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
    <div class="card d-none d-sm-flex w-100">
      <div class="d-flex flex-column card-body">
        <div id="map-area" class="flex-fill" data-grid-visibility="off">
          <svg id="map-area-svg"></svg>
          <CartogramLegend
            v-if="!state.isLoading"
            ref="mapLegendEl"
            mapID="map-area"
            v-bind:isGridVisible="props.isGridVisible"
            v-bind:isLegendResizable="props.isLegendResizable"
            v-bind:map="map"
            sysname="1-conventional"
            legendID="map-area-legend"
            v-bind:mapWidth="map?.max_width"
            v-bind:mapHeight="map?.max_height"
          />
        </div>
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
                JSON.stringify(map?.getVersionGeoJSON('1-conventional'))
              )
            "
            data-bs-toggle="modal"
            data-bs-target="#downloadModal"
            title="Download map"
          >
            <i class="fas fa-download"></i>
          </button>
        </span>
      </div>
    </div>

    <div class="card w-100" id="cartogram-container">
      <div class="d-flex flex-column card-body">
        <div class="flex-fill">
          <div id="cartogram-area" class="w-100 h-100" data-grid-visibility="off">
            <svg id="cartogram-area-svg"></svg>
            <CartogramLegend
              v-if="!state.isLoading"
              ref="cartogramLegendEl"
              mapID="cartogram-area"
              v-bind:isGridVisible="props.isGridVisible"
              v-bind:isLegendResizable="props.isLegendResizable"
              v-bind:map="map"
              v-bind:sysname="state.current_sysname"
              legendID="cartogram-area-legend"
              v-bind:mapWidth="map?.max_width"
              v-bind:mapHeight="map?.max_height"
            />
            <div v-if="typeof map !== 'undefined'" class="z-3 position-absolute bottom-0 start-0">
              <button v-on:click="() => {map!.scaleVersion(1.1, 1)}">x+</button>
              <button v-on:click="() => {map!.scaleVersion(0.9, 1)}">x-</button>
              <button v-on:click="() => {map!.scaleVersion(1, 1.1)}">y+</button>
              <button v-on:click="() => {map!.scaleVersion(1, 0.9)}">y-</button>
              <button v-on:click="() => {map!.transformReset()}">reset</button>
            </div>
            <img
              class="position-absolute bottom-0 end-0 z-3"
              src="/static/img/by.svg"
              alt="cc-by"
            />
          </div>
        </div>
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
                JSON.stringify(map?.getVersionGeoJSON(state.current_sysname))
              )
            "
            data-bs-toggle="modal"
            data-bs-target="#downloadModal"
            title="Download cartogram"
          >
            <i class="fas fa-download"></i>
          </button>
          <CartogramShare
            v-if="mode !== 'embed'"
            v-bind:sysname="props.handler"
            v-bind:sharing_key="
              props.cartogramui_data ? props.cartogramui_data.unique_sharing_key : null
            "
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
