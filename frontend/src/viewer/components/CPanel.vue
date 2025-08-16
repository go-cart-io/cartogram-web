<script setup lang="ts">
/**
 * The map panel with functions for interactivity to manipulate viewport and managing grid size.
 */
import { onMounted, nextTick, reactive, watch, ref } from 'vue'

import CPanelLegend from './CPanelLegend.vue'
import CPanelSelectVersion from './CPanelSelectVersion.vue'
import CPanelBtnDownload from './CPanelBtnDownload.vue'
import CTouchVis from './CTouchVis.vue'
import * as visualization from '../../common/visualization'
import * as animate from '../lib/animate'
import * as util from '../lib/util'
import { useTransform } from '../composables/useTransform'
import { useLegend } from '../composables/useLegend'

const SUPPORT_TOUCH = 'ontouchstart' in window || navigator.maxTouchPoints

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

const legendLineEl = ref()
let visView: any

const props = defineProps<{
  panelID: string
  defaultVersionKey: string
}>()

const transform = useTransform(props.panelID)
const legend = useLegend()

const state = reactive({
  versionKey: props.defaultVersionKey,
  currentGridIndex: 1,
  cursor: 'grab',
  isLockRatio: true,
  stretchDirection: 'x'
})

watch(
  () => store.highlightedRegionID,
  (id) => {
    visView?.signal('active', id).runAsync()
  }
)

watch(
  () => store.options.numberOfPanels,
  async () => {
    await visView.resize()
    await visView.width(visView.container().offsetWidth).runAsync()
    switchGrid(state.currentGridIndex)
  }
)

watch(
  () => store.currentColorCol,
  () => {
    init()
  }
)

onMounted(async () => {
  await init()
  switchGrid(state.currentGridIndex)
})

async function initContainer(canvasId: string) {
  const csvUrl = util.getCsvURL(store.currentMapName, CARTOGRAM_CONFIG.mapDBKey)
  const jsonUrl = util.getGeojsonURL(
    store.currentMapName,
    CARTOGRAM_CONFIG.mapDBKey,
    CARTOGRAM_CONFIG.cartoVersions[state.versionKey].name + '.json'
  )
  const container = await visualization.initWithURL(
    canvasId,
    csvUrl,
    jsonUrl,
    store.currentColorCol,
    CARTOGRAM_CONFIG.cartoColorScheme,
    CARTOGRAM_CONFIG.choroSpec
  )

  legend.init(
    CARTOGRAM_CONFIG.cartoVersions[state.versionKey].header,
    container.view.data('geo_1'),
    container.view.data('source_csv')
  )

  return container
}

async function init() {
  const container = await initContainer(props.panelID + '-vis')
  visView = container.view

  visView.addResizeListener(function () {
    legend.updateTotalArea(visView.data('geo_1'))
    switchGrid(state.currentGridIndex)
  })

  visView.addSignalListener('active', function (name: string, value: any) {
    store.highlightedRegionID = value
  })

  visView.addEventListener('pointerup', function (event: any, item: any) {
    const value = item?.datum.cartogram_data
    visView.tooltip()(visView, event, item, value)
  })
}

async function switchVersion(versionKey: string) {
  state.versionKey = versionKey
  const container = await initContainer(props.panelID + '-offscreen')
  switchGrid(state.currentGridIndex)

  function finalize() {
    container.view.runAfter(() => transform.applyCurrent())
    container.view.initialize('#' + props.panelID + '-vis').runAsync()
    visView = container.view
  }

  animate.geoTransition(props.panelID, finalize)
}

async function switchGrid(key: number) {
  state.currentGridIndex = key
  legend.updateGridData()
  await nextTick()
  transform.setGridScaleNiceNumber(
    legend.stateGridData.value[state.currentGridIndex]?.scaleNiceNumber
  )
  legend.updateLegendValue(state.currentGridIndex, transform.stateAffineScale.value)
  legendLineEl.value.setHandlePosition(legend.stateGridData.value[key]?.width)
  animate.gridTransition(props.panelID + '-grid', legend.stateGridData.value[key]?.width)
}

function switchMode() {
  if (SUPPORT_TOUCH) {
    state.isLockRatio = !state.isLockRatio
  } else if (state.isLockRatio) {
    state.stretchDirection = 'x'
    state.isLockRatio = false
  } else if (state.stretchDirection === 'x') {
    state.stretchDirection = 'y'
  } else {
    state.isLockRatio = true
  }
}
</script>

<template>
  <div class="card w-100">
    <div class="d-flex flex-column card-body">
      <div class="d-flex flex-column card-body p-0">
        <div class="d-flex position-absolute z-1">
          <c-panel-legend
            ref="legendLineEl"
            v-bind:panelID="props.panelID"
            v-bind:gridIndex="state.currentGridIndex"
            v-bind:gridData="legend.stateGridData.value"
            v-on:change="switchGrid"
          />
          <div v-bind:id="props.panelID + '-legend-num'" class="flex-fill p-1">
            <span v-html="legend.stateValue.value"></span>
            {{ CARTOGRAM_CONFIG.cartoVersions[state.versionKey]?.unit }}
            <div>Total: <span v-html="legend.stateTotalValue.value"></span></div>
          </div>
        </div>

        <div
          class="d-flex flex-fill position-relative"
          style="touch-action: none"
          v-bind:id="props.panelID"
          v-bind:style="{ cursor: state.cursor }"
          v-on:pointerdown.stop.prevent="
            ($event) => {
              transform.onPointerdown($event)
              legend.updateLegendValue(state.currentGridIndex, transform.stateAffineScale.value)
            }
          "
          v-on:pointermove.stop.prevent="
            ($event) => {
              transform.onPointermove($event, state.isLockRatio)
              legend.updateLegendValue(state.currentGridIndex, transform.stateAffineScale.value)
            }
          "
          v-on:pointerup.stop.prevent="
            ($event) => {
              transform.onPointerup($event)
              legend.updateLegendValue(state.currentGridIndex, transform.stateAffineScale.value)
            }
          "
          v-on:pointercancel.stop.prevent="
            ($event) => {
              transform.onPointerup($event)
              legend.updateLegendValue(state.currentGridIndex, transform.stateAffineScale.value)
            }
          "
          v-on:wheel.stop.prevent="
            ($event) => {
              transform.onWheel($event, state.isLockRatio, state.stretchDirection)
              legend.updateLegendValue(state.currentGridIndex, transform.stateAffineScale.value)
            }
          "
        >
          <div style="mix-blend-mode: multiply">
            <div v-bind:id="props.panelID + '-offscreen'" class="vis-area offscreen"></div>
            <div v-bind:id="props.panelID + '-vis'" class="vis-area"></div>
            <img
              class="position-absolute bottom-0 end-0 z-3"
              src="/static/img/by.svg"
              alt="cc-by"
            />
          </div>
          <svg width="100%" height="100%" v-bind:id="props.panelID + '-grid-area'">
            <defs>
              <pattern v-bind:id="props.panelID + '-grid'" patternUnits="userSpaceOnUse">
                <path
                  fill="none"
                  stroke="#5A5A5A"
                  stroke-width="2"
                  v-bind:stroke-opacity="store.options.gridOpacity"
                ></path>
              </pattern>
            </defs>
            <rect
              width="100%"
              height="100%"
              v-bind:fill="'url(#' + props.panelID + '-grid)'"
            ></rect>
          </svg>
        </div>
      </div>
      <div class="position-absolute end-0" style="width: 2.5rem">
        <button
          class="btn btn-secondary w-100 my-1"
          v-on:click="switchMode()"
          v-bind:title="state.isLockRatio ? 'Switch to free transform' : 'Switch to lock ratio'"
        >
          <i v-if="transform.stateTouchLenght.value === 3" class="fas fa-unlock"></i>
          <i v-else-if="state.isLockRatio" class="fas fa-lock"></i>
          <i v-else-if="SUPPORT_TOUCH" class="fas fa-unlock"></i>
          <i v-else-if="state.stretchDirection === 'x'" class="fas fa-arrows-alt-h"></i>
          <i v-else class="fas fa-arrows-alt-v"></i>
        </button>
        <button class="btn btn-secondary w-100 my-1" v-on:click="transform.reset()" title="Reset">
          <i class="fas fa-crosshairs"></i>
        </button>
      </div>
    </div>

    <div class="card-footer d-flex justify-content-between">
      <c-panel-select-version
        v-bind:panelID="props.panelID"
        v-bind:currentVersionName="state.versionKey"
        v-on:version_changed="(versionKey) => switchVersion(versionKey)"
      />
      <c-panel-btn-download v-bind:versionKey="state.versionKey" v-bind:panelID="props.panelID" />
    </div>
  </div>

  <c-touch-vis
    v-bind:key="transform.stateLastMove.value"
    v-bind:touchInfo="transform.touchInfo"
    v-bind:touchLenght="transform.stateTouchLenght.value"
  />
</template>

<style scoped>
.vis-area {
  position: absolute !important;
  width: 100%;
  height: 100%;
  min-height: 100px;
}

.vis-area.offscreen {
  opacity: 0;
}
</style>

<style>
path {
  mix-blend-mode: multiply;
}
path[aria-label='dividers'] {
  mix-blend-mode: normal;
}
g.root {
  transform-origin: center;
}
</style>
