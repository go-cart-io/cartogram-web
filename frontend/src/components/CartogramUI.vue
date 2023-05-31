<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import Cartogram from '../lib/cartogram.js'

import { MapVersionData, MapDataFormat, MapVersion } from '@/lib/mapVersion'
import type { Region } from '@/lib/region'
import type CartMap from '@/lib/cartMap'
import CartogramDownload from './CartogramDownload.vue'

const props = withDefaults(
  defineProps<{
    handler?: string
    cartogram_data?: any
    cartogramui_data?: any
    mappack: any
    mode?: string | null
    scale?: number | null
  }>(),
  {
    handler: 'usa',
    mode: 'full',
    scale: 1.3
  }
)

interface state {
  versions: { [key: string]: MapVersion }
  current_sysname: string
  current_map: CartMap | null
}

const state = reactive({
  versions: {},
  current_sysname: '1-conventional',
  current_map: null
})

var cartogram = new Cartogram(
  '/cartogram',
  '/cartogramui',
  '/static/cartdata',
  '/getprogress',
  'devel'
)

var cartogramDownloadEl = ref()

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
  state.versions = cartogram.model.map.versions
}

function switchVersion(event) {
  cartogram.model.map.switchVersion(state.current_sysname, event.target.value, 'cartogram-area')
  state.current_sysname = event.target.value
}

function getRegions(): { [key: string]: Region } {
  // = mappack.original.features
  return cartogram.model.map.regions
}

defineExpose({
  switchMap,
  getRegions
})
</script>

<template>
  <div>
    <p id="tooltip">&nbsp;</p>

    <div id="cartogram">
      <div class="row" id="cartogram-row">
        <div class="col-md-6">
          <div style="height: 40px">
            <h4 class="mb-0">Equal-Area Map</h4>
          </div>

          <!--CartogramMap ref="mapArea" /-->
          <div id="map-area" style="margin-top: 20px" data-grid-visibility="off"></div>
          <div style="padding-left: 0; padding-top: 10px" class="col-12">
            <!-- padding-top to add spacing between mapSVG and legend -->
            <svg
              width="375"
              height="90"
              id="map-area-legend"
              data-legend-type="static"
              data-current-grid-path="gridA"
            ></svg>
            <img
              class="cc-logo"
              src="/static/img/creativecommons_icon.svg"
              width="80"
              alt="Creative Commons Icon"
              style="position: absolute; top: 10px; margin-right: 0px"
            />
          </div>

          <div class="d-flex">
            <p style="margin-top: 20px; color: white; cursor: pointer" class="d-inline-block">
              <a class="btn btn-primary btn-customise" id="map-customise">Customise</a>
            </p>
            <p style="margin-top: 20px; margin-left: 10px">
              <a
                class="btn btn-primary"
                href=""
                id="map-download"
                data-toggle="modal"
                data-target="#download-modal"
                v-on:click="
                  cartogramDownloadEl.generateSVGDownloadLinks(
                    'map-area',
                    JSON.stringify(cartogram.model.map.getVersionGeoJSON('1-conventional'))
                  )
                "
                >Download</a
              >
            </p>
          </div>

          <div style="display: none" class="customise-popup" id="map-customise-popup">
            <form class="customise-container">
              <input
                type="checkbox"
                class="checkbox-customise"
                id="gridline-toggle-map"
                name="gridline"
                value="false"
                autocomplete="off"
              />
              <label class="checkbox-label" for="gridline-toggle-map">Show Grid Lines</label><br />
              <input
                type="checkbox"
                class="checkbox-customise"
                id="legend-toggle-map"
                name="legend"
                value="false"
                autocomplete="off"
              />
              <label class="checkbox-label" for="legend-toggle-map">Resizable Legend</label>
            </form>
          </div>
        </div>

        <div class="col-md-6" id="cartogram-container">
          <div style="height: 40px">
            <div class="d-flex align-items-center">
              <h4 class="d-inline-block mb-0">Cartogram</h4>
              <div id="map2-switch" class="ml-2">
                <div id="map2-switch-buttons">
                  <select
                    style="cursor: pointer"
                    class="form-control bg-primary text-light border-primary"
                    v-on:change="switchVersion"
                  >
                    <option v-for="(version, index) in state.versions" v-bind:value="index">
                      {{ version.name }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div id="cartogram-area" style="margin-top: 20px" data-grid-visibility="off"></div>
          <div style="padding-left: 0; padding-top: 10px" class="col-12">
            <svg
              width="375"
              height="90"
              id="cartogram-area-legend"
              data-legend-type="static"
              data-current-grid-path="gridA"
            ></svg>
            <img
              class="cc-logo"
              src="/static/img/creativecommons_icon.svg"
              width="80"
              alt="Creative Commons Icon"
              style="position: absolute; top: 10px; margin-right: 0px"
            />
          </div>

          <div class="d-flex">
            <p style="margin-top: 20px; color: white; cursor: pointer" class="d-inline-block">
              <a class="btn btn-primary btn-customise" id="cartogram-customise">Customise</a>
            </p>

            <p style="margin-top: 20px; margin-left: 10px" class="d-inline-block">
              <a
                class="btn btn-primary"
                href=""
                id="cartogram-download"
                data-toggle="modal"
                data-target="#download-modal"
                v-on:click="
                  cartogramDownloadEl.generateSVGDownloadLinks(
                    'cartogram-area',
                    JSON.stringify(cartogram.model.map.getVersionGeoJSON(state.current_sysname))
                  )
                "
                >Download</a
              >
            </p>
            <p style="margin-top: 20px; margin-left: 10px" class="d-inline-block">
              <a
                class="btn btn-info mr-2 text-light"
                href=""
                data-toggle="modal"
                data-target="#share-modal"
                >Share</a
              >
            </p>
          </div>

          <div style="display: none" class="customise-popup" id="cartogram-customise-popup">
            <form class="customise-container">
              <input
                type="checkbox"
                class="checkbox-customise"
                id="gridline-toggle-cartogram"
                name="gridline"
                value="false"
                autocomplete="off"
              />
              <label class="checkbox-label" for="gridline-toggle-cartogram">Show Grid Lines</label
              ><br />
              <input
                type="checkbox"
                class="checkbox-customise"
                id="legend-toggle-cartogram"
                name="legend"
                value="false"
                autocomplete="off"
              />
              <label class="checkbox-label" for="legend-toggle-cartogram">Resizable Legend</label>
            </form>
          </div>
        </div>
      </div>
      <span id="map1-switch"></span>
    </div>

    <CartogramDownload ref="cartogramDownloadEl" />
  </div>
</template>

<style scoped>
@media screen and (max-width: 1000px) {
  #cartogram-row {
    display: block;
  }

  #cartogram-row .col-md-6 {
    max-width: 100% !important;
  }
}

.customise-popup {
  color: white;
  border: 5px solid #d76127;
  background-color: #d76127;
  padding: 3px;
  position: absolute;
  margin-bottom: 10px;
  margin-top: -10px;
  border-radius: 1.2rem;
  width: 180px;
  z-index: 1000;
}

.checkbox-customise {
  cursor: pointer;
}

/* We use the following attributes so that clicking the checkbox text doesn't select them */
.checkbox-label {
  cursor: pointer;
  -moz-user-select: none;
  -webkit-user-select: none;
  -ms-user-select: none;
  user-select: none;
  -o-user-select: none;
}

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
